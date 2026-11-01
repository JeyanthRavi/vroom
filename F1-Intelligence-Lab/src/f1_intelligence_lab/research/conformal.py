"""RQ2 fixture pipeline: split conformal and conformalised quantile regression."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingRegressor

from .artifacts import finish, prepare, require_protocol_before_labels, write_json
from .evaluate import assert_no_leakage, fixture_rows, write_predictions
from .stats import interval_score, wilson

FEATURES=['lap','pace_variance','local_yellows','cars_in_pit_window','tyre_age_gap','race_index']


def matrix(rows: List[Dict[str, Any]]) -> np.ndarray:
    return np.asarray([[float(row[name]) for name in FEATURES] for row in rows])


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    if scores.size == 0:raise ValueError('nonempty calibration scores required')
    level=min(1.0,math.ceil((scores.size+1)*(1-alpha))/scores.size)
    return float(np.quantile(scores,level,method='higher'))


def summary(rows: List[Dict[str, Any]], lower: np.ndarray, upper: np.ndarray, alpha: float) -> Dict[str, Any]:
    actual=np.asarray([row['target_s'] for row in rows]);covered=(actual>=lower)&(actual<=upper)
    low,high=wilson(int(covered.sum()),int(covered.size))
    per_race={}
    for race in sorted({row['race_id'] for row in rows}):
        mask=np.asarray([row['race_id']==race for row in rows]);race_covered=covered[mask]
        per_race[race]={'rows':int(mask.sum()),'coverage':float(race_covered.mean()),
                        'mean_width_s':float((upper[mask]-lower[mask]).mean())}
    return {'nominal_coverage':1-alpha,'rows':int(actual.size),'coverage':float(covered.mean()),
            'wilson95':[low,high],'mean_width_s':float((upper-lower).mean()),
            'interval_score':interval_score(actual,lower,upper,alpha),'per_race':per_race}


def run_fixture(output: str) -> Path:
    out=prepare(output,'rq2-conformal',True,['deterministic synthetic races'])
    require_protocol_before_labels(out);rows=fixture_rows();assert_no_leakage(rows)
    train=[row for row in rows if row['split']=='train'];calibration=[row for row in rows if row['split']=='validation'];test=[row for row in rows if row['split']=='test']
    if {row['race_id'] for row in train}&{row['race_id'] for row in calibration}:raise ValueError('calibration overlaps training')
    point=HistGradientBoostingRegressor(loss='absolute_error',max_leaf_nodes=7,l2_regularization=2,random_state=20261102).fit(matrix(train),[row['target_s'] for row in train])
    cal_prediction=point.predict(matrix(calibration));test_prediction=point.predict(matrix(test))
    cal_actual=np.asarray([row['target_s'] for row in calibration])
    methods={};exported=[]
    interval_cache: Dict[Tuple[str,int],Tuple[np.ndarray,np.ndarray]]={}
    for nominal in (80,90):
        alpha=1-nominal/100
        correction=conformal_quantile(np.abs(cal_actual-cal_prediction),alpha)
        lo=test_prediction-correction;hi=test_prediction+correction
        methods['split_%d'%nominal]=summary(test,lo,hi,alpha);interval_cache[('split',nominal)]=(lo,hi)
        lower_model=HistGradientBoostingRegressor(loss='quantile',quantile=alpha/2,max_leaf_nodes=7,l2_regularization=2,random_state=20261102).fit(matrix(train),[row['target_s'] for row in train])
        upper_model=HistGradientBoostingRegressor(loss='quantile',quantile=1-alpha/2,max_leaf_nodes=7,l2_regularization=2,random_state=20261102).fit(matrix(train),[row['target_s'] for row in train])
        cal_lo=lower_model.predict(matrix(calibration));cal_hi=upper_model.predict(matrix(calibration))
        cqr_score=np.maximum(cal_lo-cal_actual,cal_actual-cal_hi);cqr_correction=conformal_quantile(cqr_score,alpha)
        lo=lower_model.predict(matrix(test))-cqr_correction;hi=upper_model.predict(matrix(test))+cqr_correction
        methods['cqr_%d'%nominal]=summary(test,lo,hi,alpha);interval_cache[('cqr',nominal)]=(lo,hi)
    non_green=sum(row['state']!='GREEN' for row in calibration)
    results={'fixture_only':True,'evidence_status':'fixture-only: not evidence','methods':methods,
             'mondrian':{'status':'unsupported','reason':'calibration group below 30 rows','non_green_rows':non_green},
             'decision':'fixture-only; no calibration claim'}
    write_json(out/'results.json',results)
    lo80,hi80=interval_cache[('split',80)]
    for index,row in enumerate(test):exported.append({'race_id':row['race_id'],'lap':row['lap'],'actual_s':row['target_s'],'prediction_s':float(test_prediction[index]),'lower':float(lo80[index]),'upper':float(hi80[index]),'nominal_coverage':0.8})
    write_predictions(out/'predictions.csv',exported,list(exported[0]))
    with (out/'per_race.csv').open('w',newline='') as handle:
        writer=csv.writer(handle);writer.writerow(['method','race_id','coverage','mean_width_s'])
        for method,data in methods.items():
            for race,row in data['per_race'].items():writer.writerow([method,race,row['coverage'],row['mean_width_s']])
    (out/'REPORT.md').write_text('# RQ2 fixture report\n\n**Fixture-only: not evidence.** This run verifies disjoint calibration, split conformal/CQR bounds, Wilson intervals and interval scoring. Synthetic coverage cannot support a Formula 1 calibration claim.\n')
    figures=out/'figures';figures.mkdir();labels=list(methods);nominal_values=[methods[name]['nominal_coverage'] for name in labels];observed=[methods[name]['coverage'] for name in labels]
    fig,axis=plt.subplots(figsize=(7,4));axis.scatter(nominal_values,observed,color='#009E73');axis.plot([.75,.95],[.75,.95],linestyle='--',color='#777777');axis.set_xlim(.75,.95);axis.set_ylim(.75,1.01);axis.set_xlabel('Nominal coverage');axis.set_ylabel('Observed fixture coverage');axis.set_title('Fixture conformal coverage');fig.tight_layout();fig.savefig(figures/'coverage.png',dpi=120);plt.close(fig)
    (figures/'coverage.alt.txt').write_text('Fixture-only scatter plot of observed versus nominal coverage for split conformal and CQR at 80 and 90 percent.\n')
    finish(out);return out


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--fixture',action='store_true');args=parser.parse_args()
    if not args.fixture:raise SystemExit('Real-data mode requires audited split adapter; use --fixture or follow research/RUN-ON-REAL-DATA.md')
    run_fixture(args.output)


if __name__=='__main__':main()
