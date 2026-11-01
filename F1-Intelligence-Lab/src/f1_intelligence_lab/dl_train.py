"""Fixed, multi-seed GRU versus boosting experiment on matched 10-lap histories."""
import argparse
import copy
import csv
import json
import platform
import random
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from torch import nn

from .ml_prep import digest
from .ml_sequences import WINDOW, ablate, build_split, flattened
from .ml_train import CONFIG as TREE_CONFIG
from .ml_train import baseline, evaluate, expanding_folds, save_json

PROTOCOL = {
    'version':1,'window':WINDOW,'seeds':[11,29,47],'variants':['full','no_tyre','no_control'],
    'primary':'race_macro_mae_s','hidden_size':24,'context_hidden':16,'head_hidden':32,
    'epochs':30,'patience':5,'batch_size':256,'learning_rate':0.001,'weight_decay':0.0001,
    'loss':'race-weighted absolute error in seconds','gradient_clip':1.0,'device':'cpu',
    'selection':'validation only; full GRU ensemble versus baselines and fixed boosting models; ablations diagnostic only',
    'gru_ensemble':'arithmetic mean of the three seeds; no best-seed cherry-picking',
    'test_status':'2025 test already inspected in previous project experiment; reused benchmark, NOT pristine holdout',
    'future_holdout':'2026 not read; requires separately frozen cross-season evaluation',
    'tree_config':TREE_CONFIG['hist_absolute'], 'label_trimming':'none',
    'training_cv':'three expanding training-race folds; full GRU seed 11 versus last-lap, checkpoint selection within each fold',
}


class LapGRU(nn.Module):
    def __init__(self, sequence_features, context_features):
        super().__init__()
        self.gru=nn.GRU(sequence_features,PROTOCOL['hidden_size'],batch_first=True)
        self.context=nn.Sequential(nn.Linear(context_features,PROTOCOL['context_hidden']),nn.ReLU())
        self.head=nn.Sequential(nn.Linear(PROTOCOL['hidden_size']+PROTOCOL['context_hidden'],PROTOCOL['head_hidden']),
                                nn.ReLU(),nn.Linear(PROTOCOL['head_hidden'],1))
        nn.init.zeros_(self.head[-1].weight); nn.init.zeros_(self.head[-1].bias)

    def forward(self, sequence, context):
        _,hidden=self.gru(sequence)
        return self.head(torch.cat([hidden[-1],self.context(context)],dim=1)).squeeze(-1)


def encode(data, variant, encoders=None):
    steps=[ablate(step,variant) for sequence in data['sequences'] for step in sequence]
    contexts=[ablate(x,variant) for x in data['x']]
    if encoders is None:
        encoders=(make_pipeline(DictVectorizer(sparse=False),StandardScaler()),
                  make_pipeline(DictVectorizer(sparse=False),StandardScaler()))
        seq=encoders[0].fit_transform(steps)
        ctx=encoders[1].fit_transform(contexts)
    else:
        seq=encoders[0].transform(steps); ctx=encoders[1].transform(contexts)
    seq=seq.reshape(len(contexts),WINDOW,-1).astype('float32'); ctx=ctx.astype('float32')
    if not np.isfinite(seq).all() or not np.isfinite(ctx).all():
        raise ValueError('Nonfinite encoded features')
    return torch.from_numpy(seq),torch.from_numpy(ctx),encoders


def score(data, values):
    return evaluate(data['y'],values,data['meta'],data['x'])


def race_weights(metadata):
    counts=Counter(m['session_id'] for m in metadata)
    return np.array([len(metadata)/(len(counts)*counts[m['session_id']]) for m in metadata],dtype='float32')


def infer_gru(model, encoded, data):
    model.eval()
    with torch.no_grad():
        values=model(encoded[0],encoded[1]).numpy().astype('float64')+baseline('last_lap',data['x'])
    if not np.isfinite(values).all(): raise ValueError('Invalid model output')
    return values


def train_gru(train,val,variant,seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    seq,ctx,encoders=encode(train,variant)
    vseq,vctx,_=encode(val,variant,encoders)
    model=LapGRU(seq.shape[-1],ctx.shape[-1])
    optimizer=torch.optim.AdamW(model.parameters(),lr=PROTOCOL['learning_rate'],weight_decay=PROTOCOL['weight_decay'])
    target=torch.tensor(np.asarray(train['y'])-baseline('last_lap',train['x']),dtype=torch.float32)
    weights=torch.from_numpy(race_weights(train['meta']))
    best=float('inf'); best_state=None; best_epoch=0; history=[]; stale=0
    for epoch in range(1,PROTOCOL['epochs']+1):
        model.train(); order=torch.randperm(len(target)); loss_sum=0.
        for ix in order.split(PROTOCOL['batch_size']):
            optimizer.zero_grad()
            loss=(torch.abs(model(seq[ix],ctx[ix])-target[ix])*weights[ix]).mean()
            if not torch.isfinite(loss): raise ValueError('Nonfinite loss')
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),PROTOCOL['gradient_clip']); optimizer.step()
            loss_sum+=float(loss.detach())*len(ix)
        val_mae=score(val,infer_gru(model,(vseq,vctx),val))['race_macro_mae_s']
        history.append({'epoch':epoch,'weighted_train_loss':loss_sum/len(target),'validation_race_mae_s':val_mae})
        if val_mae<best-1e-6:
            best=val_mae; best_state=copy.deepcopy(model.state_dict()); best_epoch=epoch; stale=0
        else: stale+=1
        if stale>=PROTOCOL['patience']: break
    model.load_state_dict(best_state)
    return model,encoders,{'seed':seed,'best_epoch':best_epoch,'history':history,
        'parameter_count':sum(p.numel() for p in model.parameters()),
        'input_dims':[seq.shape[-1],ctx.shape[-1]]}


def subset(data,indices):
    return {k:[data[k][i] for i in indices] for k in ['x','y','meta','sequences']}


def predict_bundle(directory,variant,seed,data):
    """Reload only trusted local artifacts. torch weights loaded in restricted mode."""
    directory=Path(directory); stem=f'gru_{variant}_{seed}'
    info=json.loads((directory/(stem+'.json')).read_text())
    model=LapGRU(*info['input_dims'])
    model.load_state_dict(torch.load(directory/(stem+'.pt'),map_location='cpu',weights_only=True))
    encoders=joblib.load(directory/(stem+'_encoders.joblib'))
    seq,ctx,_=encode(data,variant,encoders)
    return infer_gru(model,(seq,ctx),data)


def run(dataset,source_root,output,skill_tools=None):
    started=time.perf_counter(); out=Path(output); out.mkdir(parents=True,exist_ok=False)
    save_json(out/'protocol.json',PROTOCOL)
    train=build_split(dataset,source_root,'train'); val=build_split(dataset,source_root,'validation')
    save_json(out/'development_coverage.json',{s:d['coverage'] for s,d in [('train',train),('validation',val)]})
    print('COVERAGE',train['coverage'],val['coverage'],flush=True)
    flat=flattened(train)
    with (out/'training_features_only.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0])+['target_lap_time_s']); writer.writeheader()
        writer.writerows(dict(r,target_lap_time_s=y) for r,y in zip(flat,train['y']))
    if skill_tools:
        ranking=subprocess.check_output([sys.executable,str(Path(skill_tools)/'feature_selector.py'),
            '--file',str(out/'training_features_only.csv'),'--target','target_lap_time_s','--json'],text=True)
        save_json(out/'feature_ranking.json',json.loads(ranking))
    save_json(out/'feature_selection.json',{'decision':'All prespecified features retained; ablations remove tyre or control from BOTH sequence and context.',
        'fit_split':'train','sequence_fields':list(train['sequences'][0][0]),'context_fields':list(train['x'][0]),
        'ranking_scope':'training-only descriptive ranking, not causal importance'})
    models={}; scores={'train':{},'validation':{},'test':{}}; pred_val={}; diagnostics={}; records=[]
    for name in ['last_lap','rolling_mean','rolling_median','boosting_13','boosting_sequence']:
        if name.startswith('boosting'):
            inputs=flat if name=='boosting_sequence' else train['x']
            model=make_pipeline(DictVectorizer(sparse=False),HistGradientBoostingRegressor(**TREE_CONFIG['hist_absolute']))
            model.fit(inputs,np.asarray(train['y'])-baseline('last_lap',train['x']),
                      histgradientboostingregressor__sample_weight=race_weights(train['meta']))
            models[name]=model; joblib.dump(model,out/(name+'.joblib'))
        for split,data in [('train',train),('validation',val)]:
            p=(baseline('last_lap',data['x'])+models[name].predict(flattened(data) if name=='boosting_sequence' else data['x'])) if name.startswith('boosting') else baseline(name,data['x'])
            scores[split][name]=score(data,p)
            if split=='validation': pred_val[name]=p
        print(name,'validation',scores['validation'][name]['race_macro_mae_s'],flush=True)
    for variant in PROTOCOL['variants']:
        seeds=[]; train_predictions=[]; val_predictions=[]
        for seed in PROTOCOL['seeds']:
            model,encoders,info=train_gru(train,val,variant,seed)
            stem=f'gru_{variant}_{seed}'
            torch.save(model.state_dict(),out/(stem+'.pt')); joblib.dump(encoders,out/(stem+'_encoders.joblib')); save_json(out/(stem+'.json'),info)
            tp=infer_gru(model,encode(train,variant,encoders),train); vp=infer_gru(model,encode(val,variant,encoders),val)
            np.testing.assert_array_equal(vp,predict_bundle(out,variant,seed,val))
            seeds.append({'seed':seed,'train':score(train,tp),'validation':score(val,vp),'best_epoch':info['best_epoch']})
            train_predictions.append(tp); val_predictions.append(vp)
            records.append((stem,seeds[-1]['validation']))
            print(stem,'epoch',info['best_epoch'],'validation',seeds[-1]['validation']['race_macro_mae_s'],flush=True)
        name='gru_'+variant; diagnostics[name]=seeds
        scores['train'][name]=score(train,np.mean(train_predictions,axis=0))
        pred_val[name]=np.mean(val_predictions,axis=0)
        scores['validation'][name]=score(val,pred_val[name])
    # Training-only forward folds are diagnostics, not additional architecture search.
    cv=[]
    for i,(ix,jx) in enumerate(expanding_folds(train['meta'])):
        a,b=subset(train,ix),subset(train,jx)
        model,encoders,info=train_gru(a,b,'full',PROTOCOL['seeds'][0])
        cv.append({'fold':i+1,'gru':score(b,infer_gru(model,encode(b,'full',encoders),b)),
                   'last_lap':score(b,baseline('last_lap',b['x'])),'best_epoch':info['best_epoch'],
                   'note':'fold evaluation also selects checkpoint; diagnostic validation, not unbiased outer CV'})
        print('training forward fold',i+1,'finished',flush=True)
    candidates=['last_lap','rolling_mean','rolling_median','boosting_13','boosting_sequence','gru_full']
    winner=min(candidates,key=lambda n:scores['validation'][n]['race_macro_mae_s'])
    save_json(out/'selection.json',{'winner':winner,'candidates':candidates,'validation':scores['validation'],
              'selected_at_utc':datetime.now(timezone.utc).isoformat(),'test_status':PROTOCOL['test_status']})
    # No test feature/label read before every architecture, seed and checkpoint is frozen.
    test=build_split(dataset,source_root,'test')
    predictions={}
    for name in scores['validation']:
        if name.startswith('gru_'):
            variant=name[4:]
            seed_predictions=[predict_bundle(out,variant,s,test) for s in PROTOCOL['seeds']]
            for record,p in zip(diagnostics[name],seed_predictions): record['test']=score(test,p)
            p=np.mean(seed_predictions,axis=0)
        elif name.startswith('boosting'):
            p=baseline('last_lap',test['x'])+models[name].predict(flattened(test) if name=='boosting_sequence' else test['x'])
        else: p=baseline(name,test['x'])
        scores['test'][name]=score(test,p); predictions[name]=p
    with (out/'benchmark_predictions.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['row_id','session_id','driver','lap','actual_s']+list(predictions)); writer.writeheader()
        for i,(m,x,y) in enumerate(zip(test['meta'],test['x'],test['y'])):
            writer.writerow(dict(row_id=m['row_id'],session_id=m['session_id'],driver=m['driver_number'],lap=int(x['lap_number']),actual_s=y,
                                  **{name:float(p[i]) for name,p in predictions.items()}))
    for name,s in scores['validation'].items(): records.append((name,s))
    if skill_tools:
        for name,s in records:
            subprocess.run([sys.executable,str(Path(skill_tools)/'experiment_tracker.py'),'--log-file',str(out/'experiments.json'),
                'log','--name',name,'--params',json.dumps(PROTOCOL),'--metrics',json.dumps({k:v for k,v in s.items() if isinstance(v,(int,float))}),
                '--tags','sequence,validation','--notes','Lower errors are better. Historical test is reused; 2026 reserved.'],check=True,capture_output=True)
    result={'protocol':PROTOCOL,'winner':winner,'coverage':{s:d['coverage'] for s,d in [('train',train),('validation',val),('test',test)]},
        'scores':scores,'seeds':diagnostics,'training_forward_validation':cv,
        'sources':{**train['sources'],**val['sources'],**test['sources']},
        'original_manifest_sha256':digest((Path(dataset)/'manifest.json').read_bytes()),
        'source_code_sha256':{n:digest((Path(__file__).parent/n).read_bytes()) for n in ['dl_train.py','ml_sequences.py']},
        'environment':{'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__},
        'elapsed_s':time.perf_counter()-started,'created_utc':datetime.now(timezone.utc).isoformat()}
    save_json(out/'results.json',result)
    lines=['# Matched-cohort ML / DL experiment','',f'Validation-selected winner: **{winner}**.',
        '', '**2025 test is a reused benchmark, not a pristine holdout. 2026 was not read.**','',
        '| Model | Train race MAE | Validation race MAE | Benchmark race MAE | Benchmark RMSE | Benchmark R² |',
        '|---|---:|---:|---:|---:|---:|']
    for name in scores['validation']:
        t=scores['test'][name]
        vals=[scores['train'][name]['race_macro_mae_s'],scores['validation'][name]['race_macro_mae_s'],t['race_macro_mae_s'],t['rmse_s'],t['r2']]
        lines.append('| '+name+' | '+' | '.join(f'{v:.4f}' for v in vals)+' |')
    lines+=['','## Coverage','',json.dumps(result['coverage'],indent=2),'',
        'All models use the same eligible targets and training rows. GRU entries average predictions from all three seeds; no best-seed selection.',
        'Ablations remove tyre or control inputs from both context and sequences. Their differences are diagnostic, not causal attribution.',
        'Early stopping uses validation races. Training-only forward folds also select checkpoints on their validation blocks, so are not unbiased outer-CV estimates.',
        'Long laps retained. No confidence interval is inferred from lap counts. Historical corrected event time is not certified live availability.',
        'Checkpoints, encoders, per-epoch losses, seed metrics, source hashes and row-level benchmark predictions are saved locally. No website model is automatically replaced.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    save_json(out/'artifact_hashes.json',{p.name:digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',required=True); parser.add_argument('--source-root',required=True)
    parser.add_argument('--output',required=True); parser.add_argument('--skill-tools')
    args=parser.parse_args(); torch.set_num_threads(1)
    with threadpool_limits(limits=1):
        result=run(args.dataset,args.source_root,args.output,args.skill_tools)
    print('WINNER',result['winner'],flush=True)


if __name__=='__main__': main()
