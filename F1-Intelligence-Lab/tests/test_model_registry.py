import json

import pytest

from f1_intelligence_lab.model_registry import register


def test_registry_defaults_to_staging_and_never_auto_promotes(tmp_path):
    path = tmp_path / "registry.json"
    assert register(path, {"run": "one"})[-1]["status"] == "staging"
    assert json.loads(path.read_text())[0]["status"] == "staging"
    with pytest.raises(ValueError, match="status"):
        register(path, {"run": "two", "status": "production"})
