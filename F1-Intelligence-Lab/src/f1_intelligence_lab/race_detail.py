"""Persistent, source-linked race dossiers. Never infer classification from laps."""
import json
import re
import threading
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from .library_api import library
from .openf1_provider import Client, BASE
from .security import require_admin

router = APIRouter()
LOCK = threading.Lock()
LOADS = {}
EVENTS = dict(zip(
    ['Melbourne','Shanghai','Suzuka','Sakhir','Jeddah','Miami','Imola','Monte Carlo','Catalunya','Montreal','Spielberg','Silverstone','Spa-Francorchamps','Hungaroring','Zandvoort','Monza','Baku','Singapore','Austin','Mexico City','Interlagos','Las Vegas','Lusail','Yas Marina Circuit','Madring'],
    ['Australian','Chinese','Japanese','Bahrain','Saudi Arabian','Miami','Emilia Romagna','Monaco','Spanish','Canadian','Austrian','British','Belgian','Hungarian','Dutch','Italian','Azerbaijan','Singapore','United States','Mexico City','São Paulo','Las Vegas','Qatar','Abu Dhabi','Spanish']))

class Documents(HTMLParser):
    def __init__(self, prefix):
        super().__init__(); self.prefix = self.normalize(prefix); self.rows = {}; self.active = None; self.text = []
    @staticmethod
    def normalize(value):
        return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c))
    def handle_starttag(self, tag, attrs):
        if tag != 'a': return
        url = urljoin('https://www.fia.com', dict(attrs).get('href', ''))
        path = self.normalize(unquote(urlparse(url).path).lower().replace('_', ' '))
        if urlparse(url).hostname in {'www.fia.com','api.fia.com'} and '/decision-document/' in path and path.endswith('.pdf') and path.rsplit('/',1)[-1].startswith(self.prefix):
            self.active = url; self.text = []
    def handle_data(self, data):
        if self.active: self.text.append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self.active:
            title = ' '.join(' '.join(self.text).split())
            self.rows[self.active] = {'url':self.active,'title':title or unquote(self.active.rsplit('/',1)[-1]).replace('_',' ')}
            self.active = None

def fia_documents(meta):
    event = EVENTS.get(meta['event'])
    if not event: raise ValueError('No verified FIA event-name mapping for this circuit.')
    if meta['event'] == 'Catalunya' and meta['year'] >= 2026: event = 'Barcelona-Catalunya'
    season = {2023:2042,2024:2043,2025:2071,2026:2072}.get(meta['year'])
    if not season: raise ValueError('No verified FIA season mapping.')
    name = event + ' Grand Prix'
    url = f'https://www.fia.com/documents/event/{quote(name)}/championships/fia-formula-one-world-championship-14/season/season-{meta["year"]}-{season}'
    with urlopen(Request(url, headers={'User-Agent':'RaceLab-local-research/1.0'}), timeout=30) as response:
        raw = response.read(8_000_001)
    if len(raw)>8_000_000: raise ValueError('FIA response exceeds safety limit.')
    parser = Documents(f'{meta["year"]} {name.lower()}')
    parser.feed(raw.decode('utf-8'))
    rows = list(parser.rows.values())
    for row in rows:
        row['kind'] = 'Summons (not a verdict)' if 'summons' in row['title'].lower() else 'Decision / infringement' if re.search('decision|infringement',row['title'],re.I) else 'Event document'
    return rows, url

def ensure(db):
    db.execute('CREATE TABLE IF NOT EXISTS race_details (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')

def saved(lib, sid):
    lib.session(sid)
    with lib.connect() as db:
        ensure(db)
        row = db.execute('SELECT payload FROM race_details WHERE id=?',(sid,)).fetchone()
    return json.loads(row[0]) if row else {'session_id':sid,'state':'not_loaded','sections':{}}

def build(lib, sid):
    meta = lib.session(sid)
    if not re.fullmatch(r'openf1-\d+',sid): raise ValueError('Detail import currently supports OpenF1 sessions.')
    key = int(sid.split('-')[1]); client = Client(lib.root)
    out = {'session_id':sid,'state':'ready','retrieved_at':datetime.now(timezone.utc).isoformat(),'sections':{}}
    for section, endpoint in [('drivers','drivers'),('results','session_result'),('stints','stints'),('pit_stops','pit'),('race_control','race_control')]:
        try:
            rows = client.get(endpoint,session_key=key)
            out['sections'][section] = {'status':'available' if rows else 'empty','rows':rows,'source_url':BASE+endpoint+f'?session_key={key}'}
        except Exception as exc:
            out['sections'][section] = {'status':'unavailable','rows':[],'message':str(exc)}
    try:
        rows, url = fia_documents(meta)
        out['sections']['fia'] = {'status':'available' if rows else 'empty','rows':rows,'source_url':url,'message':'Official event documents; open PDFs for full reasoning. Summons are not decisions. This index may not be exhaustive.'}
    except Exception as exc:
        out['sections']['fia'] = {'status':'unavailable','rows':[],'message':str(exc),'source_url':'https://www.fia.com/documents'}
    with lib.connect() as db:
        ensure(db)
        db.execute('INSERT OR REPLACE INTO race_details VALUES (?,?)',(sid,json.dumps(out,allow_nan=False)))
    return out

@router.get('/api/race-details/{sid}')
def detail(sid: str):
    try:
        out = saved(library,sid)
        out['load_status'] = LOADS.get(sid, {'state':'idle'})
        out['metadata'] = library.session(sid)
        try: out['pace'] = library.race(sid)
        except KeyError: out['pace'] = None
        return out
    except KeyError: raise HTTPException(404,'Session not in library')

@router.post('/api/race-details/{sid}/load',status_code=202)
def refresh(sid: str, _admin: None = Depends(require_admin)):
    try: library.session(sid)
    except KeyError: raise HTTPException(404,'Session not in library')
    if not re.fullmatch(r'openf1-\d+',sid): raise HTTPException(422,'OpenF1 session required')
    if not LOCK.acquire(blocking=False): raise HTTPException(409,'A detail import is running; try again shortly.')
    LOADS[sid] = {'state':'loading'}
    def run():
        try:
            build(library,sid)
            LOADS[sid] = {'state':'complete'}
        except Exception as exc:
            LOADS[sid] = {'state':'failed','message':str(exc)}
        finally: LOCK.release()
    threading.Thread(target=run,daemon=True).start()
    return {'state':'loading','session_id':sid}

@router.get('/race-detail/',response_class=HTMLResponse,include_in_schema=False)
def page():
    return (Path(__file__).parent/'static'/'detail.html').read_text()

@router.get('/detail-assets/{asset}',include_in_schema=False)
def assets(asset: str):
    if asset not in {'detail.js','detail.css','ml.js','cross-season.js','restart.js'}: raise HTTPException(404)
    return Response((Path(__file__).parent/'static'/asset).read_text(),media_type='text/css' if asset.endswith('css') else 'application/javascript')
