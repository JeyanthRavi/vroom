"""Opt-in local historical inference; no uploads, training, or holdout access."""
import json
import logging
import os
from pathlib import Path
from threading import Lock
from fastapi import APIRouter, HTTPException
from .ml_prep import FEATURES, digest

router = APIRouter(tags=['historical ML'])
LOCK = Lock()
SERVICE = None
LOG = logging.getLogger(__name__)


def interval_fields(prediction, configuration):
    """Return optional additive conformal fields without changing legacy rows."""
    if not configuration:return {}
    nominal=float(configuration['nominal_coverage'])
    lower=float(prediction)-float(configuration['lower_offset_s'])
    upper=float(prediction)+float(configuration['upper_offset_s'])
    if not 0<nominal<1 or lower>upper:raise ValueError('Invalid conformal interval configuration')
    return {'lower':lower,'upper':upper,'nominal_coverage':nominal}


@router.get('/api/ml/restart-research')
def restart_research():
    directory=os.environ.get('F1_ROBUST_RUN')
    if not directory:return {'status':'disabled','message':'Restart experiment is not configured.'}
    try:
        run=Path(directory);hashes=json.loads((run/'artifact_hashes.json').read_text())
        raw=(run/'results.json').read_bytes()
        if digest(raw)!=hashes['results.json']:raise ValueError('Experiment checksum mismatch')
        r=json.loads(raw)
        return dict(status='ready',**{k:r[k] for k in ['winner','tree_candidate','ratio','scores','coverage','stress','limitations']})
    except Exception:
        LOG.exception('Restart research unavailable')
        raise HTTPException(503,'Restart experiment unavailable or integrity check failed.')


@router.get('/api/ml/cross-season')
def cross_season_results():
    directory=os.environ.get('F1_CROSS_SEASON_RUN')
    if not directory:
        return {'status':'disabled','message':'2026 evaluation is not configured.'}
    try:
        run=Path(directory)
        hashes=json.loads((run/'artifact_hashes.json').read_text())
        raw=(run/'results.json').read_bytes()
        if digest(raw)!=hashes['results.json']:
            raise ValueError('Cross-season checksum mismatch')
        result=json.loads(raw)
        return dict(status='ready',version=hashes['results.json'][:12],
                    **{k:result[k] for k in ['coverage','races','excluded_races','scores',
                        'selected_before_2026','paired_vs_last_lap','holdout_status','limitations']})
    except Exception:
        LOG.exception('Cross-season evaluation unavailable')
        raise HTTPException(503,'Cross-season report unavailable or integrity check failed.')


@router.get('/api/ml/experiment')
def experiment():
    """Read-only experiment metrics; never loads neural weights or raw holdout data."""
    directory = os.environ.get('F1_DL_RUN')
    if not directory:
        return {'status':'disabled','message':'Sequence experiment is not configured.'}
    try:
        run = Path(directory)
        hashes = json.loads((run/'artifact_hashes.json').read_text())
        raw = (run/'results.json').read_bytes()
        if digest(raw) != hashes['results.json']:
            raise ValueError('Experiment checksum mismatch')
        result = json.loads(raw)
        names = list(result['scores']['validation'])
        return {'status':'ready','winner':result['winner'], 'coverage':result['coverage'],
                'protocol':result['protocol'], 'version':hashes['results.json'][:12],
                'models':[{'name':name,'validation':result['scores']['validation'][name],
                           'benchmark':result['scores']['test'][name],
                           'seed_validation_mae':[s['validation']['race_macro_mae_s'] for s in result['seeds'].get(name,[])]}
                          for name in names]}
    except Exception:
        LOG.exception('Sequence experiment unavailable')
        raise HTTPException(503,'Experiment unavailable or integrity check failed.')


class HistoricalPredictor:
    def __init__(self, dataset, run):
        # Operator-controlled trusted local paths only. Hashes detect corruption,
        # not malicious replacement of both artifact and manifest.
        import joblib
        import sklearn
        self.dataset = Path(dataset)
        run = Path(run)
        hashes = json.loads((run/'artifact_hashes.json').read_text())
        for name in ['results.json','selected.joblib','selection.json']:
            if hashes[name] != digest((run/name).read_bytes()):
                raise ValueError('Model artifact checksum mismatch')
        self.results = json.loads((run/'results.json').read_text())
        for name in ['audit.json','feature_contract.json','train.csv','validation.csv','test.csv']:
            if self.results['dataset_hashes'][name] != digest((self.dataset/name).read_bytes()):
                raise ValueError('Training dataset mismatch')
        if self.results['environment']['sklearn'] != sklearn.__version__:
            raise ValueError('Model runtime version mismatch')
        self.audit = json.loads((self.dataset/'audit.json').read_text())
        self.bundle = joblib.load(run/'selected.joblib')
        if self.bundle['features'] != FEATURES or self.bundle['name'] != self.results['selection']['winner']:
            raise ValueError('Model contract mismatch')
        self.version = hashes['selected.joblib'][:12]
        self.interval = None
        if (run/'conformal.json').is_file():
            if hashes.get('conformal.json')!=digest((run/'conformal.json').read_bytes()):
                raise ValueError('Conformal artifact checksum mismatch')
            self.interval=json.loads((run/'conformal.json').read_text())
        self.cache = {}

    def sessions(self):
        return [{'session_id':s['session_id'],'split':s['split']} for s in self.audit['session_reports']
                if s['verified_for_prep'] and s['split'] in {'train','validation','test'}]

    def session(self, sid):
        report = next((s for s in self.audit['session_reports'] if s['session_id']==sid),None)
        base = {'session_id':sid,'available_sessions':self.sessions()}
        if report and report['split']=='future_holdout':
            return dict(base,status='reserved',message='This three-lap model view does not serve 2026 predictions. See the separate frozen cross-season evaluation below when configured.')
        if not report or not report['verified_for_prep']:
            return dict(base,status='unavailable',message='This race is outside the verified training dataset. No synthetic prediction is substituted.')
        from .ml_dataset import load_split
        from .ml_train import predict, baseline
        from threadpoolctl import threadpool_limits
        split = report['split']
        if split not in self.cache:
            self.cache[split] = load_split(self.dataset,split)
        features, labels, meta = self.cache[split]
        ix = [i for i,m in enumerate(meta) if m['session_id']==sid]
        if not ix:
            return dict(base,status='unavailable',message='No eligible three-lap-history examples for this race.')
        x = [features[i] for i in ix]
        with threadpool_limits(limits=1):
            values = predict(self.bundle['name'],self.bundle['model'],x)
        reference = baseline(self.results['selection']['baseline'],x)
        rows = []
        for i,p,b in zip(ix,values,reference):
            row={'driver':meta[i]['driver_number'],'lap':int(features[i]['lap_number']),
                'prediction_at':meta[i]['prediction_at'],'actual_s':labels[i],
                'predicted_s':float(p),'baseline_s':float(b),'absolute_error_s':abs(float(p)-labels[i]),
                'control_state':features[i]['control_state_at_cutoff']}
            row.update(interval_fields(p,self.interval));rows.append(row)
        return dict(base,status='ready',model=self.bundle['name'],version=self.version,split=split,
                    baseline=self.results['selection']['baseline'],rows=rows,
                    message={'train':'Training race: in-sample predictions, not an independent accuracy test.',
                             'validation':'Validation race: used for model selection.',
                             'test':'Held-out test race: not used for fitting or model selection.'}[split])


@router.get('/api/ml/races/{sid}')
def predictions(sid: str):
    global SERVICE
    dataset,run = os.environ.get('F1_ML_DATASET'),os.environ.get('F1_ML_RUN')
    if not dataset or not run:
        return {'status':'disabled','message':'ML is not configured on this server. No model predictions are available.'}
    try:
        with LOCK:
            if SERVICE is None:
                SERVICE = HistoricalPredictor(dataset,run)
            return SERVICE.session(sid)
    except Exception:
        LOG.exception('Historical ML inference unavailable')
        raise HTTPException(503,'Model unavailable or integrity check failed. Ask the local operator to check configuration.')
