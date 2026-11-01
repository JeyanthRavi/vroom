import json

import pytest
from stewardlens.agents import CitationValidationError
from stewardlens.contracts import AgentFinding
from stewardlens.model_agent import EnvironmentModelAgent, MockModelAgent
from stewardlens.repository import get_incident_packet


def test_mock_model_agent_is_offline_and_grounded():
    packet = get_incident_packet("sample-aurora-2026-01")
    finding = MockModelAgent().analyze(packet)
    assert finding.evidence_ids[0] in {item.id for item in packet.evidence}
    assert finding.regulation_ids[0] in {item.id for item in packet.regulations}


def test_environment_agent_requires_key(monkeypatch):
    monkeypatch.delenv("STEWARDLENS_MODEL_API_KEY", raising=False)
    agent = EnvironmentModelAgent(provider=lambda _: "{}")
    with pytest.raises(RuntimeError, match="not configured"):
        agent.analyze(get_incident_packet("sample-aurora-2026-01"))


def test_environment_agent_logs_and_enforces_citations(tmp_path, monkeypatch):
    packet = get_incident_packet("sample-aurora-2026-01")
    monkeypatch.setenv("STEWARDLENS_MODEL_API_KEY", "test-only-placeholder")
    invalid = AgentFinding(
        agent="provider",
        position="test",
        claims=["claim"],
        evidence_ids=["not-in-packet"],
        confidence=0.5,
    )
    agent = EnvironmentModelAgent(provider=lambda _: invalid.model_dump_json(), log_directory=tmp_path)
    with pytest.raises(CitationValidationError):
        agent.analyze(packet)
    assert not (tmp_path / "model-agent.jsonl").exists()

    valid = invalid.model_copy(update={"evidence_ids": [packet.evidence[0].id]})
    agent.provider = lambda _: valid.model_dump_json()
    assert agent.analyze(packet).evidence_ids == [packet.evidence[0].id]
    record = json.loads((tmp_path / "model-agent.jsonl").read_text().splitlines()[0])
    assert "prompt" in record and "output" in record
