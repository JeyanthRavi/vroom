"""Deterministic synthetic telemetry used for the offline demo and tests."""

from __future__ import annotations

import math
from typing import Dict, List

from .contracts import Lap, Segment, TelemetrySample


SEGMENTS = [
    Segment(id="S1", name="Main straight", kind="straight", start_distance=0, end_distance=650),
    Segment(id="T1", name="Turn 1", kind="corner", start_distance=650, end_distance=1050),
    Segment(id="S2", name="Back straight", kind="straight", start_distance=1050, end_distance=1850),
    Segment(id="T2", name="Turn 2", kind="corner", start_distance=1850, end_distance=2300),
    Segment(id="S3", name="Final straight", kind="straight", start_distance=2300, end_distance=3000),
]


def _speed_profile(distance: float, driver: str) -> float:
    base = 295.0
    corner_1 = 205.0 * math.exp(-((distance - 835.0) / 155.0) ** 2)
    corner_2 = 180.0 * math.exp(-((distance - 2070.0) / 175.0) ** 2)
    speed = base - corner_1 - corner_2
    if driver == "A":
        speed += 5.0 * math.exp(-((distance - 900.0) / 150.0) ** 2)
        speed -= 4.0 * math.exp(-((distance - 2200.0) / 210.0) ** 2)
    else:
        speed -= 3.0 * math.exp(-((distance - 900.0) / 150.0) ** 2)
        speed += 6.0 * math.exp(-((distance - 2200.0) / 210.0) ** 2)
    return max(70.0, speed)


def make_lap(driver: str) -> Lap:
    samples: List[TelemetrySample] = []
    elapsed = 0.0
    previous_distance = 0.0
    for distance in range(0, 3001, 10):
        speed = _speed_profile(float(distance), driver)
        if distance:
            elapsed += (distance - previous_distance) / (speed / 3.6)
        braking = 100.0 if (620 <= distance <= 850 or 1810 <= distance <= 2040) else 0.0
        throttle = 18.0 if braking else min(100.0, 55.0 + speed / 5.0)
        samples.append(
            TelemetrySample(
                distance=float(distance), time=elapsed, speed=speed,
                throttle=throttle, brake=braking,
                gear=max(1, min(8, int(speed / 38) + 1)),
                rpm=6500 + speed * 18, drs=12 if braking == 0 and speed > 260 else 0,
            )
        )
        previous_distance = float(distance)
    return Lap(
        id=f"demo-{driver}", driver=f"Demo Driver {driver}", circuit="Synthetic Ring",
        lap_number=1 if driver == "A" else 2, lap_time=elapsed,
        compound="MEDIUM", tyre_life=5, samples=samples, quality_score=0.98,
    )


def demo_laps() -> Dict[str, Lap]:
    return {lap.id: lap for lap in (make_lap("A"), make_lap("B"))}

