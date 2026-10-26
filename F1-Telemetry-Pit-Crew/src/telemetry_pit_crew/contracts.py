from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TelemetrySample(BaseModel):
    distance: float
    time: float
    speed: float
    throttle: float
    brake: float
    gear: int
    rpm: float
    drs: int = 0


class Lap(BaseModel):
    id: str
    driver: str
    circuit: str
    lap_number: int
    lap_time: float
    compound: str
    tyre_life: int
    samples: List[TelemetrySample]
    quality_score: float = Field(ge=0.0, le=1.0)


class Segment(BaseModel):
    id: str
    name: str
    kind: Literal["corner", "straight"]
    start_distance: float
    end_distance: float


class SegmentEvidence(BaseModel):
    id: str
    segment: Segment
    time_a: float
    time_b: float
    delta_a_minus_b: float
    braking_onset_a: Optional[float]
    braking_onset_b: Optional[float]
    min_speed_a: float
    min_speed_b: float
    throttle_pickup_a: Optional[float]
    throttle_pickup_b: Optional[float]
    max_speed_a: float
    max_speed_b: float
    quality: float = Field(ge=0.0, le=1.0)


class AgentFinding(BaseModel):
    agent: str
    segment_id: str
    finding: str
    evidence_ids: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    limitation: str = ""


class Debrief(BaseModel):
    comparison_id: str
    driver_a: str
    driver_b: str
    total_delta_seconds: float
    summary: str
    priority_findings: List[AgentFinding]
    all_agent_findings: Dict[str, List[AgentFinding]]
    data_limitations: List[str]

