import json
import numpy as np
import pytest

from f1_intelligence_lab.research.drift import psi,run_fixture


def test_psi_zero_for_identical_and_positive_for_shift():
    values=np.arange(1,101,dtype=float)
    assert psi(values,values)==pytest.approx(0)
    assert psi(values,values+50)>0


def test_drift_fixture_smoke_and_determinism(tmp_path):
    first=run_fixture(str(tmp_path/'first'));second=run_fixture(str(tmp_path/'second'))
    assert (first/'results.json').read_bytes()==(second/'results.json').read_bytes()
    result=json.loads((first/'results.json').read_text())
    assert 0<=result['adversarial_validation']['grouped_auc']<=1
    assert (first/'figures/psi.alt.txt').is_file()
