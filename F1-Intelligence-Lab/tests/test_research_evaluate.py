import pytest

from f1_intelligence_lab.research.evaluate import assert_no_leakage, fixture_rows


def test_fixture_is_deterministic_whole_race_and_cutoff_safe():
    rows=fixture_rows();assert rows==fixture_rows();assert_no_leakage(rows)
    assert {row['split'] for row in rows}=={'train','validation','test'}


def test_leakage_and_cross_split_guards_fail_closed():
    rows=fixture_rows();rows[0]['feature_latest_order']=rows[0]['cutoff_order']+1
    with pytest.raises(ValueError,match='cutoff'):assert_no_leakage(rows)
    rows=fixture_rows();rows[0]['split']='test'
    with pytest.raises(ValueError,match='partitions'):assert_no_leakage(rows)
