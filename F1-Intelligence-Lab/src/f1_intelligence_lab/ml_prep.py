"""Offline-first race audit and point-in-event-time next-lap feature builder.

Run with --fetch-fia once to collect independent classification evidence.
Never writes to the source library. No fitting, imputation or model training.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import re
import sqlite3
import statistics
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

VERSION = '1.0.0'
EVENT_NAMES = dict(zip(
    ['Melbourne','Shanghai','Suzuka','Sakhir','Jeddah','Miami','Imola','Monte Carlo','Catalunya','Montreal','Spielberg','Silverstone','Spa-Francorchamps','Hungaroring','Zandvoort','Monza','Baku','Singapore','Austin','Mexico City','Interlagos','Las Vegas','Lusail','Yas Marina Circuit','Madring'],
    ['Australian','Chinese','Japanese','Bahrain','Saudi Arabian','Miami','Emilia Romagna','Monaco','Spanish','Canadian','Austrian','British','Belgian','Hungarian','Dutch','Italian','Azerbaijan','Singapore','United States','Mexico City','São Paulo','Las Vegas','Qatar','Abu Dhabi','Spanish']))
BASE = 'https://api.openf1.org/v1/'
FEATURES = ['circuit', 'lap_number', 'lag_1_s', 'lag_2_s', 'lag_3_s',
            'rolling_mean_3_s', 'rolling_std_3_s', 'recent_change_s',
            'previous_compound', 'previous_tyre_age', 'previous_stint_lap',
            'previous_pit_out', 'control_state_at_cutoff']
META = ['row_id', 'session_id', 'driver_number', 'race_start', 'prediction_at',
        'latest_feature_at', 'history_laps', 'split', 'session_verified']
LABEL = 'target_lap_time_s'
COMPOUNDS = {'SOFT','MEDIUM','HARD','INTERMEDIATE','WET','UNKNOWN'}

def digest(raw): return hashlib.sha256(raw).hexdigest()
def dt(value):
    result = datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None: raise ValueError('timezone required')
    return result.astimezone(timezone.utc)
def finite(value): return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
def integer(value): return isinstance(value,int) and not isinstance(value,bool)
def normalize(value):
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in unicodedata.normalize('NFKD',value.lower()) if not unicodedata.combining(c)))

def profile(rows):
    fields=sorted({k for row in rows for k in row})
    return {'rows':len(rows),'columns':{key:{'types':sorted({type(row[key]).__name__ for row in rows if key in row}),
            'missing_or_null':sum(row.get(key) is None for row in rows)} for key in fields}}

def cached(root, endpoint, params, sources):
    url = BASE + endpoint + '?' + urlencode(params)
    path = root/'openf1-cache'/(digest(url.encode())+'.json')
    raw = path.read_bytes()
    rows = json.loads(raw)
    if not isinstance(rows,list): raise ValueError('Expected a JSON array: '+endpoint)
    sources.append({'url':url,'path':str(path),'sha256':digest(raw),
                    'cache_mtime':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()})
    return rows

def parse_classification(text):
    """Conservative layout parser: incomplete/ambiguous extraction cannot verify."""
    rows = {}; active = False
    for line in text.splitlines():
        if 'DRIVER' in line and 'LAPS' in line: active = True; continue
        if active and re.search(r'^\s*(FASTEST LAP|NOTES|Timekeeper)',line): break
        if not active: continue
        prefix = re.match(r'^\s*(\d+)\s+(?:(\d+)\s+)?([A-Za-z].*)$',line)
        laps = re.search(r'\s{2,}(\d+)\s{2,}(?:\d+:\d|DNS|DNF|DSQ)',line)
        if not prefix: continue
        disqualified=bool(re.search(r'\b(DQ|DSQ)\b',line))
        if not laps and not disqualified: continue
        first,second,tail = prefix.groups()
        car = int(second or first); position = int(first) if second else None
        name = re.split(r'\s{2,}',tail)[0].replace('*','').strip()
        fast = re.search(r'(?<![\d:])(\d{1,2}):(\d{2}\.\d{3})\s+(\d{1,3})(?:\s|$)',line)
        if car in rows: raise ValueError('Ambiguous duplicate FIA driver row')
        rows[car] = {'position':position,'laps':int(laps[1]) if laps else None,'name':name,'dsq':disqualified,
                     'fastest_s':int(fast[1])*60+float(fast[2]) if fast else None,
                     'fastest_lap':int(fast[3]) if fast else None}
    return rows

def evidence(section, root, fetch):
    candidates = [r for r in section.get('rows',[]) if 'final race classification' in r.get('title','').lower()
                  and not re.search(r'recalled|provisional|sprint',r.get('title',''),re.I)]
    urls = list(dict.fromkeys(r['url'] for r in candidates))
    if len(urls)!=1: raise ValueError(f'Expected one unambiguous FIA final race classification, found {len(urls)}')
    parsed = urlparse(urls[0])
    url = urlunparse(parsed._replace(path=quote(unquote(parsed.path),safe='/')))
    if parsed.scheme!='https' or parsed.hostname not in {'www.fia.com','api.fia.com'} or not parsed.path.lower().endswith('.pdf'):
        raise ValueError('Not an approved official FIA PDF URL')
    path = root/(digest(url.encode())+'.pdf')
    if not path.exists():
        if not fetch: raise ValueError('FIA evidence not cached; run with --fetch-fia')
        time.sleep(.3)
        with urlopen(Request(url,headers={'User-Agent':'RaceLab-local-research/1.0'}),timeout=25) as response:
            if urlparse(response.url).hostname not in {'www.fia.com','api.fia.com'}: raise ValueError('Unexpected document redirect')
            raw = response.read(10_000_001)
        if len(raw)>10_000_000 or not raw.startswith(b'%PDF'): raise ValueError('Invalid or oversized PDF')
        path.write_bytes(raw)
    raw = path.read_bytes()
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    text = '\n'.join(p.extract_text(extraction_mode='layout') or '' for p in reader.pages)
    return text, {'url':url,'sha256':digest(raw),'path':str(path),
                  'document_header':' '.join((reader.pages[0].extract_text() or '').split())[:1000],
                  'cached_at':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()}

def reconcile(meta, session, sections, raw_laps, text, header=None):
    failures=[]; official=parse_classification(text)
    heading=normalize(header if header is not None else text)
    event=EVENT_NAMES.get(meta['event'],'UNMAPPED')
    if meta['event']=='Catalunya' and meta['year']>=2026: event='Barcelona-Catalunya'
    if normalize(str(meta['year'])+' '+event+' Grand Prix') not in heading: failures.append('FIA event and year not confirmed')
    if 'finalraceclassification' not in heading: failures.append('FIA classification heading missing')
    results=sections.get('results',{}).get('rows',[])
    drivers=sections.get('drivers',{}).get('rows',[])
    numbers=[r.get('driver_number') for r in results]
    if len(numbers)!=len(set(numbers)): failures.append('Duplicate provider result drivers')
    driver_map={r['driver_number']:r for r in drivers}
    if len(driver_map)!=len(drivers): failures.append('Duplicate provider driver identities')
    if len(official)<10 or set(numbers)!=set(official): failures.append('FIA/provider driver-set mismatch or incomplete PDF parse')
    anchors=0
    for result in results:
        car=result.get('driver_number'); ref=official.get(car)
        if not ref: continue
        name=driver_map.get(car,{}).get('full_name','')
        # Name words can be arranged differently by the two sources; exact word-set match.
        def words(s):
            return sorted(normalize(w) for w in s.split() if normalize(w))
        aliases={'andreakimiantonelli':'kimiantonelli'}
        if words(name)!=words(ref['name']) and aliases.get(normalize(ref['name']),normalize(ref['name']))!=aliases.get(normalize(name),normalize(name)):
            failures.append(f'Car {car}: FIA/provider identity mismatch')
        if ref['laps'] is not None and result.get('number_of_laps')!=ref['laps']: failures.append(f'Car {car}: completed-lap mismatch')
        if ref.get('dsq') and not result.get('dsq'): failures.append(f'Car {car}: DSQ mismatch')
        if result.get('position')!=ref['position']: failures.append(f'Car {car}: final-position mismatch')
        if ref['fastest_lap'] is not None:
            matches=[r for r in raw_laps if r.get('driver_number')==car and r.get('lap_number')==ref['fastest_lap']]
            if len(matches)!=1 or not finite(matches[0].get('lap_duration')) or abs(matches[0]['lap_duration']-ref['fastest_s'])>.005:
                failures.append(f'Car {car}: published fastest-lap anchor mismatch')
            else: anchors+=1
    if anchors<10: failures.append('Fewer than 10 independently matched lap-time anchors')
    return {'passed':not failures,'failures':failures,'official_drivers':len(official),'matched_fastest_laps':anchors,
            'scope':'Driver identities, final positions, completed lap counts and published fastest-lap anchors; not certification of every timing/stint record.'}

def validate_laps(rows, session, driver_numbers, now, results=()):
    counts=Counter((r.get('driver_number'),r.get('lap_number')) for r in rows)
    completed={r.get('driver_number'):r['number_of_laps'] for r in results
               if integer(r.get('number_of_laps')) and not r.get('dsq')}
    valid=[]; quarantine=[]
    for index,r in enumerate(rows):
        reasons=[]; car=r.get('driver_number'); lap=r.get('lap_number'); duration=r.get('lap_duration')
        if counts[(car,lap)]>1: reasons.append('duplicate_driver_lap')
        if car not in driver_numbers: reasons.append('unknown_driver')
        if not integer(lap) or not 1<=lap<=300: reasons.append('invalid_lap_number')
        if integer(lap) and car in completed and lap>completed[car]: reasons.append('exceeds_classified_completed_laps')
        if r.get('session_key')!=session['session_key'] or r.get('meeting_key')!=session['meeting_key']: reasons.append('wrong_session_or_meeting')
        if not finite(duration) or not 1<=duration<=3600: reasons.append('missing_or_invalid_duration')
        if not isinstance(r.get('is_pit_out_lap'),bool): reasons.append('invalid_pit_out_flag')
        try:
            start=dt(r['date_start']); end=start+timedelta(seconds=duration) if finite(duration) else start
            if start.year!=session['year'] or start.date()!=dt(session['date_start']).date(): reasons.append('wrong_race_date')
            if start>now or end>now: reasons.append('future_timing')
        except (TypeError,ValueError,KeyError,AttributeError,OverflowError): reasons.append('missing_or_invalid_timestamp')
        sectors=[r.get(f'duration_sector_{i}') for i in (1,2,3)]
        if all(finite(s) and s>0 for s in sectors) and finite(duration) and abs(sum(sectors)-duration)>.02:
            reasons.append('sector_sum_mismatch')
        if reasons: quarantine.append({'row_index':index,'driver_number':car,'lap_number':lap,'reasons':reasons,
                                       'raw':json.loads(json.dumps(r),parse_constant=lambda v:{'invalid_numeric_literal':v})})
        else: valid.append(dict(r,_start=start,_end=end))
    return valid,quarantine

def control_at(events, cutoff):
    state='UNKNOWN'
    for event in events:
        if dt(event['date'])>cutoff: break
        message=event.get('message','').upper(); flag=event.get('flag')
        if message=='SESSION STARTED' or (flag=='GREEN' and event.get('scope')=='Track'): state='GREEN'
        if 'SAFETY CAR' in message and 'DEPLOYED' in message: state='VSC' if 'VIRTUAL' in message else 'SC'
        if 'SAFETY CAR' in message and ('ENDING' in message or 'IN THIS LAP' in message): state='UNKNOWN'
        if flag in {'RED','YELLOW','DOUBLE YELLOW'}: state=flag
        if flag=='CLEAR': state='UNKNOWN'
    return state

def make_features(valid, session, stints, control):
    """Only completed, contiguous t-3..t-1 laps and messages at/before t start."""
    groups=defaultdict(dict); skipped=Counter(); features=[]
    events=sorted(control,key=lambda e:dt(e['date']))
    for row in valid: groups[row['driver_number']][row['lap_number']]=row
    for car,laps in sorted(groups.items()):
        for lap,target in sorted(laps.items()):
            history=[laps.get(n) for n in range(lap-3,lap)]
            if any(h is None for h in history): skipped['insufficient_contiguous_history']+=1; continue
            cutoff=target['_start']
            if any(h['_end']>cutoff for h in history): skipped['history_not_completed_at_cutoff']+=1; continue
            # Start estimates have sub-second jitter. Do not repair them or move the
            # prediction cutoff. Every history row must still end before cutoff.
            prev=history[-1]
            # Never use final stint end, number of future stints, or target-lap compound.
            prior_stints=[s for s in stints if s.get('driver_number')==car and integer(s.get('lap_start')) and s['lap_start']<=lap-1]
            prior_stints.sort(key=lambda s:s['lap_start'])
            s=prior_stints[-1] if prior_stints else None
            if not s or s.get('compound') not in COMPOUNDS or not integer(s.get('tyre_age_at_start')) or s['tyre_age_at_start']<0:
                skipped['missing_previous_tyre_context']+=1; continue
            if len([x for x in prior_stints if x['lap_start']==s['lap_start']])!=1:
                skipped['ambiguous_previous_stint']+=1; continue
            values=[h['lap_duration'] for h in history]
            features.append({'driver_number':car,'lap_number':lap,'circuit':session['circuit_short_name'],
                'race_start':session['date_start'],'prediction_at':cutoff.isoformat(),
                'latest_feature_at':max([h['_end'] for h in history]+[dt(e['date']) for e in events if dt(e['date'])<=cutoff]).isoformat(),
                'history_laps':','.join(str(h['lap_number']) for h in history),
                'lag_1_s':values[-1],'lag_2_s':values[-2],'lag_3_s':values[-3],
                'rolling_mean_3_s':round(statistics.mean(values),6),'rolling_std_3_s':round(statistics.pstdev(values),6),
                'recent_change_s':round(values[-1]-values[-2],6),'previous_compound':s['compound'],
                'previous_tyre_age':s['tyre_age_at_start']+(lap-1)-s['lap_start']+1,
                'previous_stint_lap':(lap-1)-s['lap_start']+1,
                'previous_pit_out':int(prev['is_pit_out_lap']),
                'control_state_at_cutoff':control_at(events,cutoff),LABEL:target['lap_duration']})
    return features,dict(skipped)

def split_for(start):
    # Fixed before inspecting labels; whole races, never randomized laps.
    date=dt(start)
    if date<dt('2025-09-01T00:00:00Z'): return 'train'
    if date<dt('2025-11-01T00:00:00Z'): return 'validation'
    if date<dt('2026-01-01T00:00:00Z'): return 'test'
    return 'future_holdout'  # separate season / regulation-era distribution shift

def write_csv(path, rows, fields):
    with path.open('x',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def run(root, output, fetch=False, evidence_dir=None):
    root=Path(root).resolve(); output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    evidence_dir=Path(evidence_dir or root/'ml-evidence'); evidence_dir.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc)
    db=sqlite3.connect((root/'library.sqlite3').as_uri()+'?mode=ro',uri=True)
    # One consistent read transaction; read-only connection never migrates the source DB.
    db.execute('BEGIN')
    sessions=[json.loads(r[0]) for r in db.execute('SELECT metadata FROM sessions ORDER BY id')]
    details={sid:json.loads(payload) for sid,payload in db.execute('SELECT id,payload FROM race_details')}
    db.close()
    reports=[]; all_features=[]; all_quarantine=[]; splits=defaultdict(list)
    for meta in sessions:
        sid=meta['id']; report={'session_id':sid,'name':meta['name'],'sources':[],'blockers':[]}
        try:
            if not re.fullmatch(r'openf1-\d+',sid) or meta.get('session_code')!='R': raise ValueError('Only historical OpenF1 race sessions are eligible')
            key=int(sid.split('-')[1]); sources=report['sources']
            index=cached(root,'sessions',{'year':meta['year'],'session_name':'Race'},sources)
            matches=[s for s in index if s['session_key']==key]
            if len(matches)!=1: raise ValueError('Missing or ambiguous session metadata')
            session=matches[0]
            if session['year']!=meta['year'] or session['circuit_short_name']!=meta['event']: raise ValueError('Library/provider event mismatch')
            if dt(session['date_end'])>now or session.get('is_cancelled'): raise ValueError('Future or cancelled session')
            report['race_start']=session['date_start']; report['split']=split_for(session['date_start'])
            report['historical_age_days']=(now-dt(session['date_start'])).days
            report['import_age_hours']=round((now-dt(meta['retrieved_at'])).total_seconds()/3600,2)
            if report['import_age_hours']<0: report['blockers'].append('Future import timestamp')
            raw=cached(root,'laps',{'session_key':key},sources)
            sections=details.get(sid,{}).get('sections',{})
            report['detail_sha256']=digest(json.dumps(sections,sort_keys=True).encode())
            # Read original endpoint caches; dossier copies alone aren't sufficient provenance.
            drivers=cached(root,'drivers',{'session_key':key},sources)
            stints=cached(root,'stints',{'session_key':key},sources)
            control=cached(root,'race_control',{'session_key':key},sources)
            results=cached(root,'session_result',{'session_key':key},sources)
            if sections.get('results',{}).get('rows',[])!=results or sections.get('drivers',{}).get('rows',[])!=drivers:
                report['blockers'].append('Dossier/cache result or driver mismatch')
            sections=dict(sections,results={'rows':results},drivers={'rows':drivers})
            report['schema_profile']={key:profile(rows) for key,rows in [('laps',raw),('drivers',drivers),('stints',stints),('race_control',control),('results',results)]}
            valid,quarantine=validate_laps(raw,session,{d['driver_number'] for d in drivers},now,results)
            report['raw_laps']=len(raw); report['valid_laps']=len(valid); report['quarantined_laps']=len(quarantine)
            report['row_failure_counts']=dict(Counter(reason for q in quarantine for reason in q['reasons']))
            for q in quarantine: all_quarantine.append(dict(session_id=sid,**q))
            if not raw: report['blockers'].append('No raw lap records')
            if any(d.get('session_key')!=key or d.get('meeting_key')!=session['meeting_key'] for d in drivers+stints+control):
                report['blockers'].append('Auxiliary records refer to wrong session/meeting')
            for event in control: dt(event['date'])
            # Identity/event/date are verified independently; cached link existence is never a pass.
            try:
                text, proof=evidence(sections.get('fia',{}),evidence_dir,fetch)
                report['fia_evidence']=proof
                # Confirm linked filename year matches the session as well as the PDF content.
                if not unquote(urlparse(proof['url']).path).rsplit('/',1)[-1].startswith(str(meta['year'])):
                    raise ValueError('FIA filename year mismatch')
                check=reconcile(meta,session,sections,raw,text,proof['document_header'])
                report['reconciliation']=check
                report['blockers'].extend(check['failures'])
            except Exception as exc:
                report['blockers'].append('FIA verification unavailable: '+str(exc))
            verified=not report['blockers']
            features,skipped=make_features(valid,session,stints,control)
            report['feature_exclusions']=skipped; report['candidate_rows']=len(features)
            report['distribution']={'min_s':min((r['lap_duration'] for r in valid),default=None),
                                    'max_s':max((r['lap_duration'] for r in valid),default=None),
                                    'laps_over_180s':sum(r['lap_duration']>180 for r in valid)}
            by_car=defaultdict(list)
            for row in valid: by_car[row['driver_number']].append(row)
            overlaps=[]
            for _car,rows in by_car.items():
                rows.sort(key=lambda r:r['lap_number'])
                overlaps.extend(round((a['_end']-b['_start']).total_seconds(),6) for a,b in zip(rows,rows[1:]) if a['_end']>b['_start'])
            report['timestamp_overlap_observations']={'count':len(overlaps),'max_seconds':max(overlaps,default=0),
                'policy':'No timestamp repair. A historical lap is never used if its calculated end exceeds prediction cutoff; earlier boundary jitter is reported, not rounded away.'}
            report['missing_lap_numbers']={str(car):sorted(set(range(1,max(r['lap_number'] for r in valid if r['driver_number']==car)+1))-{r['lap_number'] for r in valid if r['driver_number']==car}) for car in {r['driver_number'] for r in valid}}
            for row in features:
                row.update(row_id=f'{sid}:{row["driver_number"]}:{row["lap_number"]}',session_id=sid,split=report['split'],session_verified=int(verified))
                all_features.append(row)
                if verified: splits[report['split']].append(row)
            report['verified_for_prep']=verified
        except Exception as exc:
            report['blockers'].append('Session preparation failed: '+str(exc)); report['verified_for_prep']=False
        reports.append(report)
        print(sid, 'PASS' if report['verified_for_prep'] else 'QUARANTINE',report.get('candidate_rows',0),'candidates',flush=True)
    fields=META+FEATURES+[LABEL]
    write_csv(output/'candidates_NOT_FOR_TRAINING.csv',all_features,fields)
    for split in ['train','validation','test','future_holdout']: write_csv(output/(split+'.csv'),splits[split],fields)
    with (output/'quarantined_laps.jsonl').open('x') as file:
        for row in all_quarantine: file.write(json.dumps(row,allow_nan=False)+'\n')
    passed=sum(r['verified_for_prep'] for r in reports)
    summary={'version':VERSION,'created_at':now.isoformat(),'sessions':len(reports),'verified_sessions':passed,
             'quarantined_sessions':len(reports)-passed,'raw_laps':sum(r.get('raw_laps',0) for r in reports),
             'quarantined_laps':len(all_quarantine),'candidate_rows':len(all_features),
             'split_rows':{k:len(v) for k,v in splits.items()},'features':FEATURES,'target':LABEL,
             'training_gate':'ready_for_baseline' if all(splits[s] for s in ['train','validation','test']) else 'blocked_insufficient_verified_splits',
             'session_reports':reports,'code_sha256':digest(Path(__file__).read_bytes())}
    (output/'audit.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
    lines=['# ML data preparation audit','',f'Generated {now.isoformat()}',
           f'\n{len(reports)} sessions audited; {passed} verified for preparation; {len(reports)-passed} quarantined.',
           f'\nRaw laps: {summary["raw_laps"]}; quarantined raw laps: {len(all_quarantine)}; candidate feature rows: {len(all_features)}.',
           '\n## Verified split sizes','']+[f'- {k}: {len(v)} rows' for k,v in splits.items()]
    lines+=['','## Session decisions','','| Race | Verification | Candidate rows | Blockers |','|---|---|---:|---|']
    for r in reports: lines.append(f'| {r["name"]} | {"PASS" if r["verified_for_prep"] else "QUARANTINE"} | {r.get("candidate_rows",0)} | '+('; '.join(r['blockers']) or 'None')+' |')
    lines+=['','## Scope and limitations','','Verification covers final classification and fastest-lap anchors, not every lap or tyre record. Labels include pit/neutralised laps and outliers; no hindsight clean-lap filtering. Features use reconstructed event time, not a captured live feed: publication delays and later provider corrections are unknown. Original data was not changed. Candidates are diagnostic only; train from the explicit feature allowlist and verified split files. No model has been trained.']
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (output/'feature_contract.json').write_text(json.dumps({'version':VERSION,'features':FEATURES,'metadata_not_for_model':META,
        'target':LABEL,'horizon':'Lap t at recorded start; only completed t-3,t-2,t-1 laps',
        'split_boundaries_utc':['2025-09-01','2025-11-01','2026-01-01'],
        'future_holdout':'2026 is reserved for separate cross-season evaluation',
        'availability':'Reconstructed event time, not verified arrival time. Historical corrections and feed latency remain unknown.',
        'forbidden':['target-lap sectors','target-lap compound','target-lap flags','final results','whole-race medians','future stint ends'],
        'fit_policy':'Fit encoders, scaling, feature selection and any imputation ONLY on train. None fitted in this task.'},indent=2))
    manifest={p.name:digest(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='session_reports'},indent=2))
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,default=Path('.local-data'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fetch-fia',action='store_true')
    parser.add_argument('--evidence-dir',type=Path)
    args=parser.parse_args()
    run(args.data_root,args.output,args.fetch_fia,args.evidence_dir)
