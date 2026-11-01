import pytest

pytest.importorskip('torch')
import joblib
import numpy as np
import torch
from f1_intelligence_lab import dl_train as dl
from f1_intelligence_lab.ml_prep import FEATURES
from f1_intelligence_lab.ml_train import save_json


def fixture_data():
    x=[]; sequences=[]
    for _i in range(12):
        row=dict.fromkeys(FEATURES, 1.0)
        row.update(circuit='TRAIN_ONLY',previous_compound='MEDIUM',control_state_at_cutoff='GREEN',lag_1_s=90.)
        x.append(row)
        sequences.append([{'pace_delta_s':0.,'lap_number':n,'compound':'MEDIUM','tyre_age':n,'stint_lap':n,'pit_out':0,'control_state':'GREEN'} for n in range(1,11)])
    return {'x':x,'sequences':sequences,'y':[90.5]*12,'meta':[{'session_id':str(i//4),'race_start':str(i//4)} for i in range(12)]}


def test_encoder_fitted_only_on_training_and_ablation_removes_fields():
    data=fixture_data(); seq,ctx,enc=dl.encode(data,'no_tyre')
    assert seq.shape[:2]==(12,10)
    for e in enc:
        assert not any('compound' in n or 'tyre_age' in n or 'stint_lap' in n for n in e[0].get_feature_names_out())
    data['x'][0]['circuit']='UNSEEN'; data['sequences'][0][0]['control_state']='NEW'
    dl.encode(data,'no_tyre',enc)
    assert 'circuit=UNSEEN' not in enc[1][0].vocabulary_


def test_deterministic_training_and_checkpoint_reload(tmp_path,monkeypatch):
    torch.set_num_threads(1)
    monkeypatch.setitem(dl.PROTOCOL,'epochs',2)
    data=fixture_data()
    a,enc,info=dl.train_gru(data,data,'full',11)
    b,enc2,_=dl.train_gru(data,data,'full',11)
    predicted=dl.infer_gru(a,dl.encode(data,'full',enc),data)
    np.testing.assert_array_equal(predicted,dl.infer_gru(b,dl.encode(data,'full',enc2),data))
    assert not np.all(predicted==90.)
    torch.save(a.state_dict(),tmp_path/'gru_full_11.pt')
    joblib.dump(enc,tmp_path/'gru_full_11_encoders.joblib')
    save_json(tmp_path/'gru_full_11.json',info)
    np.testing.assert_array_equal(predicted,dl.predict_bundle(tmp_path,'full',11,data))


def test_each_race_has_equal_total_training_weight():
    meta=[{'session_id':'a'}]*3+[{'session_id':'b'}]
    w=dl.race_weights(meta)
    assert np.isclose(w[:3].sum(),w[3])
