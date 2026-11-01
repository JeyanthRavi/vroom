import json

import pytest

pytest.importorskip('torch')
from f1_intelligence_lab import cross_season as cs
from f1_intelligence_lab.ml_dataset import load_split
from f1_intelligence_lab.ml_prep import digest


def test_default_holdout_guard_remains(tmp_path):
    with pytest.raises(ValueError,match='reserved'):
        load_split(tmp_path,'future_holdout')
    with pytest.raises(FileNotFoundError):
        load_split(tmp_path,'future_holdout',allow_future_evaluation=True)
    with pytest.raises(ValueError):
        load_split(tmp_path,'arbitrary',allow_future_evaluation=True)


def test_race_bootstrap_is_paired_and_deterministic():
    a={'per_race':{'a':{'mae_s':1.},'b':{'mae_s':2.}}}
    b={'per_race':{'a':{'mae_s':3.},'b':{'mae_s':4.}}}
    r=cs.paired_race_interval(a,b)
    assert r==cs.paired_race_interval(a,b)
    assert r['mean_delta_s']==-2. and r['ci95_s']==[-2.,-2.]
    assert r['races_better']==2


def test_freeze_precedes_holdout_access(tmp_path,monkeypatch):
    dataset=tmp_path/'data'; dataset.mkdir(); (dataset/'manifest.json').write_text('{}')
    old={'original_manifest_sha256':digest(b'{}'),'winner':'boosting_sequence'}
    monkeypatch.setattr(cs,'verify_artifacts',lambda run:(old,{'weights':'frozen'}))
    output=tmp_path/'evaluation'
    def intercept(*args,**kwargs):
        p=json.loads((output/'protocol.json').read_text())
        assert p['selected_before_2026']=='boosting_sequence'
        assert p['artifact_hashes']=={'weights':'frozen'}
        assert kwargs=={'allow_future_evaluation':True}
        raise RuntimeError('checked before labels')
    monkeypatch.setattr(cs,'build_split',intercept)
    with pytest.raises(RuntimeError,match='checked before labels'):
        cs.run(dataset,tmp_path,tmp_path,output)


def test_bad_artifact_rejected_before_load(tmp_path):
    (tmp_path/'artifact_hashes.json').write_text('{"results.json":"wrong"}')
    (tmp_path/'results.json').write_text('{}')
    with pytest.raises(ValueError,match='checksum'):
        cs.verify_artifacts(tmp_path)
