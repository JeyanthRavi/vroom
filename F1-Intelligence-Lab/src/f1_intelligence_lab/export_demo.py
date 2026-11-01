"""Export checksum-verified historical predictions, never weights or source caches."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import torch
from threadpoolctl import threadpool_limits
from .ml_sequences import build_split,flattened
from .ml_train import baseline,save_json
from .ml_prep import digest
from .robust_train import only_2025,predict_saved
from .restart_evaluate import verify

def run(dataset,source,training,evaluation,output):
    train=Path(training);ev=Path(evaluation);out=Path(output)
    verify(train,list(json.loads((train/'artifact_hashes.json').read_text())))
    verify(ev,['results.json'])
    result=json.loads((train/'results.json').read_text());regression=json.loads((ev/'results.json').read_text())
    selected=result['winner'];tree=result['tree_candidate']
    validation=result['scores']['validation']
    if validation[selected]['race_macro_mae_s']>validation['rolling_median']['race_macro_mae_s']:
        raise ValueError('2025 validation gate failed: selected model worse than median')
    if regression['protocol']['model_artifact_hashes']['results.json']!=digest((train/'results.json').read_bytes()):
        raise ValueError('Evaluation belongs to a different model run')
    choice='restart_boosting' if selected==tree else {'robust_gru':'restart_gru','unmodified_sequence_boosting':'boosting_2025'}.get(selected,selected)
    version=result['protocol']['control_version'];sessions=[]
    for split in ['train','validation','test','future_holdout']:
        d=build_split(dataset,source,split,allow_future_evaluation=split=='future_holdout',control_version=version)
        if split!='future_holdout':d=only_2025(d)
        values={n:baseline(n,d['x']) for n in ['last_lap','rolling_median']}
        values['boosting_2025']=values['last_lap']+joblib.load(train/'unmodified_sequence_boosting.joblib').predict(flattened(d))
        values['restart_boosting']=predict_saved(train,d,'robust_tree')
        values['restart_gru']=predict_saved(train,d,'robust_gru')
        if any(not np.isfinite(p).all() for p in values.values()):raise ValueError('Nonfinite predictions')
        for sid in sorted({m['session_id'] for m in d['meta']}):
            ix=[i for i,m in enumerate(d['meta']) if m['session_id']==sid];first=ix[0]
            rows=[]
            for i in ix:
                x=d['x'][i];m=d['meta'][i]
                rows.append(dict(driver=m['driver_number'],lap=x['lap_number'],actual=d['y'][i],
                    state=x['control_state_at_cutoff'],prediction_at=m['prediction_at'],
                    predictions={n:float(p[i]) for n,p in values.items()}))
            sessions.append(dict(id=sid,circuit=d['x'][first]['circuit'],date=d['meta'][first]['race_start'],split=split,rows=rows))
    out.mkdir(parents=True,exist_ok=False)
    payload=dict(schema=1,model_version=digest((train/'artifact_hashes.json').read_bytes())[:12],
        selected_on_2025=choice,models=list(values),control_version=version,sessions=sessions,
        validation=result['scores']['validation'],regression=regression['scores'],
        limitations='Historical predictions, not live inference. In-sample training and reused validation/test races are labelled. 2026 is a previously seen regression set. Long laps remain included. No causal strategy advice.')
    save_json(out/'data.json',payload)
    assets=Path(__file__).parent/'static'
    for dest,src in [('index.html','model-demo.html'),('demo.js','model-demo.js')]:
        (out/dest).write_bytes((assets/src).read_bytes())
    save_json(out/'manifest.json',{p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    print(f'Exported {len(sessions)} races; default selected on 2025: {choice}')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['dataset','source','training','evaluation','output']:p.add_argument('--'+name,required=True)
    a=p.parse_args();torch.set_num_threads(1)
    with threadpool_limits(limits=1):run(a.dataset,a.source,a.training,a.evaluation,a.output)
if __name__=='__main__':main()
