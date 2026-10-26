"""Orchestration service for a complete StewardLens review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union

from .agents import StewardAgent, anonymize_packet, run_specialists, validate_verdict_citations
from .contracts import EvidencePacket, Verdict


PacketLoader = Callable[[str], EvidencePacket]
PacketEnricher = Callable[[EvidencePacket], EvidencePacket]


def _default_packet_loader(incident_id: str) -> EvidencePacket:
    # Kept lazy so the reasoning layer can be imported and tested before a
    # repository implementation or data file is configured.
    from .repository import get_incident_packet

    return get_incident_packet(incident_id)


@dataclass
class StewardOrchestrator:
    """Load, optionally enrich, deliberate, validate, and bias-audit a case."""

    packet_loader: PacketLoader = _default_packet_loader
    packet_enricher: Optional[PacketEnricher] = None
    steward: StewardAgent = StewardAgent()
    bias_confidence_tolerance: float = 0.05

    def review(
        self,
        incident: Union[str, EvidencePacket],
        *,
        audit_bias: bool = True,
    ) -> Verdict:
        packet = self.packet_loader(incident) if isinstance(incident, str) else incident
        if self.packet_enricher is not None:
            packet = self.packet_enricher(packet)
        outputs = run_specialists(packet)
        verdict = self.steward.decide(packet, outputs)

        if audit_bias:
            anonymous_packet = anonymize_packet(packet)
            anonymous_outputs = run_specialists(anonymous_packet)
            anonymous_verdict = self.steward.decide(anonymous_packet, anonymous_outputs)
            passed = (
                verdict.decision == anonymous_verdict.decision
                and verdict.penalty_category == anonymous_verdict.penalty_category
                and abs(verdict.confidence - anonymous_verdict.confidence)
                <= self.bias_confidence_tolerance
            )
            verdict = verdict.model_copy(update={"bias_audit_passed": passed})

        validate_verdict_citations(verdict, packet)
        return verdict


def review_incident(
    incident: Union[str, EvidencePacket],
    *,
    audit_bias: bool = True,
    packet_loader: PacketLoader = _default_packet_loader,
    packet_enricher: Optional[PacketEnricher] = None,
) -> Verdict:
    """Functional convenience API used by HTTP and CLI adapters."""

    return StewardOrchestrator(
        packet_loader=packet_loader,
        packet_enricher=packet_enricher,
    ).review(incident, audit_bias=audit_bias)


def deliberate(incident_id: str) -> Verdict:
    """Compatibility entry point for the HTTP layer's deliberation route."""

    return review_incident(incident_id, audit_bias=False)


def audit_bias(incident_id: str) -> Verdict:
    """Run a fresh identity-neutral audit for an incident."""

    return review_incident(incident_id, audit_bias=True)

