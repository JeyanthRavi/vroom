"""HTTP API for the StewardLens research prototype.

The API deliberately keeps run persistence small and local.  A production
deployment can replace :class:`RunStore` without changing the agent or data
layers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from stewardlens.contracts import EvidencePacket, Incident, Verdict
from stewardlens.orchestrator import audit_bias, deliberate
from stewardlens.repository import (
    RecordNotFoundError,
    get_incident_packet,
    list_incidents,
    list_real_decisions,
)
from stewardlens.web import INDEX_HTML


class RunRecord(BaseModel):
    """One inspectable deliberation run."""

    id: str
    incident_id: str
    status: str = "completed"
    verdict: Verdict
    created_at: datetime


class BiasAuditResult(BaseModel):
    """Result attached to a prior deliberation run."""

    run_id: str
    incident_id: str
    passed: Optional[bool] = None
    result: Any


class EvaluationSummary(BaseModel):
    completed_runs: int
    unique_incidents: int
    average_confidence: float = Field(ge=0.0, le=1.0)
    decision_counts: Dict[str, int]
    bias_audits: int
    bias_audit_pass_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class RunStore:
    """Thread-safe, in-memory storage suitable for a single-process demo."""

    def __init__(self) -> None:
        self._runs: Dict[str, RunRecord] = {}
        self._audits: Dict[str, BiasAuditResult] = {}
        self._lock = Lock()

    def add(self, incident_id: str, verdict: Verdict) -> RunRecord:
        record = RunRecord(
            id=uuid4().hex,
            incident_id=incident_id,
            verdict=verdict,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._runs[record.id] = record
        return record

    def get(self, run_id: str) -> Optional[RunRecord]:
        with self._lock:
            return self._runs.get(run_id)

    def attach_audit(self, audit: BiasAuditResult) -> BiasAuditResult:
        with self._lock:
            self._audits[audit.run_id] = audit
        return audit

    def snapshot(self) -> tuple[List[RunRecord], List[BiasAuditResult]]:
        with self._lock:
            return list(self._runs.values()), list(self._audits.values())

    def clear(self) -> None:
        """Clear process-local state; useful for isolated test runs."""

        with self._lock:
            self._runs.clear()
            self._audits.clear()


run_store = RunStore()

app = FastAPI(
    title="StewardLens API",
    version="0.1.0",
    description=(
        "Educational, evidence-grounded Formula 1 incident deliberation. "
        "StewardLens is not an official FIA decision system."
    ),
)


def _incident_packet_or_404(incident_id: str) -> EvidencePacket:
    try:
        packet = get_incident_packet(incident_id)
    except (KeyError, LookupError, RecordNotFoundError):
        packet = None
    if packet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' was not found.",
        )
    return packet


def _as_verdict(value: Any) -> Verdict:
    if isinstance(value, Verdict):
        return value
    return Verdict.model_validate(value)


def _audit_passed(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, Verdict):
        return value.bias_audit_passed
    if isinstance(value, BaseModel):
        value = value.model_dump()
    if isinstance(value, dict):
        candidate = value.get("passed", value.get("bias_audit_passed"))
        return candidate if isinstance(candidate, bool) else None
    return None


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return INDEX_HTML


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/incidents", response_model=List[Incident])
def incidents() -> List[Incident]:
    return list_incidents()


@app.get("/fia-decisions")
def fia_decisions() -> List[Dict[str, Any]]:
    """List checksum-verified official FIA decisions in the local corpus."""

    return list_real_decisions()


@app.get("/incidents/{incident_id}", response_model=Incident)
def incident(incident_id: str) -> Incident:
    return _incident_packet_or_404(incident_id).incident


@app.get("/incidents/{incident_id}/evidence", response_model=EvidencePacket)
def incident_evidence(incident_id: str) -> EvidencePacket:
    return _incident_packet_or_404(incident_id)


@app.post(
    "/incidents/{incident_id}/deliberate",
    response_model=RunRecord,
    status_code=status.HTTP_201_CREATED,
)
def deliberate_incident(incident_id: str) -> RunRecord:
    # Check existence here so unknown IDs always receive a stable 404 even if
    # an orchestrator implementation raises a different lookup exception.
    _incident_packet_or_404(incident_id)
    verdict = _as_verdict(deliberate(incident_id))
    return run_store.add(incident_id, verdict)


@app.get("/runs/{run_id}", response_model=RunRecord)
def run(run_id: str) -> RunRecord:
    record = run_store.get(run_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' was not found.",
        )
    return record


@app.post("/runs/{run_id}/bias-audit", response_model=BiasAuditResult)
def bias_audit(run_id: str) -> BiasAuditResult:
    record = run_store.get(run_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' was not found.",
        )

    raw_result = audit_bias(record.incident_id)
    serializable_result = (
        raw_result.model_dump(mode="json")
        if isinstance(raw_result, BaseModel)
        else raw_result
    )
    result = BiasAuditResult(
        run_id=run_id,
        incident_id=record.incident_id,
        passed=_audit_passed(raw_result),
        result=serializable_result,
    )
    return run_store.attach_audit(result)


@app.get("/evaluation/summary", response_model=EvaluationSummary)
def evaluation_summary() -> EvaluationSummary:
    runs, audits = run_store.snapshot()
    counts: Dict[str, int] = {}
    for record in runs:
        decision = record.verdict.decision
        counts[decision] = counts.get(decision, 0) + 1

    passed = [audit.passed for audit in audits if audit.passed is not None]
    pass_rate = (
        sum(1 for result in passed if result) / len(passed) if passed else None
    )
    average_confidence = (
        sum(record.verdict.confidence for record in runs) / len(runs)
        if runs
        else 0.0
    )
    return EvaluationSummary(
        completed_runs=len(runs),
        unique_incidents=len({record.incident_id for record in runs}),
        average_confidence=average_confidence,
        decision_counts=counts,
        bias_audits=len(audits),
        bias_audit_pass_rate=pass_rate,
    )

