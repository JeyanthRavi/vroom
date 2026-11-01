import pytest
from stewardlens.agents import (
    AdvocateAgent,
    CitationValidationError,
    EvidenceAgent,
    RegulationAgent,
    StewardAgent,
    anonymize_packet,
    run_specialists,
    validate_finding_citations,
)
from stewardlens.contracts import (
    AgentFinding,
    EvidenceItem,
    EvidencePacket,
    Incident,
    RegulationClause,
)


@pytest.fixture
def packet() -> EvidencePacket:
    return EvidencePacket(
        incident=Incident(
            id="2025-test-r12",
            season=2025,
            event="Test Grand Prix",
            session="Race",
            lap=12,
            driver_a="Apex",
            driver_b="Bolt",
            category="causing_a_collision",
            summary="Apex forced Bolt off after avoidable contact.",
            evidence_ids=["tel-1", "rc-1"],
        ),
        evidence=[
            EvidenceItem(
                id="tel-1",
                kind="telemetry",
                summary="Apex remained on throttle and left no room for Bolt.",
                source="fixture://telemetry",
                quality=0.9,
            ),
            EvidenceItem(
                id="rc-1",
                kind="race_control",
                summary="The incident was noted as possible avoidable contact.",
                source="fixture://race-control",
                quality=0.8,
            ),
        ],
        regulations=[
            RegulationClause(
                id="reg-33.4",
                season=2025,
                article="33.4",
                title="Driving standards",
                text="A driver must not cause avoidable contact or force another car off track.",
                source="fixture://regulations",
            )
        ],
        precedent_ids=["precedent-2024-01"],
    )


def test_evidence_agent_reconstructs_without_assigning_decision(packet):
    result = EvidenceAgent().analyze(packet)
    assert result.agent == "evidence"
    assert result.evidence_ids == ["rc-1", "tel-1"]
    assert result.regulation_ids == []
    assert result.confidence == pytest.approx(0.85)


def test_regulation_agent_uses_packet_regulation_ids(packet):
    result = RegulationAgent().analyze(packet)
    assert result.regulation_ids == ["reg-33.4"]
    assert "Article 33.4" in result.claims[0]


def test_both_advocates_receive_the_same_grounded_record(packet):
    first = AdvocateAgent("a").analyze(packet)
    second = AdvocateAgent("b").analyze(packet)
    assert set(first.evidence_ids) == set(second.evidence_ids) == {"tel-1", "rc-1"}
    assert first.regulation_ids == second.regulation_ids == ["reg-33.4"]
    assert "Apex" in first.position
    assert "Bolt" in second.position


def test_invalid_citation_is_rejected(packet):
    bad = AgentFinding(
        agent="bad",
        position="unsupported",
        claims=["Unsupported claim"],
        evidence_ids=["missing"],
        confidence=0.5,
    )
    with pytest.raises(CitationValidationError, match="unknown evidence IDs: missing"):
        validate_finding_citations(bad, packet)


def test_steward_returns_penalty_with_valid_citations(packet):
    outputs = run_specialists(packet)
    verdict = StewardAgent().decide(packet, outputs)
    assert verdict.decision == "penalty"
    assert verdict.penalty_category == "time_penalty"
    assert set(verdict.evidence_citations) == {"tel-1", "rc-1"}
    assert verdict.regulation_citations == ["reg-33.4"]
    assert set(verdict.agent_outputs) == {
        "evidence", "regulation", "precedent", "advocate_a", "advocate_b"
    }


def test_steward_refuses_substantive_ruling_when_record_is_incomplete(packet):
    incomplete = packet.model_copy(update={"regulations": []})
    verdict = StewardAgent().decide(incomplete, run_specialists(incomplete))
    assert verdict.decision == "insufficient_evidence"
    assert verdict.penalty_category == "none"
    assert "No season-matched regulation" in " ".join(verdict.missing_evidence)


def test_anonymization_removes_driver_names_without_changing_source_packet(packet):
    anonymous = anonymize_packet(packet)
    assert anonymous.incident.driver_a == "Driver Alpha"
    assert anonymous.incident.driver_b == "Driver Beta"
    assert "Apex" not in anonymous.incident.summary
    assert "Bolt" not in " ".join(item.summary for item in anonymous.evidence)
    assert packet.incident.driver_a == "Apex"

