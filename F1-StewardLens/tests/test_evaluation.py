import hashlib
import json
from pathlib import Path

import pytest

from stewardlens.evaluation import (
    bias_audit_report,
    citation_integrity,
    load_cases,
    measured_agent_metrics,
    outcome_classification,
    retrieval_metrics,
    run,
    wilson_interval,
)


CASES = Path(__file__).parents[1] / "data" / "eval" / "cases.jsonl"


def test_eval_cases_are_hash_verified_and_mixed():
    cases = load_cases(CASES)
    assert any(case["synthetic"] for case in cases)
    assert any(not case["synthetic"] for case in cases)
    assert all(
        hashlib.sha256(case["incident_description"].encode()).hexdigest()
        == case["description_hash"]
        for case in cases
    )


def test_retrieval_and_small_n_classifier_are_deterministic():
    cases = load_cases(CASES)
    assert retrieval_metrics(cases) == retrieval_metrics(cases)
    first = outcome_classification(cases)
    second = outcome_classification(cases)
    assert first == second
    assert first["status"] == "feasibility-only-small-n"
    assert sum(sum(row) for row in first["confusion_matrix"]["counts"]) == len(cases)


def test_citation_integrity_requires_existing_relevant_ids():
    result = citation_integrity(
        [
            {"citation_ids": ["r1"]},
            {"citation_ids": ["unknown"]},
            {"citation_ids": []},
        ],
        ["r1", "r2"],
        ["r1"],
    )
    assert result == {"claims": 3, "passing": 1, "fraction": 1 / 3}


def test_bias_audit_has_wilson_interval_and_limitation():
    report = bias_audit_report([False, True, False, False])
    assert report["swaps"] == 4
    assert report["flip_rate"] == 0.25
    assert report["wilson_95"][0] < 0.25 < report["wilson_95"][1]
    with pytest.raises(ValueError):
        wilson_interval(2, 1)


def test_existing_agents_receive_citation_and_identity_swap_metrics():
    metrics = measured_agent_metrics()
    assert metrics["citation_integrity"]["claims"] > 0
    assert 0 <= metrics["citation_integrity"]["fraction"] <= 1
    assert metrics["bias_audit"]["swaps"] > 0
    assert metrics["bias_audit"]["wilson_95"] is not None


def test_evaluation_run_is_immutable_and_manifest_verified(tmp_path):
    output = run(CASES, tmp_path / "run")
    with pytest.raises(FileExistsError):
        run(CASES, output)
    manifest = json.loads((output / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
    assert "feasibility" in json.loads((output / "results.json").read_text())["evidence_status"]
