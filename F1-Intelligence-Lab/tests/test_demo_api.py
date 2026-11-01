import json
import hashlib
from fastapi.testclient import TestClient
from f1_intelligence_lab.demo_app import app

def package(tmp_path,monkeypatch,legacy=False,mode='aggregate'):
    content={
        'index.html':'<html>replay</html>','methodology.html':'<html>method</html>',
        'demo.js':'// replay','data.json':'{}','research.json':'{}',
    }
    for n,v in content.items():(tmp_path/n).write_text(v)
    files={n:hashlib.sha256(v.encode()).hexdigest() for n,v in content.items()}
    manifest=files if legacy else {'schema':2,'export_mode':mode,'files':files}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    monkeypatch.setenv('F1_DEMO_EXPORT',str(tmp_path))

def test_replay_and_health(tmp_path,monkeypatch):
    package(tmp_path,monkeypatch);client=TestClient(app)
    assert client.get('/').status_code==200
    assert client.get('/health').json()['mode']=='historical_replay'
    assert client.get('/model-demo/data.json').json()=={}
    assert client.get('/model-demo/research.json').json()=={}
    assert client.get('/model-demo/methodology.html').status_code==200
    assert 'nosniff'==client.get('/model-demo/demo.js').headers['x-content-type-options']
    assert client.get('/api/library/import').status_code==404
    assert client.get('/model-demo/manifest.json').status_code==404
    metadata=client.get('/model-demo/export-metadata.json').json()
    assert metadata['export_mode']=='aggregate' and metadata['version']=='legacy'
    assert client.get('/model-demo/data.json').headers['referrer-policy']=='no-referrer'

def test_legacy_manifest_is_labelled_full(tmp_path,monkeypatch):
    package(tmp_path,monkeypatch,legacy=True)
    assert TestClient(app).get('/model-demo/export-metadata.json').json()=={
        'manifest_schema':1,'export_mode':'legacy_full','version':'legacy','git_commit':'unknown'}

def test_corrupt_export_fails_closed(tmp_path,monkeypatch):
    package(tmp_path,monkeypatch);(tmp_path/'data.json').write_text('corrupt')
    r=TestClient(app).get('/model-demo/data.json')
    assert r.status_code==503 and str(tmp_path) not in r.text
    assert TestClient(app).get('/health').status_code==503

def test_missing_export_disabled(monkeypatch):
    monkeypatch.delenv('F1_DEMO_EXPORT',raising=False)
    assert TestClient(app).get('/model-demo/').status_code==503


def test_rollback_to_verified_package(tmp_path,monkeypatch):
    package(tmp_path,monkeypatch)
    client=TestClient(app)
    assert client.get('/health').status_code==200
    monkeypatch.setenv('F1_DEMO_EXPORT',str(tmp_path/'missing-release'))
    assert client.get('/health').status_code==503
    monkeypatch.setenv('F1_DEMO_EXPORT',str(tmp_path))
    assert client.get('/health').status_code==200
