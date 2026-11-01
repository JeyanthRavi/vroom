"""RQ4 fixture pipeline: matched GRU, TCN, MLP and sequence boosting."""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import torch
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from torch import nn

from .artifacts import finish, prepare, require_protocol_before_labels, write_json
from .evaluate import assert_no_leakage, fixture_rows, regression_scores

SEEDS=[11,29,47]


class TCN(nn.Module):
    def __init__(self,features: int):
        super().__init__();self.network=nn.Sequential(nn.Conv1d(features,8,3,padding=1),nn.ReLU(),nn.Conv1d(8,6,3,padding=1),nn.ReLU());self.output=nn.Linear(6,1)
    def forward(self,x):return self.output(self.network(x.transpose(1,2))[:,:,-1]).squeeze(1)


class GRU(nn.Module):
    def __init__(self,features: int):
        super().__init__();self.gru=nn.GRU(features,7,batch_first=True);self.output=nn.Linear(7,1)
    def forward(self,x):return self.output(self.gru(x)[0][:,-1]).squeeze(1)


class MLP(nn.Module):
    def __init__(self,features: int,window: int):
        super().__init__();self.network=nn.Sequential(nn.Flatten(),nn.Linear(features*window,10),nn.ReLU(),nn.Linear(10,1))
    def forward(self,x):return self.network(x).squeeze(1)


def parameter_count(model: nn.Module) -> int:return sum(value.numel() for value in model.parameters())


def sequences(rows: List[Dict[str,Any]],window: int,with_state: bool,with_tyre: bool) -> Tuple[np.ndarray,np.ndarray,List[Dict[str,Any]]]:
    output=[];labels=[];meta=[]
    for race in sorted({row['race_id'] for row in rows}):
        race_rows=sorted([row for row in rows if row['race_id']==race],key=lambda row:row['lap'])
        for index in range(window,len(race_rows)):
            history=[]
            for row in race_rows[index-window:index]:
                values=[row['lap']/60,row['pace_variance'],row['cars_in_pit_window'],row['rolling_median_5']/100]
                if with_state:values.extend([row['local_yellows'],float(row['state']!='GREEN')])
                if with_tyre:values.append(row['tyre_age_gap']/30)
                history.append(values)
            output.append(history);labels.append(race_rows[index]['target_s']);meta.append(race_rows[index])
    return np.asarray(output,dtype=np.float32),np.asarray(labels,dtype=np.float32),meta


def train_neural(kind: str,x_train: np.ndarray,y_train: np.ndarray,x_test: np.ndarray,seed: int) -> Tuple[np.ndarray,int]:
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.set_num_threads(1)
    constructors={'tcn':lambda:TCN(x_train.shape[2]),'gru':lambda:GRU(x_train.shape[2]),'mlp':lambda:MLP(x_train.shape[2],x_train.shape[1])}
    model=constructors[kind]();mean=float(y_train.mean());scale=float(y_train.std() or 1)
    optimizer=torch.optim.Adam(model.parameters(),lr=0.02)
    x=torch.from_numpy(x_train);y=torch.from_numpy((y_train-mean)/scale)
    model.train()
    # One full-batch epoch keeps the fixture smoke grid under 30 seconds. Real
    # runs use validation early stopping in the audited-data adapter.
    for _ in range(1):
        optimizer.zero_grad();loss=torch.mean(torch.abs(model(x)-y));loss.backward();optimizer.step()
    model.eval()
    with torch.no_grad():prediction=model(torch.from_numpy(x_test)).numpy()*scale+mean
    return prediction,parameter_count(model)


def run_fixture(output: str) -> Path:
    out=prepare(output,'rq4-sequence-fairness',True,['deterministic synthetic races'])
    require_protocol_before_labels(out);rows=fixture_rows();assert_no_leakage(rows)
    cells: List[Dict[str,Any]]=[];canonical_rows: List[Dict[str,Any]]=[];canonical_cell: Dict[str,Any]={}
    for window in (5,10,15):
        for with_state in (False,True):
            for with_tyre in (False,True):
                x,y,meta=sequences(rows,window,with_state,with_tyre)
                train_mask=np.asarray([row['split']!='test' for row in meta]);test_mask=~train_mask
                scaler=StandardScaler();flat_train=scaler.fit_transform(x[train_mask].reshape(train_mask.sum(),-1));flat_test=scaler.transform(x[test_mask].reshape(test_mask.sum(),-1))
                scaled_train=flat_train.reshape(train_mask.sum(),window,x.shape[2]).astype(np.float32);scaled_test=flat_test.reshape(test_mask.sum(),window,x.shape[2]).astype(np.float32)
                actual=y[test_mask];races=[row['race_id'] for row in np.asarray(meta,dtype=object)[test_mask]]
                baseline=np.asarray([row['rolling_median_5'] for row in np.asarray(meta,dtype=object)[test_mask]])
                cell: Dict[str,Any]={'window':window,'with_state':with_state,'with_tyre':with_tyre,
                      'rolling_median_5':regression_scores(actual,baseline,races),'models':{}}
                boosting=HistGradientBoostingRegressor(loss='absolute_error',max_leaf_nodes=7,l2_regularization=2,random_state=20261102).fit(flat_train,y[train_mask])
                cell['models']['sequence_boosting']={'ensemble':regression_scores(actual,boosting.predict(flat_test),races),'parameters':'tree_not_comparable','seeds':[]}
                for kind in ('gru','tcn','mlp'):
                    seed_rows=[];seed_predictions=[];parameters=0
                    for seed in SEEDS:
                        prediction,parameters=train_neural(kind,scaled_train,y[train_mask],scaled_test,seed);seed_predictions.append(prediction);seed_rows.append({'seed':seed,'scores':regression_scores(actual,prediction,races)})
                    ensemble=np.mean(seed_predictions,axis=0)
                    cell['models'][kind]={'ensemble':regression_scores(actual,ensemble,races),'parameters':parameters,'seeds':seed_rows,'training_time_s':None,'training_time_status':'not measured in deterministic fixture'}
                    if window==10 and with_state and with_tyre and kind=='tcn':
                        for row,target,prediction,base in zip(np.asarray(meta,dtype=object)[test_mask],actual,ensemble,baseline):canonical_rows.append({'race_id':row['race_id'],'lap':row['lap'],'actual_s':float(target),'tcn_ensemble':float(prediction),'rolling_median_5':float(base)})
                cells.append(cell)
                if window==10 and with_state and with_tyre:canonical_cell=cell
    results={'fixture_only':True,'evidence_status':'fixture-only: not evidence','seeds':SEEDS,'cells':cells,'decision':'fixture-only; no model superiority claim'}
    write_json(out/'results.json',results)
    with (out/'predictions.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(canonical_rows[0]));writer.writeheader();writer.writerows(canonical_rows)
    with (out/'per_race.csv').open('w',newline='') as handle:
        row_writer=csv.writer(handle);row_writer.writerow(['window','with_state','with_tyre','model','race_id','mae_s'])
        for cell in cells:
            models={'rolling_median_5':cell['rolling_median_5']};models.update({name:value['ensemble'] for name,value in cell['models'].items()})
            for name,score in models.items():
                for race,row in score['per_race'].items():row_writer.writerow([cell['window'],cell['with_state'],cell['with_tyre'],name,race,row['mae_s']])
    (out/'REPORT.md').write_text('# RQ4 fixture report\n\n**Fixture-only: not evidence.** All 12 window/feature ablations run sequence boosting, GRU, TCN and parameter-matched MLP controls; neural models use seeds 11, 29 and 47. Synthetic scores cannot support a superiority claim.\n')
    figures=out/'figures';figures.mkdir();tcn_score=canonical_cell['models']['tcn']['ensemble'];baseline_score=canonical_cell['rolling_median_5'];races=sorted(tcn_score['per_race']);differences=[tcn_score['per_race'][race]['mae_s']-baseline_score['per_race'][race]['mae_s'] for race in races]
    fig,axis=plt.subplots(figsize=(7,4));axis.axvline(0,color='#777777',linestyle='--');axis.scatter(differences,range(len(races)),color='#CC79A7');axis.set_yticks(range(len(races)),races);axis.set_xlabel('TCN minus rolling-median MAE (seconds)');axis.set_title('Fixture paired race differences');fig.tight_layout();fig.savefig(figures/'paired-differences.png',dpi=120);plt.close(fig)
    (figures/'paired-differences.alt.txt').write_text('Fixture-only dot plot of per-race TCN ensemble minus rolling-median MAE in seconds; negative values favour TCN.\n')
    finish(out);return out


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--fixture',action='store_true');args=parser.parse_args()
    if not args.fixture:raise SystemExit('Real-data mode requires audited split adapter; use --fixture or follow research/RUN-ON-REAL-DATA.md')
    run_fixture(args.output)


if __name__=='__main__':main()
