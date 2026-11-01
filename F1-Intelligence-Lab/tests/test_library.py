from collections import ChainMap

import pytest
from f1_intelligence_lab.app import app
from f1_intelligence_lab.historical import track_flag
from f1_intelligence_lab.library import LapMap, Library, SessionMap
from f1_intelligence_lab.openf1_provider import Client, date, status_for_lap
from fastapi.testclient import TestClient
from telemetry_pit_crew.sample_data import demo_laps
from telemetry_pit_crew.service import TelemetryService


@pytest.mark.parametrize('compound', ['HARD', None])
@pytest.mark.parametrize('include_telemetry', [True, False])
def test_openf1_null_stint_bounds_are_skipped(tmp_path, monkeypatch, compound, include_telemetry):
    from f1_intelligence_lab.openf1_provider import import_openf1
    responses = {
        'sessions': [{'session_key': 1, 'circuit_short_name': 'Melbourne', 'date_end': '2025-03-16T10:00:00Z'}],
        'drivers': [{'driver_number': 1, 'name_acronym': 'VER'}],
        'laps': [{'driver_number': 1, 'lap_number': n, 'lap_duration': 90, 'date_start': '2025-03-16T04:00:00Z'} for n in [1, 2]],
        'stints': [{'driver_number': 1, 'lap_start': None, 'lap_end': 1},
                   {'driver_number': 1, 'lap_start': 1, 'lap_end': None},
                   {'driver_number': 1, 'lap_start': 2, 'lap_end': 2, 'compound': compound, 'stint_number': 2}],
    }
    def get(self, endpoint, **params):
        if not include_telemetry:
            assert endpoint != 'car_data'
        return responses.get(endpoint, [])
    monkeypatch.setattr(Client, 'get', get)
    lib = Library(tmp_path)
    key = import_openf1(lib, 2025, 'Melbourne', 'R', include_telemetry=include_telemetry)
    assert lib.race(key)['records'] == 1
    assert lib.race(key)['drivers'][0]['stints'][0]['compound'] == (compound or 'UNKNOWN')
    assert any('1 records missing' in warning for warning in lib.race(key)['warnings'])
    if not include_telemetry:
        assert lib.session(key)['telemetry_status'] == 'not_requested'
        assert lib.session(key)['unavailable_drivers'] == []
        fixture_session(lib, key)
        with pytest.raises(ValueError, match='cannot replace existing telemetry'):
            import_openf1(lib, 2025, 'Melbourne', 'R', include_telemetry=False)


def fixture_session(lib, key='saved'):
    laps=[lap.model_copy(update={'id':key+'-'+lap.id}) for lap in demo_laps().values()]
    metadata={'id':key,'name':key,'source_type':'test_recorded'}
    lib.store(metadata,laps,{'records':3,'session_id':key})
    return laps


def test_persistence_lazy_maps_and_summaries(tmp_path):
    lib=Library(tmp_path)
    laps=fixture_session(lib)
    restored=Library(tmp_path)
    assert restored.race('saved')['records']==3
    assert SessionMap(restored)['saved']['cached'] is True
    assert LapMap(restored)[laps[0].id].model_dump()==laps[0].model_dump()
    assert 'samples' not in restored.lap_summaries('saved')[0]
    assert len(restored.sessions())==1
    with pytest.raises(KeyError): restored.race('unknown')
    with pytest.raises(KeyError): restored.lap('unknown')


def test_reimport_is_atomic_and_replaces_only_target(tmp_path):
    lib=Library(tmp_path);old=fixture_session(lib);fixture_session(lib,'other')
    lib.store({'id':'saved'},[old[0]],{'records':1})
    assert len(lib.lap_summaries('saved'))==1
    assert len(lib.lap_summaries('other'))==2
    with pytest.raises(KeyError):lib.lap(old[1].id)
    bad=old[0].model_copy(update={'lap_time':float('nan')})
    with pytest.raises(ValueError):lib.store({'id':'saved'},[bad])
    assert lib.lap(old[0].id).lap_time==old[0].lap_time
    assert lib.race('saved')['records']==1


def test_shared_service_summaries_do_not_read_telemetry(tmp_path,monkeypatch):
    lib=Library(tmp_path);fixture_session(lib)
    service=TelemetryService()
    service.sessions=ChainMap(service.sessions,SessionMap(lib))
    service.laps=ChainMap(service.laps,LapMap(lib))
    service.external_summaries=lib.lap_summaries
    monkeypatch.setattr(lib,'lap',lambda key: (_ for _ in ()).throw(AssertionError('Loaded telemetry')))
    assert len(service.list_lap_summaries('saved'))==2
    assert len(service.list_lap_summaries())>=4


def test_flags_are_conservative_and_span_lap_boundary():
    events=[{'date':'2024-01-01T10:00:00+00:00','message':'SESSION STARTED'},
            {'date':'2024-01-01T10:02:00+00:00','message':'SAFETY CAR DEPLOYED'},
            {'date':'2024-01-01T10:05:00+00:00','flag':'GREEN','scope':'Track'}]
    assert status_for_lap(date('2024-01-01T10:01:00+00:00'),date('2024-01-01T10:03:00+00:00'),events)=='SC'
    assert status_for_lap(date('2024-01-01T10:04:00+00:00'),date('2024-01-01T10:06:00+00:00'),events)=='SC'
    assert status_for_lap(date('2024-01-01T10:06:00+00:00'),date('2024-01-01T10:07:00+00:00'),events)=='GREEN'
    assert status_for_lap(date('2024-01-01T10:06:00+00:00'),date('2024-01-01T10:07:00+00:00'),[])=='UNKNOWN'
    assert track_flag('12')=='UNKNOWN'
    assert track_flag('14')=='SC'
    assert track_flag('16')=='VSC'


def test_import_queue_and_failure_recovery(tmp_path,monkeypatch):
    import f1_intelligence_lab.library_api as api
    lib=Library(tmp_path);monkeypatch.setattr(api,'library',lib)
    monkeypatch.setattr(api,'run_worker',lambda key:None)
    monkeypatch.setenv('F1_ADMIN_TOKEN','test-token')
    client=TestClient(app,headers={'x-f1-admin-token':'test-token'})
    args={'provider':'openf1','year':2024,'event':'Monza','session_code':'R'}
    first=client.post('/api/library/import',json=args)
    assert first.status_code==202
    key=first.json()['id']
    assert client.post('/api/library/import',json=args).json()['id']==key
    assert client.post('/api/library/import',json=dict(args,event='Silverstone')).status_code==409
    lib.update_job(key,'failed','Provider error')
    assert client.post('/api/library/import',json=args).json()['id']!=key
    assert client.post('/api/library/import',json=dict(args,event='https://evil.example')).status_code==422
    assert client.get('/api/library/races/missing').status_code==404


def test_import_is_disabled_without_admin_configuration(monkeypatch):
    monkeypatch.delenv('F1_ADMIN_TOKEN',raising=False)
    monkeypatch.delenv('F1_ALLOW_LOCAL_IMPORT',raising=False)
    args={'provider':'openf1','year':2024,'event':'Monza','session_code':'R'}
    response=TestClient(app).post('/api/library/import',json=args)
    assert response.status_code==403
    assert 'disabled' in response.json()['detail'].lower()


def test_cross_session_comparison_rejected(tmp_path):
    service=TelemetryService();lib=Library(tmp_path);laps=fixture_session(lib)
    service.sessions=ChainMap(service.sessions,SessionMap(lib));service.laps=ChainMap(service.laps,LapMap(lib))
    with pytest.raises(ValueError,match='same session'):
        service.compare('demo-A',laps[0].id)


def test_worker_timeout_reports_failure(tmp_path,monkeypatch):
    import subprocess

    import f1_intelligence_lab.library_api as api
    lib=Library(tmp_path);monkeypatch.setattr(api,'library',lib)
    with lib.connect() as db:
        db.execute("INSERT INTO jobs(id,state,message,request) VALUES('test','queued','waiting','{}')")
    def timeout(*args,**kwargs):raise subprocess.TimeoutExpired('worker',900)
    monkeypatch.setattr(api.subprocess,'run',timeout)
    api.run_worker('test')
    assert lib.job('test')['state']=='failed'
    assert '15 minutes' in lib.job('test')['message']


def test_sector_yellow_and_clear():
    events=[{'date':'2024-01-01T10:00:00+00:00','message':'SESSION STARTED'},
            {'date':'2024-01-01T10:01:00+00:00','flag':'YELLOW','sector':2},
            {'date':'2024-01-01T10:02:00+00:00','flag':'CLEAR','sector':2}]
    assert status_for_lap(date('2024-01-01T10:00:30+00:00'),date('2024-01-01T10:02:30+00:00'),events)=='UNKNOWN'
    assert status_for_lap(date('2024-01-01T10:03:00+00:00'),date('2024-01-01T10:04:00+00:00'),events)=='GREEN'


def test_sc_ending_is_not_assumed_green_or_sc_forever():
    events=[{'date':'2024-01-01T10:00:00+00:00','message':'SAFETY CAR DEPLOYED'},
            {'date':'2024-01-01T10:01:00+00:00','message':'SAFETY CAR IN THIS LAP'}]
    assert status_for_lap(date('2024-01-01T10:02:00+00:00'),date('2024-01-01T10:03:00+00:00'),events)=='UNKNOWN'
