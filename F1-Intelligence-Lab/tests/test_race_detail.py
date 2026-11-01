import pytest
from f1_intelligence_lab.library import Library
from f1_intelligence_lab import race_detail as detail

def test_fia_parser_rejects_wrong_year_event_and_host():
    parser=detail.Documents('2025 italian grand prix')
    parser.feed('''<a href="/system/files/decision-document/2025_italian_grand_prix_-_decision.pdf">Doc 1 - Decision</a>
    <a href="https://evil.example/decision-document/2025_italian_grand_prix_x.pdf">Bad</a>
    <a href="/system/files/decision-document/2024_italian_grand_prix_x.pdf">Old</a>
    <a href="/system/files/decision-document/2025_monaco_grand_prix_x.pdf">Other</a>''')
    assert len(parser.rows)==1
    assert next(iter(parser.rows.values()))['title']=='Doc 1 - Decision'

def test_detail_partial_failure_preserves_real_sections(tmp_path,monkeypatch):
    lib=Library(tmp_path)
    lib.store({'id':'openf1-1','event':'Monza','year':2025},[],{'records':12})
    def get(self,endpoint,**kwargs):
        if endpoint=='session_result': raise ValueError('Missing classification')
        return [{'driver_number':44}]
    monkeypatch.setattr(detail.Client,'get',get)
    monkeypatch.setattr(detail,'fia_documents',lambda meta:([], 'https://www.fia.com/documents'))
    result=detail.build(lib,'openf1-1')
    assert result['sections']['results']['status']=='unavailable'
    assert result['sections']['results']['rows']==[]
    assert result['sections']['pit_stops']['rows']==[{'driver_number':44}]
    assert detail.saved(lib,'openf1-1')==result
    assert lib.race('openf1-1')=={'records':12}
    with pytest.raises(KeyError): detail.saved(lib,'unknown')

def test_unknown_fia_event_not_guessed():
    with pytest.raises(ValueError,match='mapping'):
        detail.fia_documents({'event':'Kuala Lumpur','year':2026})

def test_accented_fia_event_matches_ascii_filename():
    parser=detail.Documents('2025 são paulo grand prix')
    parser.feed('<a href="/system/files/decision-document/2025_sao_paulo_grand_prix_-_decision.pdf">Decision</a>')
    assert len(parser.rows)==1

def test_routes_are_read_only_until_explicit_load(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from f1_intelligence_lab.app import app
    lib=Library(tmp_path)
    lib.store({'id':'openf1-1','event':'Monza','year':2025},[],{'records':12})
    monkeypatch.setattr(detail,'library',lib)
    monkeypatch.setenv('F1_ADMIN_TOKEN','test-token')
    client=TestClient(app,headers={'x-f1-admin-token':'test-token'})
    assert client.get('/api/race-details/openf1-1').json()['state']=='not_loaded'
    assert client.get('/api/race-details/missing').status_code==404
    assert client.post('/api/race-details/missing/load').status_code==404
    assert client.get('/detail-assets/nope').status_code==404
    assert client.get('/race-detail/').status_code==200
    detail.LOCK.acquire()
    try: assert client.post('/api/race-details/openf1-1/load').status_code==409
    finally: detail.LOCK.release()

def test_detail_load_is_disabled_without_admin_configuration(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from f1_intelligence_lab.app import app
    lib=Library(tmp_path);lib.store({'id':'openf1-1','event':'Monza','year':2025},[],{})
    monkeypatch.setattr(detail,'library',lib)
    monkeypatch.delenv('F1_ADMIN_TOKEN',raising=False)
    monkeypatch.delenv('F1_ALLOW_LOCAL_IMPORT',raising=False)
    assert TestClient(app).post('/api/race-details/openf1-1/load').status_code==403
