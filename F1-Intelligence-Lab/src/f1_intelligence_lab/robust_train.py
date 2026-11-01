"""2025-only restart-aware next-lap experiments; original elapsed-time labels retained."""
import argparse
import copy
import csv
import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits
from .dl_train import train_gru, infer_gru, encode, predict_bundle, race_weights, subset
from .ml_sequences import build_split, flattened
from .ml_train import baseline, evaluate, expanding_folds, save_json
from .ml_prep import digest

PLAN={'version':1,'years':[2025],'ratios':[1.5,2.0,3.0],'leaves':[7,15],
      'primary':'race_macro_mae_s','seeds':[11,29,47],
      'selection':'2025 validation only, tree representation chosen first; full three-seed GRU then compared',
      'label_policy':'Keep all original elapsed-lap targets, including long laps. No target clipping or filtering.',
      '2026':'Not loaded or scored. Previously seen failures motivate design; no independent generalization claim.',
      'stress':'Diagnostic synthetic last-history-lap interruption at 10x prior time; targets unchanged; not real race accuracy.',
      'benchmark':'2025 test is reused and not pristine; opened after selection only.'}


def transform(data,ratio):
    """Only historical inputs used. Replace extreme pace values, retain event indicators."""
    if ratio not in PLAN['ratios']: raise ValueError('Unregistered outlier ratio')
    out={**data,'x':[],'sequences':[]}; flags=[]
    for x,seq in zip(data['x'],data['sequences']):
        times=np.array([s['pace_delta_s']+x['lag_1_s'] for s in seq],dtype=float)
        if len(times)!=10 or not np.isfinite(times).all() or (times<=0).any():
            raise ValueError('Invalid completed-lap history')
        # Lower-half median tolerates several consecutive interruptions. It is
        # a historical reference, not a label-derived clean-pace classification.
        reference=float(np.median(np.sort(times)[:5]))
        unusual=times>ratio*reference
        normal=times[~unusual]
        anchor=float(normal[-1]) if len(normal) else reference
        clean=np.where(unusual,reference,times)
        z=dict(x)
        z.update(lag_1_s=anchor,lag_2_s=float(clean[-2]),lag_3_s=float(clean[-3]),
                 rolling_mean_3_s=float(clean[-3:].mean()),rolling_std_3_s=float(clean[-3:].std()),
                 recent_change_s=float(clean[-1]-clean[-2]),history_reference_s=reference,
                 long_history_count=int(unusual.sum()),previous_long_lap=int(unusual[-1]),
                 laps_since_long=next((i for i,v in enumerate(unusual[::-1]) if v),10),
                 prior_duration_log_ratio=float(np.log1p(min(times[-1]/reference,10))),
                 restart_state_transition=int((seq[-1]['control_state'] in {'RED','SC','VSC','RESTART'} and x['control_state_at_cutoff']=='GREEN') or seq[-1].get('cutoff_restart_count',0)>seq[-1].get('restart_count',0)))
        steps=[]
        for i,s in enumerate(seq):
            step=dict(s,pace_delta_s=float(np.clip(clean[i]-anchor,-reference*.5,reference*.5)),
                      long_lap=int(unusual[i]),duration_log_ratio=float(np.log1p(min(times[i]/reference,10))),
                      restart_transition=int(i>0 and ((seq[i-1]['control_state'] in {'RED','SC','VSC','RESTART'} and s['control_state']=='GREEN') or s.get('restart_count',0)>seq[i-1].get('restart_count',0))))
            steps.append(step)
        out['x'].append(z);out['sequences'].append(steps);flags.append(bool(unusual[-1]))
    out['previous_long']=flags
    return out


def anchor(data): return np.array([x['lag_1_s'] for x in data['x']])


def only_2025(data):
    ix=[i for i,m in enumerate(data['meta']) if m['race_start'].startswith('2025')]
    if not ix:raise ValueError('No 2025 examples')
    return {**data,**subset(data,ix),'coverage':{'eligible_rows':len(ix),
        'races':len({data['meta'][i]['session_id'] for i in ix}),
        'older_year_rows_excluded':len(data['x'])-len(ix)}}


def neural_view(data):
    # Existing GRU training uses a strict 13-feature baseline helper. Keep new
    # context fields in sequence steps so it can retain its unchanged contract.
    from .ml_prep import FEATURES
    result={**data,'x':[{k:x[k] for k in FEATURES} for x in data['x']], 'sequences':[]}
    for x,seq in zip(data['x'],data['sequences']):
        extra={k:v for k,v in x.items() if k not in FEATURES}
        result['sequences'].append([dict(s,**extra) for s in seq])
    return result


def assess(raw,p,flags=None):
    result=evaluate(raw['y'],p,raw['meta'],raw['x'])
    if flags is not None:
        ix=np.flatnonzero(flags)
        result['after_long_history']={'rows':len(ix),'mae_s':float(np.mean(np.abs(np.asarray(raw['y'])[ix]-np.asarray(p)[ix])))} if len(ix) else {'rows':0}
    return result


def tree_fit(data,leaves):
    model=make_pipeline(DictVectorizer(sparse=False),HistGradientBoostingRegressor(loss='absolute_error',
        max_iter=150,max_leaf_nodes=leaves,learning_rate=.05,min_samples_leaf=30,l2_regularization=1.,early_stopping=False,random_state=42))
    model.fit(flattened(data),np.asarray(data['y'])-anchor(data),histgradientboostingregressor__sample_weight=race_weights(data['meta']))
    return model


def interrupted(data):
    result=copy.deepcopy(data)
    for x,seq in zip(result['x'],result['sequences']):
        old=x['lag_1_s']; durations=[s['pace_delta_s']+old for s in seq];durations[-1]=old*10
        x['lag_1_s']=durations[-1]
        x['rolling_mean_3_s']=float(np.mean(durations[-3:]));x['rolling_std_3_s']=float(np.std(durations[-3:]));x['recent_change_s']=durations[-1]-durations[-2]
        for s,t in zip(seq,durations): s['pace_delta_s']=t-x['lag_1_s']
    return result


def predict_saved(directory,data,model_name='robust_gru'):
    """Inference for explicit experimental model choice; trusted local artifacts only."""
    directory=Path(directory);hashes=json.loads((directory/'artifact_hashes.json').read_text())
    def checked(name):
        if name not in hashes or digest((directory/name).read_bytes())!=hashes[name]:
            raise ValueError('Robust model integrity failure')
    checked('selection.json');selection=json.loads((directory/'selection.json').read_text())
    if model_name=='robust_tree':
        name=selection['tree_candidate'];checked(name+'.joblib')
        transformed=transform(data,selection['ratio'])
        return anchor(transformed)+joblib.load(directory/(name+'.joblib')).predict(flattened(transformed))
    if model_name!='robust_gru':raise ValueError('Choose robust_tree or robust_gru')
    for seed in PLAN['seeds']:
        for suffix in ['.pt','.json','_encoders.joblib']:checked(f'gru_full_{seed}'+suffix)
    transformed=neural_view(transform(data,selection['ratio']))
    return np.mean([predict_bundle(directory,'full',s,transformed) for s in PLAN['seeds']],axis=0)


def run(dataset,source_root,frozen_run,output,skill_tools=None,control_version=1):
    plan=dict(PLAN,control_version=control_version)
    out=Path(output);out.mkdir(parents=True,exist_ok=False);save_json(out/'protocol.json',plan)
    data={s:only_2025(build_split(dataset,source_root,s,control_version=control_version)) for s in ['train','validation']}
    if any(not m['race_start'].startswith('2025') for d in data.values() for m in d['meta']):
        raise ValueError('Only 2025 data allowed')
    frozen=Path(frozen_run); hashes=json.loads((frozen/'artifact_hashes.json').read_text())
    for name in ['boosting_sequence.joblib','results.json']:
        if digest((frozen/name).read_bytes())!=hashes[name]:raise ValueError('Original model hash mismatch')
    # Retrain the unchanged architecture on exactly the same 2025-only cohort.
    old_tree=tree_fit(data['train'],15)
    joblib.dump(old_tree,out/'unmodified_sequence_boosting.joblib')
    scores={'train':{},'validation':{}};candidates={}
    for ratio in PLAN['ratios']:
        t=transform(data['train'],ratio);v=transform(data['validation'],ratio)
        for leaves in PLAN['leaves']:
            name=f'robust_tree_r{ratio}_l{leaves}';model=tree_fit(t,leaves);candidates[name]=(ratio,model)
            joblib.dump(model,out/(name+'.joblib'))
            for split,d in [('train',t),('validation',v)]:
                scores[split][name]=assess(data[split],anchor(d)+model.predict(flattened(d)),d['previous_long'])
            print(name,scores['validation'][name]['race_macro_mae_s'],flush=True)
    chosen=min(candidates,key=lambda n:scores['validation'][n]['race_macro_mae_s'])
    ratio,tree=candidates[chosen]; seeds=[];gru_preds={'train':[],'validation':[]}
    converted={s:neural_view(transform(d,ratio)) for s,d in data.items()}
    for seed in PLAN['seeds']:
        model,enc,info=train_gru(converted['train'],converted['validation'],'full',seed)
        stem=f'gru_full_{seed}';torch.save(model.state_dict(),out/(stem+'.pt'));joblib.dump(enc,out/(stem+'_encoders.joblib'));save_json(out/(stem+'.json'),info)
        for split,d in converted.items():
            p=infer_gru(model,encode(d,'full',enc),d);gru_preds[split].append(p)
            np.testing.assert_array_equal(p,predict_bundle(out,'full',seed,d))
        seeds.append({'seed':seed,'validation':assess(data['validation'],gru_preds['validation'][-1]),'best_epoch':info['best_epoch']})
    for split,raw in data.items():
        for name in ['last_lap','rolling_median']:
            scores[split][name]=assess(raw,baseline(name,raw['x']))
        scores[split]['unmodified_sequence_boosting']=assess(raw,baseline('last_lap',raw['x'])+old_tree.predict(flattened(raw)))
        scores[split]['robust_gru']=assess(raw,np.mean(gru_preds[split],axis=0),transform(raw,ratio)['previous_long'])
    winner=min(scores['validation'],key=lambda n:scores['validation'][n]['race_macro_mae_s'])
    save_json(out/'selection.json',{'winner':winner,'tree_candidate':chosen,'ratio':ratio,'validation':scores['validation']})
    # Development-only forward validation, no 2026 access. Already tuned on
    # later 2025 validation: descriptive stability check, not outer CV.
    cv=[]
    leaves=int(chosen.rsplit('l',1)[1])
    for ix,jx in expanding_folds(data['train']['meta']):
        a,b=subset(data['train'],ix),subset(data['train'],jx);ta,tb=transform(a,ratio),transform(b,ratio)
        m=tree_fit(ta,leaves)
        cv.append({'robust':assess(b,anchor(tb)+m.predict(flattened(tb))),
                   'median':assess(b,baseline('rolling_median',b['x']))})
    data['test']=build_split(dataset,source_root,'test',control_version=control_version)
    if any(not m['race_start'].startswith('2025') for m in data['test']['meta']):raise ValueError('2025 only')
    raw=data['test'];d=transform(raw,ratio);nd=neural_view(d)
    predictions={n:baseline(n,raw['x']) for n in ['last_lap','rolling_median']}
    predictions['unmodified_sequence_boosting']=baseline('last_lap',raw['x'])+old_tree.predict(flattened(raw))
    for name,(r,m) in candidates.items():
        transformed=transform(raw,r);predictions[name]=anchor(transformed)+m.predict(flattened(transformed))
    predictions['robust_gru']=np.mean([predict_bundle(out,'full',s,nd) for s in PLAN['seeds']],axis=0)
    scores['test']={n:assess(raw,p,d['previous_long']) for n,p in predictions.items()}
    stress=interrupted(data['validation']);sd=transform(stress,ratio);sn=neural_view(sd)
    stress_predictions={'unmodified_sequence_boosting':baseline('last_lap',stress['x'])+old_tree.predict(flattened(stress)),
        'rolling_median':baseline('rolling_median',stress['x']),chosen:anchor(sd)+tree.predict(flattened(sd)),
        'robust_gru':np.mean([predict_bundle(out,'full',s,sn) for s in PLAN['seeds']],axis=0)}
    with (out/'predictions.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['row_id','actual_s']+list(predictions));w.writeheader()
        for i,m in enumerate(raw['meta']):w.writerow(dict(row_id=m['row_id'],actual_s=raw['y'][i],**{n:float(p[i]) for n,p in predictions.items()}))
    features=flattened(transform(data['train'],ratio))
    with (out/'training_features_only.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(features[0])+['target_lap_time_s']);w.writeheader()
        w.writerows(dict(x,target_lap_time_s=y) for x,y in zip(features,data['train']['y']))
    if skill_tools:
        ranking=subprocess.check_output([sys.executable,str(Path(skill_tools)/'feature_selector.py'),'--file',str(out/'training_features_only.csv'),'--target','target_lap_time_s','--json'],text=True)
        save_json(out/'feature_ranking.json',json.loads(ranking))
        for name,s in scores['validation'].items():
            subprocess.run([sys.executable,str(Path(skill_tools)/'experiment_tracker.py'),'--log-file',str(out/'experiments.json'),'log','--name',name,
                '--params',json.dumps(PLAN),'--metrics',json.dumps({k:v for k,v in s.items() if isinstance(v,(int,float))}),
                '--notes','2025 development only; lower error better; all predeclared features retained.'],check=True,capture_output=True)
    result={'protocol':plan,'winner':winner,'tree_candidate':chosen,'ratio':ratio,'scores':scores,'seeds':seeds,
        'forward_validation':cv,'stress':{n:assess(stress,p) for n,p in stress_predictions.items()},
        'coverage':{s:d['coverage'] for s,d in data.items()},'sources':{u:h for d in data.values() for u,h in d['sources'].items()},
        'source_code_sha256':digest(Path(__file__).read_bytes()),'original_model_sha256':hashes['boosting_sequence.joblib'],
        'feature_selection':'Training-only ranking descriptive; all predeclared features retained; no 2026 read.',
        'limitations':'Restart inputs use known historical events only. Future interruptions are not predictable. Synthetic stress is not real-race accuracy. No promotion or 2026 retest.'}
    save_json(out/'results.json',result)
    save_json(out/'artifact_hashes.json',{p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    print('SELECTED',winner,flush=True);return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ['dataset','source-root','frozen-run','output']:parser.add_argument('--'+arg,required=True)
    parser.add_argument('--control-version',type=int,choices=[1,2],default=1)
    parser.add_argument('--skill-tools');a=parser.parse_args();torch.set_num_threads(1)
    with threadpool_limits(limits=1):run(a.dataset,a.source_root,a.frozen_run,a.output,a.skill_tools,a.control_version)

if __name__=='__main__':main()
