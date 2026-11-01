"""Export checksum-verified historical results, never weights or source caches.

Aggregate mode is the safe default. Full mode is an explicit, local-only choice
while redistribution permission for lap-level source data remains unresolved.
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from threadpoolctl import threadpool_limits

from .ml_prep import digest
from .ml_sequences import build_split, flattened
from .ml_train import baseline, save_json
from .restart_evaluate import verify
from .robust_train import only_2025, predict_saved


def _score_rows(rows, models):
    scores = {}
    for model in models:
        errors = [abs(row['actual'] - row['predictions'][model]) for row in rows]
        scores[model] = {
            'eligible_laps': len(errors),
            'mae_s': float(np.mean(errors)) if errors else None,
            'median_ae_s': float(np.median(errors)) if errors else None,
        }
    return scores


def aggregate_payload(payload):
    """Remove lap- and driver-level observations from a full replay payload."""
    models = payload['models']
    races = []
    all_errors = {model: [] for model in models}
    for session in payload['sessions']:
        rows = session['rows']
        for model in models:
            all_errors[model].extend(
                abs(row['actual'] - row['predictions'][model]) for row in rows
            )
        races.append({
            'id': session['id'],
            'circuit': session['circuit'],
            'date': session['date'],
            'split': session['split'],
            'summary': _score_rows(rows, models),
        })
    histograms = {}
    calibration = {}
    for model, errors in all_errors.items():
        values = np.asarray(errors, dtype=float)
        counts, edges = np.histogram(values, bins=[0, 0.5, 1, 2, 5, 10, 30, np.inf])
        histograms[model] = {
            'bin_upper_s': [0.5, 1, 2, 5, 10, 30, None],
            'counts': counts.tolist(),
        }
        calibration[model] = {
            'eligible_laps': int(values.size),
            'within_1s_fraction': float(np.mean(values <= 1)) if values.size else None,
            'within_5s_fraction': float(np.mean(values <= 5)) if values.size else None,
        }
    return {
        'schema': 2,
        'export_mode': 'aggregate',
        'model_version': payload['model_version'],
        'selected_on_2025': payload['selected_on_2025'],
        'models': models,
        'control_version': payload['control_version'],
        'races': races,
        'error_histograms': histograms,
        'calibration': calibration,
        'validation': payload['validation'],
        'regression': payload['regression'],
        'limitations': payload['limitations'],
    }


def run(dataset,source,training,evaluation,output,mode='aggregate'):
    if mode not in {'aggregate', 'full'}:
        raise ValueError('mode must be aggregate or full')
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
                rows.append({'driver': m['driver_number'],'lap': x['lap_number'],'actual': d['y'][i],
                    'state': x['control_state_at_cutoff'],'prediction_at': m['prediction_at'],
                    'predictions': {n:float(p[i]) for n,p in values.items()}})
            sessions.append({'id': sid,'circuit': d['x'][first]['circuit'],'date': d['meta'][first]['race_start'],'split': split,'rows': rows})
    out.mkdir(parents=True,exist_ok=False)
    payload={'schema': 1,'export_mode': 'full','model_version': digest((train/'artifact_hashes.json').read_bytes())[:12],
        'selected_on_2025': choice,'models': list(values),'control_version': version,'sessions': sessions,
        'validation': result['scores']['validation'],'regression': regression['scores'],
        'limitations': 'Historical predictions, not live inference. In-sample training and reused validation/test races are labelled. Evaluated on previously examined 2026 races; not an independent holdout. Long laps remain included. No causal strategy advice.'}
    save_json(out/'data.json',aggregate_payload(payload) if mode=='aggregate' else payload)
    assets=Path(__file__).parent/'static'
    for dest,src in [('index.html','model-demo.html'),('demo.js','model-demo.js')]:
        (out/dest).write_bytes((assets/src).read_bytes())
    files={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()}
    save_json(out/'manifest.json',{'schema':2,'export_mode':mode,'files':files})
    print(f'Exported {len(sessions)} races in {mode} mode; default selected on 2025: {choice}')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['dataset','source','training','evaluation','output']:p.add_argument('--'+name,required=True)
    p.add_argument('--mode',choices=['aggregate','full'],default='aggregate')
    a=p.parse_args();torch.set_num_threads(1)
    with threadpool_limits(limits=1):run(a.dataset,a.source,a.training,a.evaluation,a.output,a.mode)
if __name__=='__main__':main()
