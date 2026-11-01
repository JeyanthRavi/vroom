"""Reproducible offline next-lap experiment. No web service or test-set tuning."""
import argparse
import csv
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .ml_dataset import CATEGORICAL, load_split
from .ml_prep import FEATURES, LABEL, digest

BASELINES = ('last_lap', 'rolling_mean', 'rolling_median')
MODELS = ('ridge', 'hist_absolute')
CONFIG = {
    'version': 1, 'seed': 42, 'primary_metric': 'race_macro_mae_s',
    'features': FEATURES, 'target': LABEL, 'model_target': 'target minus lag_1_s',
    'ridge': {'alpha': 10.0, 'solver': 'svd'},
    'hist_absolute': {'loss': 'absolute_error', 'max_iter': 150,
                      'learning_rate': 0.05, 'max_leaf_nodes': 15,
                      'min_samples_leaf': 30, 'l2_regularization': 1.0,
                      'early_stopping': False, 'random_state': 42},
    'selection': 'lowest validation race_macro_mae_s; ties prefer baseline/order',
    'future_holdout': 'not read', 'label_trimming': 'none',
}


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def checked_features(rows):
    """Reject rather than silently accept metadata or missing/nonfinite inputs."""
    if not rows:
        raise ValueError('Empty input')
    for row in rows:
        if set(row) != set(FEATURES):
            raise ValueError('Feature allowlist mismatch')
        for key, value in row.items():
            if key in CATEGORICAL:
                if not isinstance(value, str) or not value:
                    raise ValueError('Invalid categorical input')
            elif isinstance(value, bool) or not np.isfinite(float(value)):
                raise ValueError('Nonfinite or invalid numeric input')
    return rows


def baseline(name, rows):
    checked_features(rows)
    if name == 'last_lap':
        return np.array([r['lag_1_s'] for r in rows], dtype=float)
    if name == 'rolling_mean':
        return np.array([r['rolling_mean_3_s'] for r in rows], dtype=float)
    if name == 'rolling_median':
        return np.array([np.median([r['lag_1_s'], r['lag_2_s'], r['lag_3_s']]) for r in rows])
    raise ValueError('Unknown baseline')


def fit_model(name, rows, labels):
    checked_features(rows)
    labels = np.asarray(labels, dtype=float)
    if len(labels) != len(rows) or not np.isfinite(labels).all():
        raise ValueError('Invalid labels')
    if name == 'ridge':
        model = make_pipeline(DictVectorizer(sparse=False), StandardScaler(),
                              Ridge(**CONFIG[name]))
    elif name == 'hist_absolute':
        model = make_pipeline(DictVectorizer(sparse=False),
                              HistGradientBoostingRegressor(**CONFIG[name]))
    else:
        raise ValueError('Unknown model')
    # Learn the change from the last completed lap, not a circuit-specific intercept.
    model.fit(rows, labels - baseline('last_lap', rows))
    return model


def predict(name, model, rows):
    checked_features(rows)
    if name in BASELINES:
        values = baseline(name, rows)
    else:
        values = baseline('last_lap', rows) + model.predict(rows)
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite predictions')
    return values


def metrics(labels, predictions):
    y, p = np.asarray(labels), np.asarray(predictions)
    if not len(y) or len(y) != len(p) or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('Invalid evaluation arrays')
    return {'rows': len(y), 'mae_s': float(mean_absolute_error(y, p)),
            'rmse_s': float(np.sqrt(mean_squared_error(y, p))),
            'r2': float(r2_score(y, p)) if len(y) > 1 and np.var(y) > 0 else None,
            'p90_abs_error_s': float(np.quantile(np.abs(y-p), .90))}


def evaluate(labels, predictions, metadata, rows):
    y, p = np.asarray(labels), np.asarray(predictions)
    groups = sorted({m['session_id'] for m in metadata})
    per_race = {}
    for session in groups:
        ix = [i for i, m in enumerate(metadata) if m['session_id'] == session]
        per_race[session] = metrics(y[ix], p[ix])
    result = metrics(y, p)
    result['race_macro_mae_s'] = float(np.mean([v['mae_s'] for v in per_race.values()]))
    result['per_race'] = per_race
    # Descriptive slices only: never filter labels for fitting or model selection.
    slices = {
        'known_green_at_cutoff': [i for i,r in enumerate(rows) if r['control_state_at_cutoff']=='GREEN'],
        'not_known_green_at_cutoff': [i for i,r in enumerate(rows) if r['control_state_at_cutoff']!='GREEN'],
        'previous_pit_out': [i for i,r in enumerate(rows) if r['previous_pit_out']==1],
        'observed_target_over_180s': [i for i,v in enumerate(y) if v>180],
    }
    result['slices'] = {k: metrics(y[ix], p[ix]) if ix else {'rows': 0} for k,ix in slices.items()}
    return result


def expanding_folds(metadata):
    sessions = sorted({(m['race_start'],m['session_id']) for m in metadata})
    blocks = np.array_split(np.arange(len(sessions)), 4)
    if any(len(b)==0 for b in blocks):
        raise ValueError('Need at least four training races for chronological CV')
    for k in range(1,4):
        before = {sessions[i][1] for b in blocks[:k] for i in b}
        after = {sessions[i][1] for i in blocks[k]}
        yield ([i for i,m in enumerate(metadata) if m['session_id'] in before],
               [i for i,m in enumerate(metadata) if m['session_id'] in after])


def select_candidate(validation):
    return min(validation, key=lambda name: validation[name]['race_macro_mae_s'])


def run(dataset, output, skill_tools=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    save_json(output/'protocol.json', CONFIG)  # frozen before training/validation/test
    train, y_train, m_train = load_split(dataset, 'train')
    val, y_val, m_val = load_split(dataset, 'validation')
    if {m['session_id'] for m in m_train} & {m['session_id'] for m in m_val}:
        raise ValueError('Race overlap')
    with (output/'train_features_only.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FEATURES+[LABEL])
        writer.writeheader()
        writer.writerows(dict(r, **{LABEL:y}) for r,y in zip(train,y_train))
    if skill_tools:
        ranking = subprocess.check_output([sys.executable, str(Path(skill_tools)/'feature_selector.py'),
                  '--file', str(output/'train_features_only.csv'), '--target', LABEL, '--json'], text=True)
        save_json(output/'feature_ranking.json', json.loads(ranking))
    save_json(output/'feature_selection.json', {
        'selected': FEATURES, 'fit_split': 'train',
        'reason': 'Retain all 13 prespecified features; ranking is diagnostic, not a significance test. No holdout-driven selection.'})
    fitted, train_scores, val_scores, cv, seconds = {}, {}, {}, {}, {}
    for name in BASELINES + MODELS:
        start = time.perf_counter()
        model = fit_model(name, train, y_train) if name in MODELS else None
        fitted[name] = model
        train_scores[name] = evaluate(y_train, predict(name,model,train), m_train, train)
        val_scores[name] = evaluate(y_val, predict(name,model,val), m_val, val)
        cv[name] = []
        for ix,jx in expanding_folds(m_train):
            x_fit, x_eval = [train[i] for i in ix], [train[i] for i in jx]
            fold_model = fit_model(name,x_fit,[y_train[i] for i in ix]) if name in MODELS else None
            cv[name].append(evaluate([y_train[i] for i in jx], predict(name,fold_model,x_eval),
                                     [m_train[i] for i in jx], x_eval))
        seconds[name] = time.perf_counter()-start
        if name in MODELS:
            joblib.dump({'name':name,'model':model,'features':FEATURES,'config':CONFIG}, output/(name+'.joblib'))
        print(name, 'validation race MAE:', val_scores[name]['race_macro_mae_s'], flush=True)
    winner = select_candidate(val_scores)
    best_baseline = select_candidate({k:val_scores[k] for k in BASELINES})
    best_model = select_candidate({k:val_scores[k] for k in MODELS})
    selection = {'winner':winner,'baseline':best_baseline,'model':best_model,
                 'selected_at_utc':datetime.now(timezone.utc).isoformat(),
                 'validation':val_scores,'test_used_for_selection':False}
    save_json(output/'selection.json', selection)  # written BEFORE opening test
    joblib.dump({'name':winner,'model':fitted[winner],'features':FEATURES,'config':CONFIG}, output/'selected.joblib')
    test, y_test, m_test = load_split(dataset, 'test')
    if {m['session_id'] for m in m_test} & {m['session_id'] for m in m_train+m_val}:
        raise ValueError('Test race overlap')
    test_scores = {}
    # Only the validation-selected model and baseline are scored on the final test.
    for name in dict.fromkeys([best_baseline, best_model]):
        p = predict(name,fitted[name],test)
        test_scores[name] = evaluate(y_test,p,m_test,test)
        with (output/(name+'_test_predictions.csv')).open('w',newline='') as f:
            writer=csv.writer(f)
            writer.writerow(['row_id','session_id','actual_s','predicted_s','absolute_error_s'])
            writer.writerows([m['row_id'],m['session_id'],y,float(v),abs(y-float(v))] for m,y,v in zip(m_test,y_test,p))
    if skill_tools:
        for name in BASELINES+MODELS:
            values = {k:v for k,v in val_scores[name].items() if isinstance(v,(int,float))}
            subprocess.run([sys.executable,str(Path(skill_tools)/'experiment_tracker.py'),
                '--log-file',str(output/'experiments.json'),'log','--name',name,
                '--params',json.dumps({'protocol':CONFIG,'fit_split':'train'}),
                '--metrics',json.dumps(values),'--tags','validation,offline',
                '--notes','Lower MAE/RMSE is better; use selection.json, not tracker max-value ranking.'],check=True,capture_output=True)
    manifest = json.loads((Path(dataset)/'manifest.json').read_text())
    report = {'protocol':CONFIG,'dataset_hashes':{k:manifest[k] for k in ['audit.json','feature_contract.json','train.csv','validation.csv','test.csv']},
              'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'joblib':joblib.__version__},
              'created_utc':datetime.now(timezone.utc).isoformat(), 'selection':selection,
              'train':train_scores,'validation':val_scores,'test':test_scores,'training_race_cv':cv,
              'elapsed_seconds':seconds, 'source_sha256':digest(Path(__file__).read_bytes())}
    save_json(output/'results.json',report)
    lines = ['# First-model experiment', '', 'Primary metric: equal-weight per-race MAE in seconds (lower is better).',
             '', '| Candidate | Train race MAE | Validation race MAE | Test race MAE | Test RMSE | Test R² |',
             '|---|---:|---:|---:|---:|---:|']
    for name in BASELINES+MODELS:
        t=test_scores.get(name,{})
        vals=[train_scores[name]['race_macro_mae_s'],val_scores[name]['race_macro_mae_s'],
              t.get('race_macro_mae_s'),t.get('rmse_s'),t.get('r2')]
        lines.append('| '+name+' | '+' | '.join('—' if v is None else f'{v:.4f}' for v in vals)+' |')
    lines += ['',f'Validation-selected default: **{winner}**. Selected trained model: **{best_model}**.',
              '', 'Models and preprocessing fitted on training races only; three expanding whole-race CV folds are diagnostic. No parameter search, random lap splits, validation refit, or test-driven changes. 2026 holdout not read.',
              '', '## Limitations', '',
              '- Only three test races; correlated laps are not independent samples. No universal accuracy or statistical-significance claim.',
              '- Historical event timestamps are not verified live arrival times. Source verification is bounded, not proof of every lap.',
              '- Requires three contiguous prior laps and predicts completed-lap duration, not retirement or future incidents.',
              '- Long laps, pit effects and neutralisations remain in the labels. Cutoff-state slices do not reveal future incidents; >180-second slice is hindsight diagnostic only.',
              '- Unseen circuit categories are ignored by the training-fitted encoder; lap history still carries circuit pace.',
              '- No causal strategy recommendation, production API integration or deployment is provided.',
              '', 'Only load joblib artifacts that you created and trust; deserialization can execute code.']
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')
    save_json(output/'artifact_hashes.json',{p.name:digest(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()})
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--skill-tools',help='Optional directory with feature_selector.py and experiment_tracker.py')
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        result=run(args.dataset,args.output,args.skill_tools)
    print('Selected:',result['selection']['winner'])


if __name__=='__main__':
    main()
