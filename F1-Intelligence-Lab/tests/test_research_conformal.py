import json

import numpy as np
from f1_intelligence_lab.research.conformal import conformal_quantile, run_fixture


def test_conformal_quantile_uses_higher_finite_sample_rule():
    assert conformal_quantile(np.asarray([1.,2.,3.,4.]),0.2)==4


def test_conformal_fixture_smoke_and_determinism(tmp_path):
    first=run_fixture(str(tmp_path/'first'));second=run_fixture(str(tmp_path/'second'))
    assert (first/'results.json').read_bytes()==(second/'results.json').read_bytes()
    result=json.loads((first/'results.json').read_text())
    assert set(result['methods'])=={'split_80','split_90','cqr_80','cqr_90'}
    assert result['mondrian']['status']=='unsupported'
