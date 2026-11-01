import json

from f1_intelligence_lab.research.forward_holdout import opened_rows


def write_dataset(path,races):
    rows=[{'session_id':race,'race_start':'2026-11-%02dT12:00:00Z'%(3+index),'row_id':race+':1','target_s':90.0} for index,race in enumerate(races)]
    path.write_text('\n'.join(json.dumps(row) for row in rows)+'\n')


def test_forward_holdout_pending_below_three_races(tmp_path):
    source=tmp_path/'two.jsonl';write_dataset(source,['a','b'])
    result=json.loads((opened_rows(str(source),str(tmp_path/'pending'))/'results.json').read_text())
    assert result['status']=='forward holdout pending' and result['labels_evaluated'] is False


def test_forward_holdout_opens_three_post_boundary_races(tmp_path):
    source=tmp_path/'three.jsonl';write_dataset(source,['a','b','c'])
    result=json.loads((opened_rows(str(source),str(tmp_path/'open'))/'results.json').read_text())
    assert result['status']=='opened once' and result['verified_races']==3
