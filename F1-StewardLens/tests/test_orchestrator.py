from dataclasses import dataclass

from stewardlens.agents import HeuristicDecisionAdapter, StewardAgent
from stewardlens.contracts import EvidenceItem, EvidencePacket, Incident, RegulationClause
from stewardlens.orchestrator import (
    StewardOrchestrator,
    audit_bias,
    deliberate,
    review_incident,
)


def make_packet() -> EvidencePacket:
    return EvidencePacket(
        incident=Incident(
            id="case-1",
            season=2026,
            event="Demo GP",
            session="Race",
            lap=5,
            driver_a="North",
            driver_b="South",
            category="collision",
            summary="Both contributed and neither was predominantly responsible.",
            evidence_ids=["e1", "e2"],
        ),
        evidence=[
            EvidenceItem(
                id="e1", kind="telemetry", summary="Both contributed to the contact.",
                source="fixture://one", quality=0.9,
            ),
            EvidenceItem(
                id="e2", kind="race_control", summary="Neither was predominantly responsible.",
                source="fixture://two", quality=0.85,
            ),
        ],
        regulations=[
            RegulationClause(
                id="r1", season=2026, article="1", title="Driving conduct",
                text="Stewards may classify contact as a racing incident.",
                source="fixture://rule",
            )
        ],
    )


def test_orchestrator_loads_by_id_and_runs_bias_audit():
    seen = []

    def loader(incident_id):
        seen.append(incident_id)
        return make_packet()

    verdict = StewardOrchestrator(packet_loader=loader).review("case-1")
    assert seen == ["case-1"]
    assert verdict.decision == "racing_incident"
    assert verdict.bias_audit_passed is True


def test_orchestrator_can_skip_bias_audit():
    verdict = StewardOrchestrator().review(make_packet(), audit_bias=False)
    assert verdict.bias_audit_passed is None


def test_orchestrator_applies_packet_enricher_before_review():
    bare = make_packet().model_copy(update={"regulations": []})

    def enrich(packet):
        return packet.model_copy(update={"regulations": make_packet().regulations})

    verdict = StewardOrchestrator(packet_enricher=enrich).review(bare)
    assert verdict.decision == "racing_incident"
    assert verdict.regulation_citations == ["r1"]


def test_functional_review_api_accepts_packet():
    verdict = review_incident(make_packet())
    assert verdict.incident_id == "case-1"
    assert len(verdict.agent_outputs) == 5


@dataclass(frozen=True)
class NameBiasedAdapter(HeuristicDecisionAdapter):
    def decide(self, packet, findings):
        if packet.incident.driver_a == "North":
            return "penalty", "time_penalty", 0.9, ["Identity-sensitive result."], ""
        return "racing_incident", "none", 0.9, ["Identity-sensitive result."], ""


def test_bias_audit_detects_identity_sensitive_adapter():
    orchestrator = StewardOrchestrator(steward=StewardAgent(adapter=NameBiasedAdapter()))
    verdict = orchestrator.review(make_packet())
    assert verdict.bias_audit_passed is False


def test_confidence_is_bounded_and_deterministic():
    orchestrator = StewardOrchestrator()
    first = orchestrator.review(make_packet())
    second = orchestrator.review(make_packet())
    assert 0 <= first.confidence <= 1
    assert first.model_dump() == second.model_dump()


def test_http_compatibility_entry_points(monkeypatch):
    import stewardlens.repository as repository

    monkeypatch.setattr(
        repository, "get_incident_packet", lambda _: make_packet(), raising=False
    )
    assert deliberate("case-1").bias_audit_passed is None
    assert audit_bias("case-1").bias_audit_passed is True

