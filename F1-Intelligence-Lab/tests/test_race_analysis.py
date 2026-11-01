import pytest
from fastapi.testclient import TestClient
from f1_intelligence_lab.app import app
from f1_intelligence_lab.race_analysis import analyze, parse_csv, demo_csv

client = TestClient(app)
HEADER = "driver,lap,lap_time,compound,stint,pit,flag\n"


def test_demo_and_assets():
    response = client.get('/api/races/demo')
    assert response.status_code == 200
    d = response.json()
    assert d['source_type'] == 'synthetic'
    assert d['records'] == 90
    assert len(d['drivers']) == 3
    assert d['drivers'][0]['pit_laps'] == [12]
    assert len(d['sha256']) == 64
    for path in ['/race-lab/', '/race-assets/race.css', '/race-assets/race.js']:
        assert client.get(path).status_code == 200
    assert client.get('/race-assets/app.py').status_code == 404
    assert client.get('/api/races/template').text == demo_csv()


def test_clean_laps_median_and_trend():
    text = HEADER + '\n'.join(f'AAA,{lap},{time},MEDIUM,1,{pit},{flag}' for lap,time,pit,flag in [
        (1,100,0,'GREEN'), (2,80,0,'GREEN'), (3,81,0,'GREEN'), (4,82,0,'GREEN'),
        (5,110,1,'GREEN'),(6,90,0,'GREEN'),(7,120,0,'SC'),(8,120,0,'VSC'),(9,120,0,'RED'),(10,120,0,'UNKNOWN')])
    d = analyze(text)['drivers'][0]
    assert d['clean_laps'] == 3
    assert d['excluded_laps'] == 7
    assert d['median'] == 81
    assert d['fastest'] == 80
    assert d['stints'][0]['trend'] == 1


def test_sparse_and_no_clean_laps():
    d = analyze(HEADER + 'AAA,3,100,HARD,1,0,SC\n')
    assert d['drivers'][0]['median'] is None
    assert d['drivers'][0]['stints'][0]['trend'] is None
    assert d['drivers'][0]['missing_laps'] == [1,2]
    assert len(d['warnings']) == 2


@pytest.mark.parametrize('row',[
    'AAA,1,nan,HARD,1,0,GREEN', 'AAA,1,inf,HARD,1,0,GREEN',
    'AAA,0,80,HARD,1,0,GREEN', 'AAA,1,-80,HARD,1,0,GREEN',
    'AAA,1,80,FAKE,1,0,GREEN', 'AAA,1,80,HARD,1,2,GREEN',
    '<script>,1,80,HARD,1,0,GREEN', 'AAA,1,80,HARD,1,0,BAD',
    'AAA,1,80,HARD,1,0', 'AAA,1,80,HARD,1,0,GREEN,EXTRA',
])
def test_bad_rows_rejected(row):
    with pytest.raises(ValueError):
        parse_csv(HEADER + row)


def test_duplicates_and_stints_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        parse_csv(HEADER + 'AAA,1,80,HARD,1,0,GREEN\n'*2)
    with pytest.raises(ValueError, match='compound changes'):
        parse_csv(HEADER + 'AAA,1,80,HARD,1,0,GREEN\nAAA,2,81,SOFT,1,0,GREEN')
    with pytest.raises(ValueError, match='must not decrease'):
        parse_csv(HEADER + 'AAA,1,80,HARD,2,0,GREEN\nAAA,2,81,SOFT,1,0,GREEN')


def test_headers_empty_size_and_bom():
    for text in ['', HEADER, 'driver,time\nAAA,80', 'x'*500001]:
        with pytest.raises(ValueError):
            parse_csv(text)
    assert len(parse_csv('\ufeff'+demo_csv())) == 90


def test_import_does_not_mutate_demo():
    before = client.get('/api/races/demo').json()
    response = client.post('/api/races/analyze', json={'name':'My race','csv':HEADER+'AAA,2,88,HARD,1,0,GREEN'})
    assert response.status_code == 200
    assert response.json()['source_type'] == 'user_import'
    assert response.json()['name'] == 'My race'
    assert client.get('/api/races/demo').json() == before
    assert client.post('/api/races/analyze', json={'csv':'invalid'}).status_code == 422


def test_http_import_enforces_documented_500kb_limit():
    assert client.post('/api/races/analyze',json={'csv':'x'*500_001}).status_code==422


def test_input_order_does_not_change_analysis_and_sparse_slope():
    records = ['AAA,2,80,HARD,1,0,GREEN','AAA,4,82,HARD,1,0,GREEN','AAA,8,86,HARD,1,0,GREEN']
    a = analyze(HEADER+'\n'.join(records))
    b = analyze(HEADER+'\n'.join(reversed(records)))
    assert a['drivers'] == b['drivers']
    assert a['drivers'][0]['stints'][0]['trend'] == 1
