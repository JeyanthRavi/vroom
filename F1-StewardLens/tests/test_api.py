from __future__ import annotations

import pytest
import stewardlens.api as api
from fastapi.testclient import TestClient
from stewardlens.contracts import (
    AgentFinding,
    EvidenceItem,
    EvidencePacket,
    Incident,
    RegulationClause,
    Verdict,
)
from stewardlens.repository import RecordNotFoundError


@pytest.fixture
def packet() -> EvidencePacket:
    incident = Incident(
        id="sample-incident",
        season=2024,
        event="Sample Grand Prix",
        session="Race",
        lap=12,
        driver_a="AAA",
        driver_b="BBB",
        category="causing_a_collision",
        summary="The cars made contact while contesting the same corner.",
        evidence_ids=["evidence-1"],
        official_decision="penalty",
        official_penalty="time_penalty",
    )
    return EvidencePacket(
        incident=incident,
        evidence=[
            EvidenceItem(
                id="evidence-1",
                kind="fact",
                summary="Contact occurred at the apex.",
                source="verified sample dataset",
                quality=0.95,
            )
        ],
        regulations=[
            RegulationClause(
                id="reg-1",
                season=2024,
                article="33.4",
                title="Driving standards",
                text="A short fixture clause.",
                source="fixture://regulation",
            )
        ],
    )


@pytest.fixture
def verdict() -> Verdict:
    finding = AgentFinding(
        agent="evidence",
        position="neutral",
        claims=["Contact occurred at the apex."],
        evidence_ids=["evidence-1"],
        regulation_ids=[],
        confidence=0.9,
    )
    return Verdict(
        incident_id="sample-incident",
        decision="penalty",
        penalty_category="time_penalty",
        confidence=0.82,
        findings=["Driver AAA was predominantly responsible."],
        evidence_citations=["evidence-1"],
        regulation_citations=["reg-1"],
        dissenting_interpretation="Both drivers were entitled to contest the corner.",
        missing_evidence=[],
        agent_outputs={"evidence": finding},
    )


@pytest.fixture(autouse=True)
def isolated_run_store() -> None:
    api.run_store.clear()
    yield
    api.run_store.clear()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, packet: EvidencePacket) -> TestClient:
    monkeypatch.setattr(api, "list_incidents", lambda: [packet.incident])
    monkeypatch.setattr(
        api,
        "get_incident_packet",
        lambda incident_id: packet if incident_id == packet.incident.id else None,
    )
    return TestClient(api.app)


def test_home_serves_browser_interface(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "StewardLens" in response.text
    assert "Run agent deliberation" in response.text


def test_lists_incidents_and_returns_evidence(client: TestClient) -> None:
    incidents = client.get("/incidents")
    evidence = client.get("/incidents/sample-incident/evidence")

    assert incidents.status_code == 200
    assert incidents.json()[0]["id"] == "sample-incident"
    assert evidence.status_code == 200
    assert evidence.json()["evidence"][0]["id"] == "evidence-1"


def test_verified_fia_decisions_are_exposed(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api,
        "list_real_decisions",
        lambda: [
            {
                "id": "fia-example",
                "source_document_url": "https://api.fia.com/example.pdf",
                "sha256": "a" * 64,
            }
        ],
    )
    response = client.get("/fia-decisions")
    assert response.status_code == 200
    assert response.json()[0]["id"] == "fia-example"
    assert len(response.json()[0]["sha256"]) == 64


@pytest.mark.parametrize(
    "path",
    ["/incidents/missing", "/incidents/missing/evidence"],
)
def test_unknown_incident_returns_404(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_repository_not_found_error_becomes_404(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(_: str) -> EvidencePacket:
        raise RecordNotFoundError("Unknown incident")

    monkeypatch.setattr(api, "get_incident_packet", missing)

    response = client.get("/incidents/not-in-repository")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident 'not-in-repository' was not found."


def test_deliberation_run_and_bias_audit_flow(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    verdict: Verdict,
) -> None:
    monkeypatch.setattr(api, "deliberate", lambda incident_id: verdict)
    monkeypatch.setattr(
        api,
        "audit_bias",
        lambda incident_id: {"passed": True, "confidence_delta": 0.01},
    )

    created = client.post("/incidents/sample-incident/deliberate")
    assert created.status_code == 201
    run_id = created.json()["id"]
    assert created.json()["verdict"]["decision"] == "penalty"

    fetched = client.get(f"/runs/{run_id}")
    assert fetched.status_code == 200
    assert fetched.json()["incident_id"] == "sample-incident"

    audited = client.post(f"/runs/{run_id}/bias-audit")
    assert audited.status_code == 200
    assert audited.json()["passed"] is True

    summary = client.get("/evaluation/summary")
    assert summary.status_code == 200
    assert summary.json() == {
        "completed_runs": 1,
        "unique_incidents": 1,
        "average_confidence": 0.82,
        "decision_counts": {"penalty": 1},
        "bias_audits": 1,
        "bias_audit_pass_rate": 1.0,
    }


def test_unknown_run_returns_404(client: TestClient) -> None:
    assert client.get("/runs/missing").status_code == 404
    assert client.post("/runs/missing/bias-audit").status_code == 404

