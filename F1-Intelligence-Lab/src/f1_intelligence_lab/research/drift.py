"""RQ3 fixture pipeline: covariate shift, adversarial validation and timeline."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ks_2samp
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .artifacts import finish, prepare, require_protocol_before_labels, write_json
from .evaluate import assert_no_leakage, fixture_rows

FEATURES=['lap','pace_variance','local_yellows','cars_in_pit_window','tyre_age_gap','rolling_median_5']


def psi(reference: np.ndarray,comparison: np.ndarray,bins: int=10) -> float:
    edges=np.unique(np.quantile(reference,np.linspace(0,1,bins+1)))
    if edges.size<2:return 0.0
    edges[0],edges[-1]=-np.inf,np.inf
    ref=np.histogram(reference,bins=edges)[0]/reference.size
    cur=np.histogram(comparison,bins=edges)[0]/comparison.size
    ref=np.clip(ref,1e-6,None);cur=np.clip(cur,1e-6,None)
    return float(np.sum((cur-ref)*np.log(cur/ref)))


def run_fixture(output: str) -> Path:
    out=prepare(output,'rq3-drift',True,['deterministic synthetic races'])
    require_protocol_before_labels(out);rows=fixture_rows();assert_no_leakage(rows)
    reference=[row for row in rows if row['split']!='test'];comparison=[dict(row) for row in rows if row['split']=='test']
    for row in comparison:
        row['pace_variance']+=0.18;row['rolling_median_5']+=1.4;row['season_label']=1
    for row in reference:row['season_label']=0
    diagnostics={}
    for name in FEATURES:
        a=np.asarray([row[name] for row in reference],dtype=float);b=np.asarray([row[name] for row in comparison],dtype=float)
        ks=ks_2samp(a,b)
        diagnostics[name]={'psi':psi(a,b),'ks_statistic':float(ks.statistic),'ks_pvalue_descriptive':float(ks.pvalue)}
    combined=reference+comparison
    x=np.asarray([[row[name] for name in FEATURES] for row in combined],dtype=float)
    y=np.asarray([row['season_label'] for row in combined],dtype=int);groups=np.asarray([row['race_id'] for row in combined])
    model=make_pipeline(StandardScaler(),LogisticRegression(solver='liblinear',max_iter=1000,random_state=20261102))
    probability=cross_val_predict(model,x,y,groups=groups,cv=GroupKFold(4),method='predict_proba')[:,1]
    auc=float(roc_auc_score(y,probability));model.fit(x,y)
    coefficients=np.abs(model[-1].coef_[0]);ranking=[name for _,name in sorted(zip(coefficients,FEATURES),reverse=True)]
    timeline=[]
    for race in sorted({row['race_id'] for row in rows}):
        race_rows=[row for row in rows if row['race_id']==race]
        baseline=float(np.mean([abs(row['target_s']-row['rolling_median_5']) for row in race_rows]))
        timeline.append({'race_id':race,'race_index':race_rows[0]['race_index'],'rolling_median_5_mae_s':baseline})
    adaptations={
        'recency_weighting':{'selection':'2025 rolling folds only','fixture_status':'pipeline placeholder'},
        'per_circuit_normalisation':{'selection':'2025 rolling folds only','fixture_status':'pipeline placeholder'},
        'rolling_median_residual':{'selection':'2025 rolling folds only','fixture_status':'pipeline placeholder'},
    }
    results={'fixture_only':True,'evidence_status':'fixture-only: not evidence','feature_shift':diagnostics,
             'adversarial_validation':{'grouped_auc':auc,'top_features':ranking},
             'rolling_origin':timeline,'adaptations':adaptations,'decision':'fixture-only; no shift claim'}
    write_json(out/'results.json',results)
    with (out/'per_race.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(timeline[0]));writer.writeheader();writer.writerows(timeline)
    with (out/'predictions.csv').open('w',newline='') as handle:
        prediction_writer=csv.writer(handle);prediction_writer.writerow(['race_id','season_label','adversarial_probability'])
        for row,prediction in zip(combined,probability):prediction_writer.writerow([row['race_id'],row['season_label'],float(prediction)])
    figures=out/'figures';figures.mkdir()
    fig,axis=plt.subplots(figsize=(8,4));names=list(diagnostics);axis.bar(names,[diagnostics[name]['psi'] for name in names],color='#0072B2');axis.set_ylabel('Population stability index');axis.set_title('Fixture covariate shift by feature');axis.tick_params(axis='x',rotation=35);fig.tight_layout();fig.savefig(figures/'psi.png',dpi=120);plt.close(fig)
    (figures/'psi.alt.txt').write_text('Bar chart of fixture-only PSI values for six cutoff-safe features; taller bars indicate larger synthetic shift.\n')
    fig,axis=plt.subplots(figsize=(8,4));axis.plot([row['race_index'] for row in timeline],[row['rolling_median_5_mae_s'] for row in timeline],marker='o',color='#D55E00');axis.set_xlabel('Fixture race order');axis.set_ylabel('Rolling-median MAE (seconds)');axis.set_title('Fixture rolling-origin error timeline');fig.tight_layout();fig.savefig(figures/'rolling-mae.png',dpi=120);plt.close(fig)
    (figures/'rolling-mae.alt.txt').write_text('Line chart of rolling-median mean absolute error in seconds across eight synthetic races.\n')
    (out/'REPORT.md').write_text('# RQ3 drift report\n\n**Fixture-only: not evidence.** Synthetic shifts intentionally exercise PSI, KS, grouped adversarial validation and rolling-origin plotting. They do not explain the real 2025 to 2026 degradation.\n')
    finish(out);return out


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--fixture',action='store_true');args=parser.parse_args()
    if not args.fixture:raise SystemExit('Real-data mode requires audited split adapter; use --fixture or follow research/RUN-ON-REAL-DATA.md')
    run_fixture(args.output)


if __name__=='__main__':main()
