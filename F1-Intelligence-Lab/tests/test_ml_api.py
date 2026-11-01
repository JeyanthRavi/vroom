import pytest
from fastapi.testclient import TestClient
from f1_intelligence_lab.app import app
from f1_intelligence_lab import ml_api


def test_disabled_without_optional_config(monkeypatch):
    monkeypatch.delenv('F1_ML_RUN',raising=False)
    assert TestClient(app).get('/api/ml/races/openf1-9149').json()['status']=='disabled'


def test_experiment_configuration_and_integrity(monkeypatch,tmp_path):
    import json
    from f1_intelligence_lab.ml_prep import digest
    client=TestClient(app)
    monkeypatch.delenv('F1_DL_RUN',raising=False)
    assert client.get('/api/ml/experiment').json()['status']=='disabled'
    result={'winner':'gru_full','coverage':{},'protocol':{},
            'scores':{'validation':{'gru_full':{'race_macro_mae_s':1.}},
                      'test':{'gru_full':{'race_macro_mae_s':2.}}},'seeds':{}}
    raw=json.dumps(result).encode()
    (tmp_path/'results.json').write_bytes(raw)
    (tmp_path/'artifact_hashes.json').write_text(json.dumps({'results.json':digest(raw)}))
    monkeypatch.setenv('F1_DL_RUN',str(tmp_path))
    response=client.get('/api/ml/experiment')
    assert response.status_code==200
    assert response.json()['models'][0]['name']=='gru_full'
    (tmp_path/'results.json').write_text('{}')
    response=client.get('/api/ml/experiment')
    assert response.status_code==503
    assert str(tmp_path) not in response.text


def test_cross_season_summary_and_integrity(monkeypatch,tmp_path):
    import json
    from f1_intelligence_lab.ml_prep import digest
    client=TestClient(app)
    monkeypatch.delenv('F1_CROSS_SEASON_RUN',raising=False)
    assert client.get('/api/ml/cross-season').json()['status']=='disabled'
    result={k:{} for k in ['coverage','races','excluded_races','scores','selected_before_2026',
                          'paired_vs_last_lap','holdout_status','limitations']}
    raw=json.dumps(result).encode()
    (tmp_path/'results.json').write_bytes(raw)
    (tmp_path/'artifact_hashes.json').write_text(json.dumps({'results.json':digest(raw)}))
    monkeypatch.setenv('F1_CROSS_SEASON_RUN',str(tmp_path))
    assert client.get('/api/ml/cross-season').json()['status']=='ready'
    (tmp_path/'results.json').write_text('{}')
    response=client.get('/api/ml/cross-season')
    assert response.status_code==503 and str(tmp_path) not in response.text
    assert client.get('/detail-assets/cross-season.js').status_code==200


def test_restart_summary_and_integrity(monkeypatch,tmp_path):
    import json
    from f1_intelligence_lab.ml_prep import digest
    client=TestClient(app)
    monkeypatch.delenv('F1_ROBUST_RUN',raising=False)
    assert client.get('/api/ml/restart-research').json()['status']=='disabled'
    result={k:{} for k in ['winner','tree_candidate','ratio','scores','coverage','stress','limitations']}
    raw=json.dumps(result).encode()
    (tmp_path/'results.json').write_bytes(raw)
    (tmp_path/'artifact_hashes.json').write_text(json.dumps({'results.json':digest(raw)}))
    monkeypatch.setenv('F1_ROBUST_RUN',str(tmp_path))
    assert client.get('/api/ml/restart-research').json()['status']=='ready'
    (tmp_path/'results.json').write_text('{}')
    response=client.get('/api/ml/restart-research')
    assert response.status_code==503 and str(tmp_path) not in response.text
    assert client.get('/detail-assets/restart.js').status_code==200


def test_missing_artifacts_fail_closed(monkeypatch):
    monkeypatch.setattr(ml_api,'SERVICE',None)
    monkeypatch.setenv('F1_ML_RUN','/nonexistent/private-run')
    monkeypatch.setenv('F1_ML_DATASET','/nonexistent/private-data')
    response=TestClient(app).get('/api/ml/races/openf1-9149')
    assert response.status_code==503
    assert '/nonexistent' not in response.text


def test_holdout_and_unverified_never_read_features():
    service=ml_api.HistoricalPredictor.__new__(ml_api.HistoricalPredictor)
    service.audit={'session_reports':[
        {'session_id':'future','split':'future_holdout','verified_for_prep':True},
        {'session_id':'bad','split':'train','verified_for_prep':False},
        {'session_id':'ok','split':'test','verified_for_prep':True}]}
    assert service.session('future')['status']=='reserved'
    assert service.session('bad')['status']=='unavailable'
    assert service.session('unknown')['status']=='unavailable'
    assert service.sessions()==[{'session_id':'ok','split':'test'}]


def test_asset_allowlist():
    client=TestClient(app)
    response=client.get('/detail-assets/ml.js')
    assert response.status_code==200
    assert 'export async function renderML' in response.text
    assert client.get('/detail-assets/selected.joblib').status_code==404


def test_corrupt_model_rejected_before_deserialization(tmp_path,monkeypatch):
    import json
    pytest.importorskip('sklearn')
    import joblib
    from f1_intelligence_lab.ml_prep import digest
    (tmp_path/'results.json').write_text('{}')
    (tmp_path/'selected.joblib').write_bytes(b'corrupt')
    (tmp_path/'artifact_hashes.json').write_text(json.dumps({
        'results.json':digest(b'{}'),'selected.joblib':'not-the-correct-hash'}))
    def forbidden(*args,**kwargs):
        pytest.fail('Must not deserialize corrupt artifact')
    monkeypatch.setattr(joblib,'load',forbidden)
    with pytest.raises(ValueError,match='checksum'):
        ml_api.HistoricalPredictor(tmp_path,tmp_path)
