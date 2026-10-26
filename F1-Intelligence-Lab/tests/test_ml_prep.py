from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import sqlite3
import pytest
from f1_intelligence_lab.ml_prep import (
    FEATURES, LABEL, META, dt, validate_laps, make_features, parse_classification,
    split_for, reconcile, run, digest, BASE,
)
from urllib.parse import urlencode

START=datetime(2025,9,7,13,tzinfo=timezone.utc)
SESSION={'session_key':1,'meeting_key':2,'year':2025,'circuit_short_name':'Monza',
         'date_start':START.isoformat(),'date_end':(START+timedelta(hours=2)).isoformat()}
NOW=datetime(2026,10,27,tzinfo=timezone.utc)

def raw_laps(n=8):
    return [{'session_key':1,'meeting_key':2,'driver_number':44,'lap_number':i,
             'date_start':(START+timedelta(seconds=90*(i-1))).isoformat(),
             'lap_duration':90.,'is_pit_out_lap':False,
             'duration_sector_1':30.,'duration_sector_2':30.,'duration_sector_3':30.}
            for i in range(1,n+1)]

STINTS=[{'driver_number':44,'lap_start':1,'lap_end':8,'stint_number':1,
         'compound':'MEDIUM','tyre_age_at_start':0}]

def valid(rows): return validate_laps(rows,SESSION,{44},NOW)[0]

def test_feature_contract_and_shifted_history():
    rows,_=make_features(valid(raw_laps()),SESSION,STINTS,[])
    first=rows[0]
    assert first['lap_number']==4 and first['history_laps']=='1,2,3'
    assert first['lag_1_s']==90 and first['previous_tyre_age']==3
    assert first['prediction_at']==first['latest_feature_at']
    assert LABEL not in FEATURES
    assert not set(META)&set(FEATURES)
    assert not any('position' in x or 'fastest' in x or 'target' in x for x in FEATURES)

def test_future_laps_and_target_value_do_not_change_features():
    raw=raw_laps(); before,_=make_features(valid(raw),SESSION,STINTS,[])
    changed=deepcopy(raw)
    for row in changed[3:]:
        row['lap_duration']=120.; row['duration_sector_1']=60.
    after,_=make_features(valid(changed),SESSION,STINTS,[])
    assert {k:before[0][k] for k in FEATURES}=={k:after[0][k] for k in FEATURES}
    assert before[0][LABEL]!=after[0][LABEL]

def test_future_control_and_stint_ends_cannot_leak():
    laps=valid(raw_laps())
    events=[{'date':(START-timedelta(seconds=1)).isoformat(),'message':'SESSION STARTED'}]
    before,_=make_features(laps,SESSION,STINTS,events)
    later=events+[{'date':(START+timedelta(seconds=500)).isoformat(),'flag':'RED','message':'RED FLAG'}]
    stints=deepcopy(STINTS); stints[0]['lap_end']=300
    stints.append({'driver_number':44,'lap_start':7,'compound':'SOFT','tyre_age_at_start':0})
    after,_=make_features(laps,SESSION,stints,later)
    assert before[0]==after[0]
    assert before[0]['control_state_at_cutoff']=='GREEN'

def test_late_previous_lap_is_not_rounded_into_history():
    raw=raw_laps(); raw[2]['lap_duration']=90.001; raw[2]['duration_sector_3']=30.001
    rows,exclusions=make_features(valid(raw),SESSION,STINTS,[])
    assert 4 not in {r['lap_number'] for r in rows}
    assert exclusions['history_not_completed_at_cutoff']==1

def test_missing_and_duplicate_laps_break_history_no_silent_dedup():
    raw=raw_laps(); raw.append(deepcopy(raw[2]))
    good,bad=validate_laps(raw,SESSION,{44},NOW)
    assert len(bad)==2 and all('duplicate_driver_lap' in q['reasons'] for q in bad)
    rows,_=make_features(good,SESSION,STINTS,[])
    assert {r['lap_number'] for r in rows}=={7,8}

@pytest.mark.parametrize('field,value,reason',[
    ('lap_duration',float('nan'),'missing_or_invalid_duration'),
    ('date_start',None,'missing_or_invalid_timestamp'),
    ('driver_number',99,'unknown_driver'),
    ('session_key',99,'wrong_session_or_meeting'),
    ('duration_sector_1',50,'sector_sum_mismatch'),
    ('lap_number',True,'invalid_lap_number'),
])
def test_invalid_rows_are_quarantined_without_mutation(field,value,reason):
    rows=raw_laps(1); rows[0][field]=value
    before=repr(rows)
    good,bad=validate_laps(rows,SESSION,{44},NOW)
    assert not good and reason in bad[0]['reasons']
    assert repr(rows)==before

def test_fixed_chronological_race_splits():
    assert split_for('2025-08-31T23:59:59Z')=='train'
    assert split_for('2025-09-01T00:00:00Z')=='validation'
    assert split_for('2025-11-01T00:00:00Z')=='test'
    assert split_for('2026-01-01T00:00:00Z')=='future_holdout'

def test_classification_parser_and_fail_closed_reconciliation():
    text='''2025 ITALIAN GRAND PRIX Final Race Classification
    NO DRIVER NAT ENTRANT LAPS TIME GAP FASTEST ON
    1  44  Lewis HAMILTON  Ferrari  53  1:20:00.000  1:20.000  52  25
    2  4  Lando NORRIS  McLaren  53  1:20:10.000  10.000  1:21.000  50  18
    NOT CLASSIFIED
       14  Fernando ALONSO  Aston Martin  0  DNS
       27  Nico HULKENBERG  Sauber       DQ
    FASTEST LAP
    44 Lewis HAMILTON 1:20.000 on lap 52
    '''
    parsed=parse_classification(text)
    assert set(parsed)=={44,4,14,27}
    assert parsed[44]['fastest_s']==80
    assert parsed[14]['position'] is None and parsed[14]['laps']==0
    assert parsed[27]['dsq'] and parsed[27]['laps'] is None
    report=reconcile({'year':2025,'event':'Monza'},SESSION,{},[],text)
    assert not report['passed']  # link/heading existence alone never verifies a session

def test_offline_run_excludes_unverified_and_preserves_source(tmp_path):
    root=tmp_path/'data'; root.mkdir(); cache=root/'openf1-cache'; cache.mkdir()
    metadata={'id':'openf1-1','name':'Fixture race','year':2025,'event':'Monza',
              'session_code':'R','retrieved_at':'2025-09-08T00:00:00Z'}
    with sqlite3.connect(root/'library.sqlite3') as db:
        db.execute('CREATE TABLE sessions (id TEXT,metadata TEXT)')
        db.execute('INSERT INTO sessions VALUES (?,?)',('openf1-1',json.dumps(metadata)))
        db.execute('CREATE TABLE race_details (id TEXT,payload TEXT)')
    data={'sessions':[SESSION],'laps':raw_laps(),'drivers':[{'driver_number':44,'session_key':1,'meeting_key':2}],
          'stints':[dict(s,session_key=1,meeting_key=2) for s in STINTS],'race_control':[], 'session_result':[]}
    for endpoint,rows in data.items():
        params={'year':2025,'session_name':'Race'} if endpoint=='sessions' else {'session_key':1}
        (cache/(digest((BASE+endpoint+'?'+urlencode(params)).encode())+'.json')).write_text(json.dumps(rows))
    paths=list(root.rglob('*')); before={str(p):digest(p.read_bytes()) for p in paths if p.is_file()}
    report=run(root,tmp_path/'output')
    assert report['candidate_rows']==5 and report['verified_sessions']==0
    assert report['training_gate'].startswith('blocked')
    assert all(count==0 for count in report['split_rows'].values())
    assert before=={str(p):digest(p.read_bytes()) for p in paths if p.is_file()}
    with pytest.raises(FileExistsError): run(root,tmp_path/'output')

def test_verified_loader_allowlist_and_tamper_detection(tmp_path):
    from f1_intelligence_lab.ml_prep import write_csv
    from f1_intelligence_lab.ml_dataset import load_split
    rows,_=make_features(valid(raw_laps()),SESSION,STINTS,[])
    for row in rows:
        row.update(row_id=f'openf1-1:44:{row["lap_number"]}',session_id='openf1-1',split='validation',session_verified=1)
    write_csv(tmp_path/'validation.csv',rows,META+FEATURES+[LABEL])
    (tmp_path/'audit.json').write_text(json.dumps({'training_gate':'ready_for_baseline','split_rows':{'validation':len(rows)},
        'session_reports':[{'session_id':'openf1-1','split':'validation','verified_for_prep':True}]}))
    (tmp_path/'feature_contract.json').write_text(json.dumps({'features':FEATURES,'target':LABEL}))
    (tmp_path/'manifest.json').write_text(json.dumps({p.name:digest(p.read_bytes()) for p in tmp_path.iterdir()}))
    X,y,metadata=load_split(tmp_path,'validation')
    assert set(X[0])==set(FEATURES) and len(y)==5
    assert 'session_id' not in X[0] and metadata[0]['session_id']=='openf1-1'
    with pytest.raises(ValueError,match='reserved'): load_split(tmp_path,'future_holdout')
    with (tmp_path/'validation.csv').open('a') as file: file.write('\n')
    with pytest.raises(ValueError,match='checksum'): load_split(tmp_path,'validation')
