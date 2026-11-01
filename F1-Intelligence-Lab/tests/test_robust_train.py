from copy import deepcopy

import pytest

pytest.importorskip('torch')
from f1_intelligence_lab.ml_prep import FEATURES
from f1_intelligence_lab.robust_train import interrupted, neural_view, only_2025, transform


def data():
    x=dict.fromkeys(FEATURES, 1.0)
    x.update(circuit='TEST',lag_1_s=90.,lag_2_s=90.,lag_3_s=90.,previous_compound='MEDIUM',control_state_at_cutoff='GREEN')
    seq=[{'pace_delta_s':0.,'lap_number':i+1,'compound':'MEDIUM','tyre_age':i+1,'stint_lap':i+1,'pit_out':0,'control_state':'GREEN'} for i in range(10)]
    return {'x':[x],'sequences':[seq],'y':[91.],'meta':[{'session_id':'test'}]}


def test_long_lap_does_not_become_prediction_anchor():
    original=data();stress=interrupted(original);out=transform(stress,2.)
    assert stress['x'][0]['lag_1_s']==900.
    assert out['x'][0]['lag_1_s']==90.
    assert out['x'][0]['previous_long_lap']==1
    assert out['sequences'][0][-1]['long_lap']==1
    assert original==data()
    assert out['y']==original['y']


def test_transform_ignores_target_and_preserves_labels():
    a=data();b=deepcopy(a);b['y']=[2200.]
    assert transform(a,1.5)['x']==transform(b,1.5)['x']
    assert transform(b,1.5)['y']==[2200.]
    view=neural_view(transform(b,1.5))
    assert set(view['x'][0])==set(FEATURES)
    assert 'previous_long_lap' in view['sequences'][0][0]


def test_restart_flag_uses_known_history_and_current_state():
    d=data();d['sequences'][0][-1]['control_state']='RED'
    assert transform(d,2.)['x'][0]['restart_state_transition']==1
    d['x'][0]['control_state_at_cutoff']='UNKNOWN'
    assert transform(d,2.)['x'][0]['restart_state_transition']==0


def test_multiple_interruptions_and_invalid_history():
    d=data()
    for s in d['sequences'][0][-4:]:s['pace_delta_s']=2000.
    assert transform(d,2.)['x'][0]['lag_1_s']==90.
    d['sequences'][0][0]['pace_delta_s']=float('nan')
    with pytest.raises(ValueError):transform(d,2.)


def test_only_2025_training_rows_survive():
    d=data();d['meta'][0]['race_start']='2024-01-01'
    with pytest.raises(ValueError):only_2025(d)
    d['meta'][0]['race_start']='2025-01-01'
    assert only_2025(d)['coverage']['eligible_rows']==1
    d['meta'][0]['race_start']='2026-01-01'
    with pytest.raises(ValueError):only_2025(d)


def test_saved_model_integrity_checked_before_loading(tmp_path,monkeypatch):
    import json

    import joblib
    from f1_intelligence_lab.ml_prep import digest
    from f1_intelligence_lab.robust_train import predict_saved
    selection=json.dumps({'tree_candidate':'tree','ratio':2.}).encode()
    (tmp_path/'selection.json').write_bytes(selection)
    (tmp_path/'tree.joblib').write_bytes(b'corrupt')
    (tmp_path/'artifact_hashes.json').write_text(json.dumps({'selection.json':digest(selection),'tree.joblib':'wrong'}))
    def forbidden(*args,**kwargs):pytest.fail('Corrupt model must not deserialize')
    monkeypatch.setattr(joblib,'load',forbidden)
    with pytest.raises(ValueError,match='integrity'):
        predict_saved(tmp_path,data(),'robust_tree')
