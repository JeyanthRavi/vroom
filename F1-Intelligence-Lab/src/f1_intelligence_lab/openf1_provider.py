"""Public OpenF1 historical adapter, rate-limited and cached locally."""
import csv
import hashlib
import io
import json
import math
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .race_analysis import analyze, FIELDS

BASE = 'https://api.openf1.org/v1/'
NAMES = {'R':'Race','Q':'Qualifying','S':'Sprint','SQ':'Sprint Qualifying','FP1':'Practice 1','FP2':'Practice 2','FP3':'Practice 3'}


def date(value):
    return datetime.fromisoformat(value.replace('Z','+00:00'))


class Client:
    def __init__(self, root):
        self.root = root / 'openf1-cache'
        self.root.mkdir(exist_ok=True)
        self.urls = []

    def get(self, endpoint, **params):
        url = BASE + endpoint + '?' + urlencode(params)
        self.urls.append(url)
        path = self.root / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        if path.exists() and (endpoint != 'sessions' or time.time()-path.stat().st_mtime < 21600):
            return json.loads(path.read_text())
        for attempt in range(3):
            time.sleep(.5)
            try:
                with urlopen(Request(url, headers={'User-Agent':'RaceLab-local-research/1.0'}), timeout=45) as response:
                    raw = response.read(30_000_001)
                if len(raw) > 30_000_000: raise ValueError('Provider response exceeds safety limit.')
                result = json.loads(raw)
                if not isinstance(result,list): raise ValueError('Provider returned an unexpected response.')
                # Empty responses can be transient; never permanently cache them.
                if result:
                    temp = path.with_suffix('.tmp');temp.write_text(json.dumps(result));temp.replace(path)
                return result
            except HTTPError as exc:
                if exc.code == 404 and endpoint == 'car_data': return []
                if exc.code not in {429,500,502,503,504} or attempt == 2: raise
                retry = exc.headers.get('Retry-After','5')
                time.sleep(min(60,max(1,int(retry))) if retry.isdigit() else 5)


def status_for_lap(start, end, control):
    """Conservative event-derived flags, not official per-lap accuracy metadata."""
    state, sectors, worst = 'UNKNOWN', set(), set()
    for event in control:
        at = date(event['date'])
        if at > end: break
        if at >= start: worst.add('UNKNOWN' if sectors else state)
        message = event.get('message','').upper()
        flag, scope = event.get('flag'), event.get('scope')
        if message == 'SESSION STARTED': state = 'GREEN'
        if 'VIRTUAL SAFETY CAR' in message and 'DEPLOYED' in message: state = 'VSC'
        elif 'SAFETY CAR' in message and 'DEPLOYED' in message: state = 'SC'
        # An ending announcement is not the exact green restart timestamp.
        # Without an explicit restart event, keep subsequent coverage unknown
        # instead of falsely claiming the rest of the race ran under SC/VSC.
        if 'SAFETY CAR' in message and ('IN THIS LAP' in message or 'ENDING' in message): state = 'UNKNOWN'
        if flag == 'RED': state = 'RED'
        if flag == 'GREEN' and scope == 'Track': state = 'GREEN';sectors.clear()
        if flag in {'YELLOW','DOUBLE YELLOW'}:
            sectors.add(event.get('sector') or 'track')
        if flag == 'CLEAR': sectors.discard(event.get('sector') or 'track')
        if at >= start: worst.add('UNKNOWN' if sectors else state)
    worst.add('UNKNOWN' if sectors else state)
    return next((v for v in ['RED','SC','VSC','UNKNOWN','GREEN'] if v in worst),'UNKNOWN')


def import_openf1(library, year, event, code, progress=lambda message:None, *, include_telemetry=True):
    from telemetry_pit_crew.contracts import Lap, TelemetrySample
    if year < 2023: raise ValueError('OpenF1 historical coverage starts in 2023. Select FastF1 for older sessions, subject to availability.')
    client = Client(library.root)
    progress('Finding the historical OpenF1 session.')
    sessions = client.get('sessions',year=year,session_name=NAMES[code])
    query = event.casefold().strip()
    matches = [s for s in sessions if any(query in str(s.get(k,'')).casefold() for k in ['location','circuit_short_name','country_name'])]
    if len(matches) != 1:
        choices=', '.join(s['circuit_short_name'] for s in (matches or sessions))
        raise ValueError(f'Choose a unique circuit name. Available matches: {choices}')
    session = matches[0]
    if date(session['date_end']) >= datetime.now(timezone.utc): raise ValueError('Only completed historical sessions are supported.')
    key = session['session_key'];sid=f'openf1-{key}'
    if not include_telemetry:
        if code not in {'R', 'S'}:
            raise ValueError('Timing-only import requires a race or sprint.')
        if library.lap_summaries(sid):
            raise ValueError('Timing-only import cannot replace existing telemetry. Use a full import.')
    progress('Downloading complete available lap timing, stints, pit events and race control.')
    raw_laps=client.get('laps',session_key=key)
    drivers=client.get('drivers',session_key=key)
    stints=[dict(s, compound=s.get('compound') or 'UNKNOWN')
            for s in client.get('stints',session_key=key)]
    pits=client.get('pit',session_key=key)
    control=sorted(client.get('race_control',session_key=key),key=lambda x:x['date'])
    driver_codes={d['driver_number']:d.get('name_acronym') or str(d['driver_number']) for d in drivers}
    pit_keys={(p['driver_number'],p['lap_number']) for p in pits}
    deleted=set()
    for c in control:
        m=re.search(r'CAR (\d+) .*?DELETED.*?\bLAP (\d+)',c.get('message',''))
        if m: deleted.add((int(m[1]),int(m[2])))
    usable=[];skipped=0
    for r in raw_laps:
        duration=r.get('lap_duration');number=r['driver_number'];lap=r['lap_number']
        if not duration or not math.isfinite(duration) or not 1<=duration<=3600 or not r.get('date_start') or number not in driver_codes:
            skipped+=1;continue
        # Provider stints for non-starters/retirements can have unknown bounds.
        stint=next((s for s in stints if s['driver_number']==number
                    and s.get('lap_start') is not None and s.get('lap_end') is not None
                    and s['lap_start']<=lap<=s['lap_end']),None)
        if stint is None: skipped+=1;continue
        start=date(r['date_start']);end=start+timedelta(seconds=duration)
        flag=status_for_lap(start,end,control)
        if r.get('is_pit_out_lap') or (number,lap) in deleted: flag='UNKNOWN'
        usable.append(dict(raw=r,driver=driver_codes[number],stint=stint,flag=flag))
    if not usable: raise ValueError('No usable lap records returned for this session.')
    race=None
    if code in {'R','S'}:
        out=io.StringIO();writer=csv.writer(out,lineterminator='\n');writer.writerow(FIELDS)
        for item in usable:
            r=item['raw'];s=item['stint']
            writer.writerow([item['driver'],r['lap_number'],r['lap_duration'],s['compound'],s['stint_number'],int((r['driver_number'],r['lap_number']) in pit_keys),item['flag']])
        race=analyze(out.getvalue(),f"{year} {session['circuit_short_name']} · {NAMES[code]}",'openf1_historical')
        race['session_id']=sid
        race['warnings'] += [f'{skipped} records missing valid timing, start timestamp, driver or stint were omitted.',
            'Flags are conservatively reconstructed from race-control messages. After a safety-car ending announcement, laps stay UNKNOWN until an explicit green restart is available. This may exclude later stints; use the all-laps chart to inspect them. Not official per-lap accuracy certification.']
        race['methodology']['clean_laps'] += ' OpenF1 flags are inferred from race-control events; deleted/pit-out laps are mapped to UNKNOWN.'
    telemetry=[];unavailable=[]
    for index,(number,driver) in enumerate(sorted(driver_codes.items()) if include_telemetry else []):
        progress(f'Loading telemetry {index+1}/{len(driver_codes)}: {driver}')
        candidates=sorted([i for i in usable if i['raw']['driver_number']==number and not i['raw'].get('is_pit_out_lap') and (number,i['raw']['lap_number']) not in deleted and (number,i['raw']['lap_number']) not in pit_keys],key=lambda i:i['raw']['lap_duration'])
        converted=None
        for item in candidates[:3]:
            r=item['raw'];start=date(r['date_start']);end=start+timedelta(seconds=r['lap_duration'])
            samples=client.get('car_data',session_key=key,driver_number=number,**{'date>':start.isoformat(),'date<':end.isoformat()})
            result=[];distance=0.;previous=None
            for sample in sorted(samples,key=lambda s:s['date']):
                t=(date(sample['date'])-start).total_seconds()
                vals=[sample.get(k) for k in ['speed','throttle','brake','n_gear','rpm','drs']]
                if any(v is None or not math.isfinite(float(v)) for v in vals): continue
                if previous and t<=previous[0]: continue
                if previous: distance+=(previous[1]+sample['speed'])/2/3.6*(t-previous[0])
                previous=(t,sample['speed'])
                result.append(TelemetrySample(distance=distance,time=t,speed=sample['speed'],throttle=sample['throttle'],brake=sample['brake'],gear=sample['n_gear'],rpm=sample['rpm'],drs=sample['drs']))
            if len(result)>=3:
                converted=Lap(id=f'{sid}-{driver.lower()}-{r["lap_number"]}',driver=driver,circuit=session['circuit_short_name'],lap_number=r['lap_number'],lap_time=r['lap_duration'],compound=item['stint']['compound'],tyre_life=max(0,r['lap_number']-item['stint']['lap_start']+int(item['stint'].get('tyre_age_at_start') or 0)),samples=result,quality_score=.65)
                break
        if converted: telemetry.append(converted)
        else: unavailable.append(driver)
    metadata=dict(id=sid,name=f"{year} {session['circuit_short_name']} — {code}",year=year,event=session['circuit_short_name'],session_code=code,
                  source_type='openf1_historical',source_url=BASE+'laps?session_key='+str(key),source_urls=client.urls,
                  retrieved_at=datetime.now(timezone.utc).isoformat(),provider_version='OpenF1 v1',drivers_total=len(driver_codes),telemetry_drivers=len(telemetry),unavailable_drivers=unavailable,race_records=race['records'] if race else 0,
                  notes='OpenF1 historical data. Full available race lap timing; one fastest usable non-deleted/non-pit telemetry lap per driver (up to three candidates tried). Sampled speed is integrated for approximate distance. Race flags are inferred conservatively from messages. Lap-relative replay, not race positions. Not live timing.')
    metadata['telemetry_status'] = 'requested' if include_telemetry else 'not_requested'
    if not include_telemetry:
        metadata['notes'] = 'Timing-only import. Car telemetry was not requested; its availability is unknown. Race Lab uses available lap timing, stints and pit events. Race flags are inferred conservatively. Reimport with telemetry enabled to check driver telemetry.'
        race['warnings'].append('Car telemetry was not requested for this timing-only import.')
    progress('Saving validated timing and telemetry atomically.')
    if race:
        race['provenance']={'provider':'OpenF1 v1','session_key':key,'retrieved_at':metadata['retrieved_at'],
                            'source_urls':client.urls,'flag_method':'conservative race-control reconstruction'}
    library.store(metadata,telemetry,race)
    return sid
