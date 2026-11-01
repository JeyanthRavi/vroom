import hashlib
import json
from pathlib import Path

import pytest

from f1_intelligence_lab.site_export import build, research_payload


ROOT = Path(__file__).parents[2]


def test_research_payload_is_explicitly_fixture_only():
    payload = research_payload(ROOT)
    assert payload["evidence_status"] == "fixture-only: not evidence"
    assert payload["evaluated_on"]["forward_holdout"] == "pending"
    assert payload["hazard"]["1"]["baseline_brier"] is not None


def test_site_build_is_immutable_small_and_verified(tmp_path):
    source = ROOT / "F1-Intelligence-Lab" / "demo-export-aggregate"
    output = build(source, tmp_path / "site", ROOT)
    with pytest.raises(FileExistsError):
        build(source, output, ROOT)
    manifest = json.loads((output / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
    assert sum(path.stat().st_size for path in output.iterdir()) < 1_000_000
    research = json.loads((output / "research.json").read_text())
    assert research["evidence_status"] == "fixture-only: not evidence"
    assert "Pre-registered protocol" in (output / "methodology.html").read_text()
