"""RQ1 fixture pipeline: conditional pace plus neutralisation hazard."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
import torch

from .artifacts import finish, prepare, require_protocol_before_labels, write_json
from .evaluate import assert_no_leakage, fixture_rows, regression_scores, write_predictions
from .stats import expected_calibration_error, paired_race_bootstrap, reliability_bins
from .tcn import TCN

FEATURES = ['lap','pace_variance','local_yellows','cars_in_pit_window','tyre_age_gap','race_index']


def feature(row: Dict[str, Any]) -> Dict[str, Any]:
    values = {name: row[name] for name in FEATURES}
    values['circuit'] = row['circuit']
    values['state'] = row['state']
    return values


def _classification(y: np.ndarray, probability: np.ndarray) -> Dict[str, Any]:
    return {
        'rows': int(y.size), 'positives': int(y.sum()), 'prevalence': float(y.mean()),
        'pr_auc': float(average_precision_score(y, probability)),
        'roc_auc': float(roc_auc_score(y, probability)),
        'brier': float(brier_score_loss(y, probability)),
        'log_loss': float(log_loss(y, probability, labels=[0,1])),
        'ece_10': expected_calibration_error(y.tolist(), probability.tolist()),
        'reliability': reliability_bins(y.tolist(), probability.tolist(), 10),
    }


def _breakdowns(rows: List[Dict[str, Any]], y: np.ndarray, probability: np.ndarray) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for field in ('race_id','circuit'):
        output[field]={}
        for value in sorted({row[field] for row in rows}):
            mask=np.asarray([row[field]==value for row in rows]);labels=y[mask];predicted=probability[mask]
            output[field][value]={'rows':int(mask.sum()),'positives':int(labels.sum()),
                                  'prevalence':float(labels.mean()),'brier':float(brier_score_loss(labels,predicted)),
                                  'pr_auc':float(average_precision_score(labels,predicted)) if len(set(labels))>1 else None}
    return output


def _sequence_matrix(rows: List[Dict[str,Any]],window: int=5) -> np.ndarray:
    output=[]
    by_race={race:sorted([row for row in rows if row['race_id']==race],key=lambda row:row['lap']) for race in {row['race_id'] for row in rows}}
    positions={(row['race_id'],row['lap']):index for race in by_race.values() for index,row in enumerate(race)}
    for row in rows:
        race=by_race[row['race_id']];index=positions[(row['race_id'],row['lap'])];history=race[max(0,index-window+1):index+1]
        history=[history[0]]*(window-len(history))+history
        output.append([[float(item[name]) for name in FEATURES] for item in history])
    return np.asarray(output,dtype=np.float32)


def _tcn_probability(train: List[Dict[str,Any]],test: List[Dict[str,Any]],key: str) -> np.ndarray:
    torch.manual_seed(20261102);torch.set_num_threads(1);x_train=torch.from_numpy(_sequence_matrix(train));x_test=torch.from_numpy(_sequence_matrix(test));y=torch.tensor([row[key] for row in train],dtype=torch.float32)
    model=TCN(x_train.shape[2]);optimizer=torch.optim.Adam(model.parameters(),lr=.01);positive=max(1,float(y.sum()));criterion=torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor((len(y)-positive)/positive))
    for _ in range(6):optimizer.zero_grad();loss=criterion(model(x_train),y);loss.backward();optimizer.step()
    with torch.no_grad():return torch.sigmoid(model(x_test)).numpy()


def run_fixture(output: str) -> Path:
    out = prepare(output, 'rq1-pace-hazard', True, ['deterministic synthetic races'])
    require_protocol_before_labels(out)
    rows = fixture_rows()
    assert_no_leakage(rows)
    train = [row for row in rows if row['split'] in {'train','validation'}]
    test = [row for row in rows if row['split']=='test']
    train_x, test_x = [feature(row) for row in train], [feature(row) for row in test]
    hazard_results = {}
    hazard_predictions = {}
    for horizon in (1,3):
        key = 'hazard_h%d' % horizon
        y_train = np.asarray([row[key] for row in train],dtype=int)
        y_test = np.asarray([row[key] for row in test],dtype=int)
        base = np.full(y_test.shape,float(y_train.mean()))
        logistic = make_pipeline(DictVectorizer(sparse=True),LogisticRegression(
            class_weight='balanced',max_iter=1000,random_state=20261102))
        logistic.fit(train_x,y_train)
        logit_probability = logistic.predict_proba(test_x)[:,1]
        tree = make_pipeline(DictVectorizer(sparse=False),HistGradientBoostingClassifier(
            max_leaf_nodes=7,l2_regularization=2.0,random_state=20261102))
        weights=np.where(y_train==1,len(y_train)/(2*max(1,y_train.sum())),len(y_train)/(2*max(1,(y_train==0).sum())))
        tree.fit(train_x,y_train,histgradientboostingclassifier__sample_weight=weights)
        tree_probability=tree.predict_proba(test_x)[:,1]
        tcn_probability=_tcn_probability(train,test,key)
        hazard_results[str(horizon)]={
            'base_rate':_classification(y_test,base),
            'logistic':_classification(y_test,logit_probability),
            'boosting':_classification(y_test,tree_probability),
            'small_tcn':_classification(y_test,tcn_probability),
        }
        for model_name,probability in [('base_rate',base),('logistic',logit_probability),('boosting',tree_probability),('small_tcn',tcn_probability)]:
            hazard_results[str(horizon)][model_name]['breakdowns']=_breakdowns(test,y_test,probability)
        hazard_predictions[horizon]=tree_probability

    pace_train=[row for row in train if row['green_target']]
    pace_model=make_pipeline(DictVectorizer(sparse=False),HistGradientBoostingRegressor(
        loss='absolute_error',max_leaf_nodes=7,l2_regularization=2.0,random_state=20261102))
    pace_model.fit([feature(row) for row in pace_train],[row['pace_target_s'] for row in pace_train])
    pace=np.asarray(pace_model.predict(test_x))
    mixed_model=make_pipeline(DictVectorizer(sparse=False),HistGradientBoostingRegressor(
        loss='absolute_error',max_leaf_nodes=7,l2_regularization=2.0,random_state=20261102))
    mixed_model.fit(train_x,[row['target_s'] for row in train])
    mixed=np.asarray(mixed_model.predict(test_x))
    combined=pace+hazard_predictions[1]*25.0
    actual=np.asarray([row['target_s'] for row in test])
    races=[row['race_id'] for row in test]
    predictions={
        'rolling_median_5':np.asarray([row['rolling_median_5'] for row in test]),
        'single_stage_boosting':mixed,'two_stage':combined,
    }
    scores={name:regression_scores(actual,value,races) for name,value in predictions.items()}
    differences=[]
    for race in sorted(set(races)):
        differences.append(scores['two_stage']['per_race'][race]['mae_s']-
                           scores['rolling_median_5']['per_race'][race]['mae_s'])
    paired=paired_race_bootstrap(differences)
    results={'fixture_only':True,'evidence_status':'fixture-only: not evidence',
             'hazard':hazard_results,'mixed_target':scores,'paired_vs_rolling_median_5':paired,
             'decision':'fixture-only; no research success/failure claim'}
    write_json(out/'results.json',results)
    exported=[]
    for index,row in enumerate(test):
        exported.append({'race_id':row['race_id'],'lap':row['lap'],'actual_s':row['target_s'],
                         'rolling_median_5':float(predictions['rolling_median_5'][index]),
                         'single_stage_boosting':float(mixed[index]),'two_stage':float(combined[index]),
                         'hazard_probability_h1':float(hazard_predictions[1][index])})
    write_predictions(out/'predictions.csv',exported,list(exported[0]))
    with (out/'per_race.csv').open('w',newline='') as handle:
        writer=csv.writer(handle);writer.writerow(['race_id','model','mae_s'])
        for name,score in scores.items():
            for race,row in score['per_race'].items():writer.writerow([race,name,row['mae_s']])
    (out/'REPORT.md').write_text(
        '# RQ1 fixture report\n\n**Fixture-only: not evidence.** This smoke run verifies the two-stage pace/hazard pipeline, metrics, calibration bins and immutable artifacts. Synthetic scores cannot support a Formula 1 performance claim.\n')
    figures=out/'figures';figures.mkdir();curve=hazard_results['1']['boosting']['reliability']
    fig,axis=plt.subplots(figsize=(5,5));axis.plot([0,1],[0,1],linestyle='--',color='#777777');axis.plot([row['mean_probability'] for row in curve],[row['observed_rate'] for row in curve],marker='o',color='#0072B2');axis.set_xlabel('Predicted neutralisation probability');axis.set_ylabel('Observed fixture frequency');axis.set_title('Fixture H=1 reliability');fig.tight_layout();fig.savefig(figures/'hazard-reliability.png',dpi=120);plt.close(fig)
    (figures/'hazard-reliability.alt.txt').write_text('Fixture-only reliability curve comparing predicted H=1 neutralisation probabilities with observed synthetic frequencies; diagonal denotes ideal calibration.\n')
    finish(out)
    return out


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    parser.add_argument('--fixture',action='store_true',help='run deterministic synthetic smoke data')
    args=parser.parse_args()
    if not args.fixture:raise SystemExit('Real-data mode requires audited split adapter; use --fixture or follow research/RUN-ON-REAL-DATA.md')
    run_fixture(args.output)


if __name__=='__main__':main()
