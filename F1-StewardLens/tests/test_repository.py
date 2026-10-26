import json

import pytest

from stewardlens.repository import (
    JsonRepository,
    RecordNotFoundError,
    RepositoryError,
    get_incident_packet,
    list_incidents,
)


def test_default_repository_loads_complete_sample_dataset():
    repository = JsonRepository()

    incidents = repository.list_incidents()

    assert len(incidents) >= 3
    assert all("fictional" in incident.event.lower() for incident in incidents)
    assert all(repository.get_evidence(incident.id) for incident in incidents)


def test_incident_packet_contains_ranked_context():
    repository = JsonRepository()

    packet = repository.get_incident_packet("sample-northstar-2026-03")

    assert packet.incident.id == "sample-northstar-2026-03"
    assert len(packet.evidence) == 3
    assert packet.regulations[0].id == "sample-rule-2026-5.3"
    assert "sample-northstar-2026-03" not in packet.precedent_ids


def test_unknown_incident_raises_clear_error():
    with pytest.raises(RecordNotFoundError, match="Unknown incident"):
        JsonRepository().get_incident("missing-case")


def test_module_level_repository_boundary_supports_api_and_agents():
    incidents = list_incidents()

    assert incidents
    assert get_incident_packet(incidents[0].id).incident == incidents[0]


def test_repository_rejects_missing_evidence_reference(tmp_path):
    incident = {
        "id": "broken",
        "season": 2026,
        "event": "Fictional",
        "session": "Race",
        "lap": 1,
        "driver_a": "A",
        "driver_b": "B",
        "category": "collision",
        "summary": "Sample",
        "evidence_ids": ["missing"],
    }
    (tmp_path / "incidents.json").write_text(json.dumps([incident]))
    (tmp_path / "evidence.json").write_text("[]")
    (tmp_path / "regulations.json").write_text("[]")

    with pytest.raises(RepositoryError, match="missing evidence"):
        JsonRepository(tmp_path)

