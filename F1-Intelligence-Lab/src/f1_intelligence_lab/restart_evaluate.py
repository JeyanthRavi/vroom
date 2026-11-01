"""Frozen 2026 restart regression check. Never trains, tunes or promotes models."""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import torch
from threadpoolctl import threadpool_limits

from .cross_season import paired_race_interval
from .dl_train import score
from .ml_prep import digest, dt
from .ml_sequences import build_split, flattened
from .ml_train import baseline, evaluate, save_json
from .robust_train import predict_saved, transform


def verify(directory, names):
    directory=Path(directory)
    hashes=json.loads((directory/'artifact_hashes.json').read_text())
    for name in names:
        if hashes.get(name)!=digest((directory/name).read_bytes()):
            raise ValueError('Artifact integrity failure: '+name)
    return {name:hashes[name] for name in names}


def masks(data, ratio):
    converted=transform(data,ratio)
    x=converted['x']; seq=converted['sequences']; y=np.asarray(data['y'])
    return {
        'previous_lap_over_180s':np.array([r['lag_1_s']>180 for r in data['x']]),
        'previous_lap_over_frozen_ratio':np.array([bool(r['previous_long_lap']) for r in x]),
        'within_three_laps_after_long_history':np.array([r['laps_since_long']<=2 for r in x]),
        'known_control_restart_at_cutoff':np.array([bool(r['restart_state_transition']) for r in x]),
        'recent_known_control_restart':np.array([bool(r['restart_state_transition']) or any(s['restart_transition'] for s in steps[-3:]) for r,steps in zip(x,seq)]),
        'observed_target_over_180s':y>180,
        'ordinary_target_no_recent_long_history':np.array([r['laps_since_long']>2 for r in x]) & (y<=180),
    }


def sliced_score(data, prediction, mask):
    ix=np.flatnonzero(mask)
    if not len(ix):return {'rows':0,'races':0}
    result=evaluate(np.asarray(data['y'])[ix],np.asarray(prediction)[ix],
                    [data['meta'][i] for i in ix],[data['x'][i] for i in ix])
    result['races']=len(result['per_race'])
    return result


def resumption_events(events):
    """Evaluation-only annotations; notices and infringement messages are not restarts."""
    suspended=False;result=[]
    for e in sorted(events,key=lambda e:dt(e['date'])):
        message=e.get('message','').upper()
        if e.get('flag')=='RED' or message.startswith('RED FLAG - RACE SUSPENDED'):
            suspended=True
        elif message=='SESSION STARTED' and suspended:
            result.append(e);suspended=False
    return result


def source_restart_slice(data,dataset,source_root):
    audit=json.loads((Path(dataset)/'audit.json').read_text())
    mask=np.zeros(len(data['y']),dtype=bool);evidence=[]
    for report in audit['session_reports']:
        sid=report['session_id']
        if sid not in {m['session_id'] for m in data['meta']}:continue
        source=next(s for s in report['sources'] if '/race_control?' in s['url'])
        raw=(Path(source_root)/'openf1-cache'/(digest(source['url'].encode())+'.json')).read_bytes()
        if digest(raw)!=source['sha256']:raise ValueError('Race-control source changed')
        for event in resumption_events(json.loads(raw)):
            evidence.append({'session_id':sid,'event':event,'source':source})
            # Event lap anchors the window; never stretch it to later eligible rows.
            lap=event.get('lap_number')
            if not isinstance(lap,int):continue
            for i,(m,x) in enumerate(zip(data['meta'],data['x'])):
                if m['session_id']==sid and dt(m['prediction_at'])>=dt(event['date']) and lap<=x['lap_number']<=lap+2:
                    mask[i]=True
    return mask,evidence


def run(dataset,source_root,robust_run,original_evaluation,output,skill_tools=None):
    robust=Path(robust_run);original=Path(original_evaluation);out=Path(output)
    # Verify all trained artifacts before reading any evaluation examples.
    hashes=json.loads((robust/'artifact_hashes.json').read_text())
    frozen=verify(robust,list(hashes))
    previous=verify(original,['results.json','predictions.csv','protocol.json'])
    selection=json.loads((robust/'selection.json').read_text())
    training=json.loads((robust/'protocol.json').read_text())
    prior=json.loads((original/'results.json').read_text())
    manifest=digest((Path(dataset)/'manifest.json').read_bytes())
    if manifest!=prior['protocol']['dataset_manifest_sha256']:raise ValueError('Dataset manifest changed')
    out.mkdir(parents=True,exist_ok=False)
    protocol={'primary':'race_macro_mae_s','ratio':selection['ratio'],'control_version':training.get('control_version',1),
        'selection_frozen_on_2025':selection['winner'],
        'policy':'Previously examined 2026 regression test. No fitting, tuning, reselection or promotion.',
        'slices':'Previous duration >180s; frozen ratio; first three following long laps; known RED/SC/VSC-to-GREEN transitions; target >180s.',
        'supplemental_slice':'Post-hoc diagnostic after empty feature-transition slices: raw SESSION STARTED following red suspension, event lap through lap+2, target starts at/after event. No feature changes.',
        'model_artifact_hashes':frozen,'prior_evaluation_hashes':previous,
        'dataset_manifest_sha256':manifest,'code_sha256':digest(Path(__file__).read_bytes())}
    save_json(out/'protocol.json',protocol)
    data=build_split(dataset,source_root,'future_holdout',allow_future_evaluation=True,control_version=training.get('control_version',1))
    if any(not m['race_start'].startswith('2026') for m in data['meta']):raise ValueError('Expected 2026 only')
    rows=list(csv.DictReader((original/'predictions.csv').open()))
    if len(rows)!=len(data['y']):raise ValueError('Prior evaluation cohort changed')
    for row,m,y in zip(rows,data['meta'],data['y']):
        if row['row_id']!=m['row_id'] or float(row['actual_s'])!=y:raise ValueError('Prior row alignment changed')
    values={n:baseline(n,data['x']) for n in ['last_lap','rolling_median']}
    values.update({new:np.array([float(r[old]) for r in rows]) for new,old in
        [('original_boosting','boosting_sequence'),('original_gru','gru_full')]})
    values['boosting_2025']=baseline('last_lap',data['x'])+joblib.load(robust/'unmodified_sequence_boosting.joblib').predict(flattened(data))
    values['restart_boosting']=predict_saved(robust,data,'robust_tree')
    values['restart_gru']=predict_saved(robust,data,'robust_gru')
    scores={n:score(data,p) for n,p in values.items()}
    conditions=masks(data,selection['ratio'])
    conditions['source_red_flag_resumption_window'],events=source_restart_slice(data,dataset,source_root)
    slices={k:{n:sliced_score(data,p,mask) for n,p in values.items()} for k,mask in conditions.items()}
    result={'protocol':protocol,'coverage':data['coverage'],'scores':scores,'slices':slices,
        'paired_vs_median':{n:paired_race_interval(s,scores['rolling_median']) for n,s in scores.items() if n!='rolling_median'},
        'races':prior['races'],'excluded_races':prior['excluded_races'],'sources':data['sources'],'resumption_evidence':events,
        'limitations':'Regression check, not untouched generalization. Control-state transitions are reconstructed proxies, not individually adjudicated restart events. Long target laps retained. Sparse slices may cover very few races. Original models used two older training races; boosting_2025 is the same-cohort comparator.'}
    with (out/'predictions.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['row_id','session_id','driver','lap','actual_s']+list(values)+list(conditions));w.writeheader()
        for i,(m,x,y) in enumerate(zip(data['meta'],data['x'],data['y'])):
            w.writerow(dict(row_id=m['row_id'],session_id=m['session_id'],driver=m['driver_number'],lap=x['lap_number'],actual_s=y,
                **{n:float(p[i]) for n,p in values.items()},**{n:bool(mask[i]) for n,mask in conditions.items()}))
    save_json(out/'results.json',result)
    if skill_tools:
        for name,s in scores.items():
            subprocess.run([sys.executable,str(Path(skill_tools)/'experiment_tracker.py'),'--log-file',str(out/'experiments.json'),
                'log','--name','2026_restart_regression_'+name,'--params',json.dumps({'fit':False,'ratio':selection['ratio']}),
                '--metrics',json.dumps({k:v for k,v in s.items() if isinstance(v,(int,float))}),
                '--notes','Previously seen 2026; no selection. Lower error better.'],check=True,capture_output=True)
    lines=['# Frozen restart models on 2026','','No retraining, tuning, reselection or promotion.',
        '',json.dumps(data['coverage'],indent=2),'','| Model | Equal-race MAE | Pooled RMSE | Pooled R² |','|---|---:|---:|---:|']
    lines += [f"| {n} | {s['race_macro_mae_s']:.4f} | {s['rmse_s']:.4f} | {s['r2']:.4f} |" for n,s in scores.items()]
    for condition,models in slices.items():
        lines += ['',f'## {condition}','','| Model | Rows | Races | Pooled MAE | Equal-race MAE |','|---|---:|---:|---:|---:|']
        lines += [f"| {n} | {s['rows']} | {s['races']} | {s.get('mae_s',0):.4f} | {s.get('race_macro_mae_s',0):.4f} |" if s['rows'] else f'| {n} | 0 | 0 | N/A | N/A |' for n,s in models.items()]
    lines += ['',result['limitations'],'','Per-race metrics, exploratory paired race-bootstrap intervals, excluded races and row-level predictions are saved alongside this report.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    verify(robust,list(frozen))
    save_json(out/'artifact_hashes.json',{p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    print(json.dumps({'coverage':data['coverage'],'mae':{n:s['race_macro_mae_s'] for n,s in scores.items()}},indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ['dataset','source-root','robust-run','original-evaluation','output']:parser.add_argument('--'+arg,required=True)
    parser.add_argument('--evaluate-2026',required=True,action='store_true')
    parser.add_argument('--skill-tools');a=parser.parse_args();torch.set_num_threads(1)
    with threadpool_limits(limits=1):run(a.dataset,a.source_root,a.robust_run,a.original_evaluation,a.output,a.skill_tools)

if __name__=='__main__':main()
