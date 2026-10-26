"""Stable contracts shared by StewardLens components.

This module is owned by the integration layer. Feature modules should import
these models rather than redefining their own payload shapes.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Decision = Literal[
    "penalty", "no_further_action", "racing_incident", "insufficient_evidence"
]
PenaltyCategory = Literal[
    "none", "reprimand", "time_penalty", "grid_penalty", "other"
]


class EvidenceItem(BaseModel):
    id: str
    kind: Literal["fact", "telemetry", "race_control", "document"]
    summary: str
    source: str
    quality: float = Field(ge=0.0, le=1.0)


class RegulationClause(BaseModel):
    id: str
    season: int
    article: str
    title: str
    text: str
    source: str


class Incident(BaseModel):
    id: str
    season: int
    event: str
    session: str
    lap: int
    driver_a: str
    driver_b: str
    category: str
    summary: str
    evidence_ids: List[str]
    official_decision: Optional[Decision] = None
    official_penalty: Optional[PenaltyCategory] = None


class EvidencePacket(BaseModel):
    incident: Incident
    evidence: List[EvidenceItem]
    regulations: List[RegulationClause] = Field(default_factory=list)
    precedent_ids: List[str] = Field(default_factory=list)


class AgentFinding(BaseModel):
    agent: str
    position: str
    claims: List[str]
    evidence_ids: List[str]
    regulation_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)


class Verdict(BaseModel):
    incident_id: str
    decision: Decision
    penalty_category: PenaltyCategory
    confidence: float = Field(ge=0.0, le=1.0)
    findings: List[str]
    evidence_citations: List[str]
    regulation_citations: List[str]
    dissenting_interpretation: str
    missing_evidence: List[str]
    agent_outputs: Dict[str, AgentFinding]
    bias_audit_passed: Optional[bool] = None

