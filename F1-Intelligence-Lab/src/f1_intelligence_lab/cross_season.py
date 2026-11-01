"""Explicit opt-in, frozen-artifact 2026 evaluation. No fitting or selection."""
import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch
from threadpoolctl import threadpool_limits

from .dl_train import PROTOCOL, predict_bundle, score
from .ml_prep import digest
from .ml_sequences import build_split, flattened
from .ml_train import baseline, save_json

NAMES=['last_lap','rolling_mean','rolling_median','boosting_13','boosting_sequence',
       'gru_full','gru_no_tyre','gru_no_control']


def verify_artifacts(run):
    run=Path(run)
    hashes=json.loads((run/'artifact_hashes.json').read_text())
    required=['results.json','protocol.json','selection.json','boosting_13.joblib','boosting_sequence.joblib']
    for variant in PROTOCOL['variants']:
        for seed in PROTOCOL['seeds']:
            stem=f'gru_{variant}_{seed}'
            required.extend([stem+'.pt',stem+'.json',stem+'_encoders.joblib'])
    for name in required:
        if hashes.get(name)!=digest((run/name).read_bytes()):
            raise ValueError('Frozen artifact checksum mismatch: '+name)
    old=json.loads((run/'results.json').read_text())
    if old['protocol']!=PROTOCOL or old['environment']['torch']!=torch.__version__:
        raise ValueError('Frozen architecture or runtime differs')
    return old,{n:hashes[n] for n in required}


def paired_race_interval(model,reference):
    """Paired race-level bootstrap; descriptive uncertainty, not lap-level IID."""
    keys=sorted(model['per_race'])
    differences=np.array([model['per_race'][k]['mae_s']-reference['per_race'][k]['mae_s'] for k in keys])
    rng=np.random.default_rng(20261028)
    means=rng.choice(differences,size=(10000,len(keys)),replace=True).mean(axis=1)
    return {'mean_delta_s':float(differences.mean()),'ci95_s':np.quantile(means,[.025,.975]).tolist(),
            'races_better':int((differences<0).sum()),'races':len(keys),
            'method':'10,000 paired race-bootstrap resamples; exploratory, assumes exchangeable races; negative favours model'}


def run(dataset,source_root,frozen_run,output,skill_tools=None):
    frozen_run=Path(frozen_run); out=Path(output)
    old,hashes=verify_artifacts(frozen_run)
    manifest_hash=digest((Path(dataset)/'manifest.json').read_bytes())
    if old['original_manifest_sha256']!=manifest_hash:
        raise ValueError('Audited dataset manifest changed')
    out.mkdir(parents=True,exist_ok=False)
    protocol={'created_utc':datetime.now(timezone.utc).isoformat(),
        'authorization':'User explicitly requested evaluation of 2026 races on 28 October 2026',
        'primary':'race_macro_mae_s','models':NAMES,'selected_before_2026':old['winner'],
        'policy':'No fitting, tuning, checkpoint changes, reselection or automatic promotion. All eligible audited 2026 races.',
        'coverage':'Frozen audit snapshot, not every scheduled 2026 race; require 10 completed contiguous history laps.',
        'uncertainty':'10,000 paired race bootstrap resamples, seed 20261028; no lap-IID inference',
        'artifact_hashes':hashes,'dataset_manifest_sha256':manifest_hash,
        'evaluation_code_sha256':digest(Path(__file__).read_bytes())}
    # Persist commitment before reading any future-holdout CSV or raw race cache.
    save_json(out/'protocol.json',protocol)
    data=build_split(dataset,source_root,'future_holdout',allow_future_evaluation=True)
    values={}; scores={}; seeds={}
    for name in NAMES:
        if name.startswith('gru_'):
            variant=name[4:]
            predictions=[predict_bundle(frozen_run,variant,s,data) for s in PROTOCOL['seeds']]
            seeds[name]=[{'seed':s,'scores':score(data,p)} for s,p in zip(PROTOCOL['seeds'],predictions)]
            p=np.mean(predictions,axis=0)
        elif name.startswith('boosting'):
            model=joblib.load(frozen_run/(name+'.joblib'))
            p=baseline('last_lap',data['x'])+model.predict(flattened(data) if name=='boosting_sequence' else data['x'])
        else:
            p=baseline(name,data['x'])
        values[name]=p; scores[name]=score(data,p)
        print(name,scores[name]['race_macro_mae_s'],flush=True)
    audit=json.loads((Path(dataset)/'audit.json').read_text())
    races={m['session_id']:{'session_id':m['session_id'],'race_start':m['race_start'],'circuit':x['circuit']}
           for m,x in zip(data['meta'],data['x'])}
    excluded=[{'session_id':r['session_id'],'blockers':r.get('blockers',[])} for r in audit['session_reports']
              if r['split']=='future_holdout' and not r['verified_for_prep']]
    result={'protocol':protocol,'coverage':data['coverage'],'races':sorted(races.values(),key=lambda r:r['race_start']),
        'excluded_races':excluded,'scores':scores,'seeds':seeds,'selected_before_2026':old['winner'],
        'paired_vs_last_lap':{n:paired_race_interval(s,scores['last_lap']) for n,s in scores.items() if n!='last_lap'},
        'previous_benchmark_scores':old['scores']['test'],'sources':data['sources'],
        'holdout_status':'2026 now evaluated; no longer untouched for subsequent tuning',
        'limitations':'Historical event-time reconstruction, not live availability. Eligibility and circuit mix differ across years; differences are not isolated concept drift.'}
    with (out/'predictions.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['row_id','session_id','driver','lap','actual_s']+NAMES); w.writeheader()
        for i,(m,x,y) in enumerate(zip(data['meta'],data['x'],data['y'])):
            w.writerow(dict(row_id=m['row_id'],session_id=m['session_id'],driver=m['driver_number'],lap=int(x['lap_number']),actual_s=y,
                            **{n:float(values[n][i]) for n in NAMES}))
    save_json(out/'results.json',result)
    if skill_tools:
        for name,s in scores.items():
            subprocess.run([sys.executable,str(Path(skill_tools)/'experiment_tracker.py'),'--log-file',str(out/'experiments.json'),
                'log','--name','2026_frozen_'+name,'--params',json.dumps({'selected_before_2026':old['winner'],'fit':False}),
                '--metrics',json.dumps({k:v for k,v in s.items() if isinstance(v,(int,float))}),
                '--tags','2026,frozen,evaluation','--notes','Lower error is better. No model selection on 2026.'],check=True,capture_output=True)
    lines=['# Frozen 2026 cross-season evaluation','',f"Previously selected model: **{old['winner']}**. No retraining or reselection.",
           '',json.dumps(data['coverage'],indent=2),'','| Model | Race MAE (s) | Pooled RMSE (s) | Pooled R² |','|---|---:|---:|---:|']
    lines += [f"| {n} | {s['race_macro_mae_s']:.4f} | {s['rmse_s']:.4f} | {s['r2']:.4f} |" for n,s in scores.items()]
    lines += ['',result['holdout_status'],result['limitations'],'',
              'Excluded unverified races: '+json.dumps(excluded),
              'Per-race metrics, condition slices and paired race-bootstrap intervals are in results.json. All models share identical eligible targets.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    save_json(out/'artifact_hashes.json',{p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['dataset','source-root','frozen-run','output']: p.add_argument('--'+arg,required=True)
    p.add_argument('--evaluate-2026',action='store_true',required=True)
    p.add_argument('--skill-tools'); a=p.parse_args(); torch.set_num_threads(1)
    with threadpool_limits(limits=1): run(a.dataset,a.source_root,a.frozen_run,a.output,a.skill_tools)


if __name__=='__main__': main()
