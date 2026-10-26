"""Deterministic telemetry alignment and feature extraction."""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence

from .contracts import Lap, Segment, SegmentEvidence, TelemetrySample


def _within(samples: Sequence[TelemetrySample], segment: Segment) -> List[TelemetrySample]:
    return [s for s in samples if segment.start_distance <= s.distance <= segment.end_distance]


def _duration(samples: Sequence[TelemetrySample]) -> float:
    return 0.0 if len(samples) < 2 else samples[-1].time - samples[0].time


def _first_distance(
    samples: Sequence[TelemetrySample], predicate: Callable[[TelemetrySample], bool]
) -> Optional[float]:
    item = next((s for s in samples if predicate(s)), None)
    return None if item is None else item.distance


def extract_segment_evidence(lap_a: Lap, lap_b: Lap, segments: Sequence[Segment]) -> List[SegmentEvidence]:
    evidence: List[SegmentEvidence] = []
    for segment in segments:
        a = _within(lap_a.samples, segment)
        b = _within(lap_b.samples, segment)
        if len(a) < 2 or len(b) < 2:
            continue
        time_a, time_b = _duration(a), _duration(b)
        evidence.append(
            SegmentEvidence(
                id=f"ev-{segment.id}", segment=segment,
                time_a=time_a, time_b=time_b, delta_a_minus_b=time_a - time_b,
                braking_onset_a=_first_distance(a, lambda s: s.brake >= 50),
                braking_onset_b=_first_distance(b, lambda s: s.brake >= 50),
                min_speed_a=min(s.speed for s in a), min_speed_b=min(s.speed for s in b),
                throttle_pickup_a=_first_distance(a, lambda s: s.throttle >= 95),
                throttle_pickup_b=_first_distance(b, lambda s: s.throttle >= 95),
                max_speed_a=max(s.speed for s in a), max_speed_b=max(s.speed for s in b),
                quality=min(lap_a.quality_score, lap_b.quality_score),
            )
        )
    return evidence

