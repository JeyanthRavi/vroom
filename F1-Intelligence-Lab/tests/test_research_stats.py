
import pytest
from f1_intelligence_lab.research.stats import (
    expected_calibration_error,
    interval_score,
    paired_race_bootstrap,
    reliability_bins,
    wilson,
)


def test_paired_bootstrap_is_deterministic_and_uses_races():
    first=paired_race_bootstrap([-1,0.5,-0.25],resamples=1000,seed=7)
    assert first==paired_race_bootstrap([-1,0.5,-0.25],resamples=1000,seed=7)
    assert first['races']==3 and first['wins']==2


def test_wilson_matches_known_half_success_interval():
    low,high=wilson(5,10)
    assert low==pytest.approx(0.2366,abs=1e-3)
    assert high==pytest.approx(0.7634,abs=1e-3)


def test_reliability_and_ece_hand_example():
    rows=reliability_bins([0,1],[0.2,0.8],bins=2)
    assert len(rows)==2
    assert expected_calibration_error([0,1],[0.2,0.8])==pytest.approx(0.2)


def test_interval_score_hand_example_and_invalid_bounds():
    assert interval_score([1,3],[0,0],[2,2],alpha=0.2)==pytest.approx(7.0)
    with pytest.raises(ValueError):interval_score([1],[2],[0],0.2)
