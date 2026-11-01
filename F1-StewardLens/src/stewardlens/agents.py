"""Deterministic specialist agents used by the StewardLens tribunal.

The first release deliberately keeps reasoning offline.  Each specialist
returns the same typed :class:`AgentFinding` contract an LLM adapter would
return, which makes a future model-backed implementation a replaceable detail
rather than a rewrite of the orchestration layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import mean
from typing import Dict, Iterable, Literal, Mapping, Optional, Protocol, Sequence

from .contracts import AgentFinding, Decision, EvidencePacket, PenaltyCategory, Verdict


class CitationValidationError(ValueError):
    """Raised when an agent cites material that is not in its input packet."""


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _short(text: str, limit: int = 180) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def validate_finding_citations(finding: AgentFinding, packet: EvidencePacket) -> None:
    """Ensure a finding references only evidence and rules in ``packet``.

    Validation is intentionally strict at the agent boundary.  Invalid IDs
    are a data-integrity problem and are never silently removed.
    """

    evidence_ids = {item.id for item in packet.evidence}
    regulation_ids = {clause.id for clause in packet.regulations}
    unknown_evidence = sorted(set(finding.evidence_ids) - evidence_ids)
    unknown_regulations = sorted(set(finding.regulation_ids) - regulation_ids)
    if unknown_evidence or unknown_regulations:
        details = []
        if unknown_evidence:
            details.append(f"unknown evidence IDs: {', '.join(unknown_evidence)}")
        if unknown_regulations:
            details.append(f"unknown regulation IDs: {', '.join(unknown_regulations)}")
        raise CitationValidationError(f"{finding.agent}: {'; '.join(details)}")


def validate_verdict_citations(verdict: Verdict, packet: EvidencePacket) -> None:
    """Validate final citations and all embedded specialist findings."""

    evidence_ids = {item.id for item in packet.evidence}
    regulation_ids = {clause.id for clause in packet.regulations}
    unknown_evidence = sorted(set(verdict.evidence_citations) - evidence_ids)
    unknown_regulations = sorted(set(verdict.regulation_citations) - regulation_ids)
    if unknown_evidence or unknown_regulations:
        details = []
        if unknown_evidence:
            details.append(f"unknown evidence IDs: {', '.join(unknown_evidence)}")
        if unknown_regulations:
            details.append(f"unknown regulation IDs: {', '.join(unknown_regulations)}")
        raise CitationValidationError(f"steward: {'; '.join(details)}")
    for finding in verdict.agent_outputs.values():
        validate_finding_citations(finding, packet)


class SpecialistAgent(Protocol):
    """Boundary implemented by deterministic and future LLM specialists."""

    @property
    def name(self) -> str:
        """Stable key used to collect the specialist output."""

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        """Return one schema-validated, grounded finding."""


@dataclass(frozen=True)
class EvidenceAgent:
    name: str = "evidence"

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        ordered = sorted(packet.evidence, key=lambda item: item.id)
        claims = [f"{item.kind.replace('_', ' ').title()}: {_short(item.summary)}" for item in ordered]
        limitations = []
        kinds = {item.kind for item in ordered}
        if not ordered:
            limitations.append("No evidence items were supplied.")
        if "telemetry" not in kinds:
            limitations.append("No telemetry evidence is available.")
        if "race_control" not in kinds:
            limitations.append("No race-control evidence is available.")
        low_quality = [item.id for item in ordered if item.quality < 0.6]
        if low_quality:
            limitations.append("Low-quality evidence: " + ", ".join(low_quality))
        confidence = mean(item.quality for item in ordered) if ordered else 0.0
        finding = AgentFinding(
            agent=self.name,
            position="neutral reconstruction",
            claims=claims or ["The incident cannot be reconstructed from the supplied packet."],
            evidence_ids=[item.id for item in ordered],
            confidence=_bounded(confidence),
            limitations=limitations,
        )
        validate_finding_citations(finding, packet)
        return finding


@dataclass(frozen=True)
class RegulationAgent:
    name: str = "regulation"

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        clauses = sorted(packet.regulations, key=lambda clause: clause.id)
        claims = [
            f"Article {clause.article} ({clause.title}) may apply: {_short(clause.text)}"
            for clause in clauses
        ]
        limitations = [] if clauses else ["No season-matched regulation was retrieved."]
        finding = AgentFinding(
            agent=self.name,
            position="applicable regulations",
            claims=claims or ["No rule application can be assessed from this packet."],
            evidence_ids=[],
            regulation_ids=[clause.id for clause in clauses],
            confidence=0.9 if clauses else 0.0,
            limitations=limitations,
        )
        validate_finding_citations(finding, packet)
        return finding


@dataclass(frozen=True)
class PrecedentAgent:
    name: str = "precedent"

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        precedents = sorted(set(packet.precedent_ids))
        limitations = ["Precedents are persuasive comparisons, not binding rules."]
        if not precedents:
            limitations.append("No comparable historical decision was retrieved.")
        return AgentFinding(
            agent=self.name,
            position="historical comparison",
            claims=[f"Comparable decision available: {item}" for item in precedents]
            or ["No historical comparison is available."],
            evidence_ids=[],
            confidence=0.65 if precedents else 0.0,
            limitations=limitations,
        )


@dataclass(frozen=True)
class AdvocateAgent:
    """Build the strongest grounded interpretation for one named driver."""

    side: str

    @property
    def name(self) -> str:
        return f"advocate_{self.side.lower()}"

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        if self.side.lower() not in {"a", "b"}:
            raise ValueError("Advocate side must be 'a' or 'b'.")
        driver = packet.incident.driver_a if self.side.lower() == "a" else packet.incident.driver_b
        opponent = packet.incident.driver_b if self.side.lower() == "a" else packet.incident.driver_a
        usable = sorted(
            (item for item in packet.evidence if item.quality >= 0.5),
            key=lambda item: (-item.quality, item.id),
        )
        cited = [item.id for item in usable]
        regulations = [clause.id for clause in sorted(packet.regulations, key=lambda clause: clause.id)]
        claims = [
            f"The available record permits an interpretation favorable to {driver}; "
            f"responsibility should not be assigned merely from the identities of {driver} and {opponent}."
        ]
        if cited:
            claims.append(
                f"The argument for {driver} relies on the corroborated record "
                f"({', '.join(cited)}) and treats contrary inferences as disputed."
            )
        limitations = [] if cited else ["No evidence of sufficient quality supports a driver-specific argument."]
        finding = AgentFinding(
            agent=self.name,
            position=f"strongest grounded case for {driver}",
            claims=claims,
            evidence_ids=cited,
            regulation_ids=regulations,
            confidence=_bounded(mean(item.quality for item in usable) * 0.75) if usable else 0.0,
            limitations=limitations,
        )
        validate_finding_citations(finding, packet)
        return finding


class DecisionAdapter(Protocol):
    """Replaceable decision boundary for a future model-backed steward."""

    def decide(
        self, packet: EvidencePacket, findings: Mapping[str, AgentFinding]
    ) -> tuple[Decision, PenaltyCategory, float, Sequence[str], str]:
        """Return decision, penalty, confidence, findings, and dissent."""


@dataclass(frozen=True)
class HeuristicDecisionAdapter:
    """Conservative keyword scorer suitable for demos and offline tests."""

    penalty_terms: tuple[str, ...] = (
        "caused a collision",
        "predominantly to blame",
        "predominantly responsible",
        "avoidable contact",
        "unsafe release",
        "forced off",
        "left no room",
        "locked the front",
        "front-wheel lock-up",
        "missed the apex",
        "rejoined across the racing line",
        "unsafe rejoin",
        "breach",
        "at fault",
    )
    racing_terms: tuple[str, ...] = (
        "racing incident",
        "both contributed",
        "neither predominantly",
        "shared responsibility",
        "side by side",
        "maintained a predictable line",
        "without either driver losing control",
    )
    no_action_terms: tuple[str, ...] = (
        "no further action",
        "no infringement",
        "no breach",
        "no driver was wholly or predominantly",
    )

    def decide(
        self, packet: EvidencePacket, findings: Mapping[str, AgentFinding]
    ) -> tuple[Decision, PenaltyCategory, float, Sequence[str], str]:
        evidence = [item for item in packet.evidence if item.quality >= 0.5]
        regulatory_support = bool(packet.regulations)
        average_quality = mean(item.quality for item in evidence) if evidence else 0.0
        if len(evidence) < 2 or average_quality < 0.55 or not regulatory_support:
            return (
                "insufficient_evidence",
                "none",
                _bounded(0.35 + average_quality * 0.2),
                ["The evidentiary or regulatory record is incomplete."],
                "A fuller record could support a substantive ruling.",
            )

        corpus = " ".join(
            [packet.incident.summary]
            + [item.summary for item in evidence]
            + [clause.text for clause in packet.regulations]
        ).lower()
        DecisionCandidate = Literal["penalty", "racing_incident", "no_further_action"]
        scores: Dict[DecisionCandidate, int] = {
            "penalty": sum(corpus.count(term) for term in self.penalty_terms),
            "racing_incident": sum(corpus.count(term) for term in self.racing_terms),
            "no_further_action": sum(corpus.count(term) for term in self.no_action_terms),
        }
        # Longer phrases can contain a generic "breach"; explicit no-action
        # language is therefore given priority on tied scores.
        priority: Dict[DecisionCandidate, int] = {
            "no_further_action": 2,
            "racing_incident": 1,
            "penalty": 0,
        }
        decision: DecisionCandidate = max(
            scores, key=lambda key: (scores[key], priority[key])
        )
        if scores[decision] == 0:
            decision = "racing_incident"
        penalty: PenaltyCategory = "time_penalty" if decision == "penalty" else "none"
        top_score = scores[decision]
        confidence = _bounded(0.52 + min(top_score, 3) * 0.1 + average_quality * 0.18)
        summary = {
            "penalty": "The cited record supports a rule breach warranting a penalty.",
            "racing_incident": "The record does not establish predominant responsibility.",
            "no_further_action": "The record supports closing the investigation without further action.",
        }[decision]
        dissent = {
            "penalty": "A dissent could treat the contact as shared racing responsibility.",
            "racing_incident": "A dissent could assign predominant responsibility to one driver.",
            "no_further_action": "A dissent could find that the same facts meet the threshold for a breach.",
        }[decision]
        return decision, penalty, confidence, [summary], dissent


@dataclass(frozen=True)
class StewardAgent:
    adapter: DecisionAdapter = HeuristicDecisionAdapter()
    name: str = "steward"

    def decide(self, packet: EvidencePacket, findings: Mapping[str, AgentFinding]) -> Verdict:
        decision, penalty, confidence, conclusions, dissent = self.adapter.decide(packet, findings)
        evidence_citations = sorted(
            {
                citation
                for finding in findings.values()
                for citation in finding.evidence_ids
            }
        )
        regulation_citations = sorted(
            {
                citation
                for finding in findings.values()
                for citation in finding.regulation_ids
            }
        )
        missing = list(findings.get("evidence", AgentFinding(
            agent="evidence",
            position="neutral reconstruction",
            claims=[],
            evidence_ids=[],
            confidence=0.0,
        )).limitations)
        missing.extend(findings.get("regulation", AgentFinding(
            agent="regulation",
            position="applicable regulations",
            claims=[],
            evidence_ids=[],
            confidence=0.0,
        )).limitations)
        verdict = Verdict(
            incident_id=packet.incident.id,
            decision=decision,
            penalty_category=penalty,
            confidence=confidence,
            findings=list(conclusions),
            evidence_citations=evidence_citations,
            regulation_citations=regulation_citations,
            dissenting_interpretation=dissent,
            missing_evidence=sorted(set(missing)),
            agent_outputs=dict(findings),
        )
        validate_verdict_citations(verdict, packet)
        return verdict


def anonymize_packet(packet: EvidencePacket) -> EvidencePacket:
    """Return a semantically identical packet with neutral driver labels."""

    names = ((packet.incident.driver_a, "Driver Alpha"), (packet.incident.driver_b, "Driver Beta"))

    def replace(text: str) -> str:
        for original, anonymous in names:
            text = re.sub(re.escape(original), anonymous, text, flags=re.IGNORECASE)
        return text

    incident = packet.incident.model_copy(
        update={
            "driver_a": "Driver Alpha",
            "driver_b": "Driver Beta",
            "summary": replace(packet.incident.summary),
        }
    )
    evidence = [item.model_copy(update={"summary": replace(item.summary)}) for item in packet.evidence]
    return packet.model_copy(update={"incident": incident, "evidence": evidence})


def run_specialists(
    packet: EvidencePacket,
    agents: Optional[Iterable[SpecialistAgent]] = None,
) -> Dict[str, AgentFinding]:
    """Run all independent specialists in a stable order."""

    specialists = list(agents) if agents is not None else [
        EvidenceAgent(),
        RegulationAgent(),
        PrecedentAgent(),
        AdvocateAgent("a"),
        AdvocateAgent("b"),
    ]
    outputs: Dict[str, AgentFinding] = {}
    for agent in specialists:
        finding = agent.analyze(packet)
        validate_finding_citations(finding, packet)
        if finding.agent in outputs:
            raise ValueError(f"Duplicate agent name: {finding.agent}")
        outputs[finding.agent] = finding
    return outputs

