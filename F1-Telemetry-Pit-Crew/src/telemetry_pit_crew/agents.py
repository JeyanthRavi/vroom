"""Offline specialist agents grounded entirely in computed evidence."""

from __future__ import annotations

from typing import Dict, List

from .contracts import AgentFinding, SegmentEvidence


def _winner(ev: SegmentEvidence) -> str:
    return "A" if ev.delta_a_minus_b < 0 else "B"


def braking_agent(items: List[SegmentEvidence]) -> List[AgentFinding]:
    out = []
    for ev in items:
        if ev.segment.kind != "corner" or ev.braking_onset_a is None or ev.braking_onset_b is None:
            continue
        diff = ev.braking_onset_a - ev.braking_onset_b
        out.append(AgentFinding(
            agent="braking", segment_id=ev.segment.id,
            finding=f"Driver {_winner(ev)} was faster through {ev.segment.name}; A's detected braking onset was {abs(diff):.0f} m {'later' if diff > 0 else 'earlier'} than B's.",
            evidence_ids=[ev.id], confidence=ev.quality * 0.82,
            limitation="Brake is a binary public channel; pedal pressure is unavailable.",
        ))
    return out


def cornering_agent(items: List[SegmentEvidence]) -> List[AgentFinding]:
    return [AgentFinding(
        agent="cornering", segment_id=ev.segment.id,
        finding=f"Driver {_winner(ev)} gained time in {ev.segment.name}; minimum-speed difference was {abs(ev.min_speed_a - ev.min_speed_b):.1f} km/h.",
        evidence_ids=[ev.id], confidence=ev.quality * 0.78,
        limitation="This is consistent with a corner-speed difference but does not prove setup or driving technique.",
    ) for ev in items if ev.segment.kind == "corner"]


def traction_agent(items: List[SegmentEvidence]) -> List[AgentFinding]:
    out = []
    for ev in items:
        if ev.segment.kind != "corner":
            continue
        out.append(AgentFinding(
            agent="traction", segment_id=ev.segment.id,
            finding=f"Exit performance in {ev.segment.name} favoured Driver {_winner(ev)} by the segment timing evidence.",
            evidence_ids=[ev.id], confidence=ev.quality * 0.66,
            limitation="Throttle pickup alone cannot separate traction, tyre state and car setup.",
        ))
    return out


def straight_line_agent(items: List[SegmentEvidence]) -> List[AgentFinding]:
    return [AgentFinding(
        agent="straight_line", segment_id=ev.segment.id,
        finding=f"Driver {_winner(ev)} was faster over {ev.segment.name}; peak-speed difference was {abs(ev.max_speed_a - ev.max_speed_b):.1f} km/h.",
        evidence_ids=[ev.id], confidence=ev.quality * 0.8,
        limitation="The preceding corner and DRS state may contribute to this difference.",
    ) for ev in items if ev.segment.kind == "straight"]


def run_specialists(items: List[SegmentEvidence]) -> Dict[str, List[AgentFinding]]:
    return {
        "braking": braking_agent(items), "cornering": cornering_agent(items),
        "traction": traction_agent(items), "straight_line": straight_line_agent(items),
    }

