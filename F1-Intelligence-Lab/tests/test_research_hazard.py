import json

import pytest

pytest.importorskip("torch")

from f1_intelligence_lab.research.hazard import run_fixture


def test_hazard_fixture_smoke_and_determinism(tmp_path):
    first = run_fixture(str(tmp_path / "first"))
    second = run_fixture(str(tmp_path / "second"))
    assert (first / "results.json").read_bytes() == (second / "results.json").read_bytes()
    result = json.loads((first / "results.json").read_text())
    assert result["fixture_only"] is True
    assert result["hazard"]["1"]["boosting"]["rows"] > 0
    assert result["hazard"]["1"]["small_tcn"]["rows"] > 0
    assert result["hazard"]["1"]["small_tcn"]["breakdowns"]["race_id"]
    assert result["hazard"]["1"]["small_tcn"]["breakdowns"]["circuit"]
    assert (first / "manifest.json").is_file()
    assert (first / "predictions.csv").is_file()
