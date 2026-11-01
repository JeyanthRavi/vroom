import json

import pytest

pytest.importorskip('sklearn')
import joblib
import numpy as np
from f1_intelligence_lab import ml_train as ml
from f1_intelligence_lab.ml_prep import FEATURES
from threadpoolctl import threadpool_limits


def row(i=0):
    result={k:float(i+1) for k in FEATURES}
    result.update(circuit='A',previous_compound='HARD',control_state_at_cutoff='GREEN',
                  lag_1_s=90.+i,lag_2_s=92.+i,lag_3_s=94.+i,rolling_mean_3_s=92.+i)
    return result


def test_baselines_and_metrics():
    assert ml.baseline('last_lap',[row()]).tolist()==[90.]
    assert ml.baseline('rolling_mean',[row()]).tolist()==[92.]
    assert ml.baseline('rolling_median',[row()]).tolist()==[92.]
    assert ml.metrics([1,3],[2,2])['mae_s']==1
    assert ml.metrics([1],[1])['r2'] is None
    with pytest.raises(ValueError): ml.metrics([1],[float('nan')])


@pytest.mark.parametrize('change',[{'session_id':'secret'}, {'lag_1_s':float('nan')}, {'circuit':''}])
def test_invalid_input(change):
    with pytest.raises(ValueError): ml.predict('last_lap',None,[dict(row(),**change)])


def test_race_macro_not_lap_micro():
    scores=ml.evaluate([0,0,0,0],[1,1,1,9],
                       [{'session_id':s} for s in ['a','a','a','b']],[row()]*4)
    assert scores['mae_s']==3
    assert scores['race_macro_mae_s']==5
    assert ml.select_candidate({'baseline':{'race_macro_mae_s':1},'model':{'race_macro_mae_s':1}})=='baseline'


def test_chronological_whole_race_folds():
    meta=[{'race_start':f'2025-{i:02d}-01','session_id':str(i)} for i in range(1,9) for _ in range(2)]
    for train,val in ml.expanding_folds(meta):
        assert max(meta[i]['race_start'] for i in train)<min(meta[i]['race_start'] for i in val)
        assert not {meta[i]['session_id'] for i in train}&{meta[i]['session_id'] for i in val}


@pytest.mark.parametrize('name',ml.MODELS)
def test_train_only_encoder_reproducible_serialization(name,tmp_path):
    rows=[row(i%10) for i in range(65)]
    labels=[r['lag_1_s']+.5 for r in rows]
    with threadpool_limits(limits=1):
        a=ml.fit_model(name,rows,labels)
        b=ml.fit_model(name,rows,labels)
        unseen=dict(row(),circuit='NEVER_TRAINED')
        expected=ml.predict(name,a,[unseen])
        np.testing.assert_allclose(expected,ml.predict(name,b,[unseen]))
        assert 'circuit=NEVER_TRAINED' not in a[0].vocabulary_
        joblib.dump(a,tmp_path/'model.joblib')
        np.testing.assert_allclose(expected,ml.predict(name,joblib.load(tmp_path/'model.joblib'),[unseen]))


def test_test_loaded_only_after_selection_and_no_future(monkeypatch,tmp_path):
    calls=[]
    def load(directory,split):
        calls.append(split)
        if split=='test':
            assert (tmp_path/'run'/'selection.json').exists()
            assert json.loads((tmp_path/'run'/'selection.json').read_text())['test_used_for_selection'] is False
        assert split!='future_holdout'
        rows=[row(i%3) for i in range(16)]
        meta=[{'session_id':split+str(i//4),'race_start':f'2025-01-0{i//4+1}','row_id':str(i)} for i in range(16)]
        return rows,[r['lag_1_s']+.5 for r in rows],meta
    monkeypatch.setattr(ml,'load_split',load)
    (tmp_path/'manifest.json').write_text(json.dumps(dict.fromkeys(['audit.json', 'feature_contract.json', 'train.csv', 'validation.csv', 'test.csv'], 'test-hash')))
    with threadpool_limits(limits=1):
        result=ml.run(tmp_path,tmp_path/'run')
    assert calls==['train','validation','test']
    assert len(result['test'])==2
    with pytest.raises(FileExistsError): ml.run(tmp_path,tmp_path/'run')
