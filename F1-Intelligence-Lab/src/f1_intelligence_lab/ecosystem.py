"""Shared catalogue and evidence-backed tools for the local F1 ecosystem."""
import re
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from stewardlens.repository import list_real_decisions
from telemetry_pit_crew.api import service

router = APIRouter(prefix="/api/ecosystem", tags=["ecosystem"])

PROJECTS = [
    {"id": "race-lab", "name": "Race Lab", "category": "Performance", "path": "/race-lab/", "description": "Analyze race lap pace, stints and pit events. Import your own CSV or explore a labelled synthetic exercise."},
    {"id": "telemetry", "name": "Telemetry Pit Crew", "category": "Performance", "path": "/telemetry/", "description": "Compare laps through braking, cornering, traction and straight-line findings."},
    {"id": "stewardlens", "name": "StewardLens", "category": "Race control", "path": "/stewardlens/", "description": "Inspect incident evidence and run a simulated steward deliberation."},
    {"id": "pitwall", "name": "Pitwall Replay", "category": "Performance", "path": "/pitwall/", "description": "Replay recorded lap telemetry with a shared clock, scrubbing and speed controls."},
    {"id": "scoutgrid", "name": "ScoutGrid", "category": "Performance", "path": "/scoutgrid/", "description": "Explore the available drivers and compare recorded lap times and speed ranges."},
    {"id": "claimcheck", "name": "ClaimCheck", "category": "Evidence", "path": "/claimcheck/", "description": "Check numerical timing and penalty claims against the cached source records."},
    {"id": "archive", "name": "FIA Archive", "category": "Evidence", "path": "/archive/", "description": "Search official decision records and inspect their original document references."},
]


def session_or_404(session_id):
    session = service.sessions.get(session_id)
    if session is None:
        raise HTTPException(404, "Session is not in the local data catalogue.")
    return session


@router.get("/catalog")
def catalog():
    sessions = service.list_sessions()
    return {"projects": PROJECTS, "sessions": sessions,
            "recorded_sessions": sum(s["source_type"] != "synthetic" for s in sessions),
            "synthetic_sessions": sum(s["source_type"] == "synthetic" for s in sessions),
            "official_documents": len(list_real_decisions()),
            "scope": "Local research MVPs; deterministic analysis; no live race feed or external LLM."}


@router.get("/scout")
def scout(session_id: str):
    session = session_or_404(session_id)
    laps = sorted(service.list_laps(session_id), key=lambda lap: lap.lap_time)
    best = laps[0].lap_time if laps else 0
    rows = [{"lap_id": lap.id, "driver": lap.driver, "lap_number": lap.lap_number,
             "lap_time": lap.lap_time, "gap_to_fastest": round(lap.lap_time - best, 6),
             "top_speed": max((s.speed for s in lap.samples), default=None),
             "minimum_speed": min((s.speed for s in lap.samples), default=None),
             "samples": len(lap.samples), "compound": lap.compound}
            for lap in laps]
    return {"session": session, "rows": rows,
            "limitation": "Ranking covers only these cached laps. It is not a full qualifying classification or a driver-talent score. Speed extrema come from sampled telemetry."}


@router.get("/replay")
def replay(session_id: str):
    session = session_or_404(session_id)
    laps = service.list_laps(session_id)
    return {"session": session, "laps": [lap.model_dump() for lap in laps],
            "duration": max((lap.lap_time for lap in laps), default=0),
            "limitation": "Lap-relative playback, not a simultaneous race replay. Each sample is held until the next recorded timestamp. Progress uses elapsed lap time, not GPS position; missing coverage is shown explicitly."}


class Claim(BaseModel):
    kind: Literal["lap_time", "lap_delta", "penalty_seconds"]
    value: float = Field(allow_inf_nan=False, ge=-100000, le=100000)
    session_id: Optional[str] = None
    lap_a_id: Optional[str] = None
    lap_b_id: Optional[str] = None
    decision_id: Optional[str] = None


@router.post("/check")
def check_claim(claim: Claim):
    if claim.kind == "penalty_seconds":
        decision = next((d for d in list_real_decisions() if d["id"] == claim.decision_id), None)
        if decision is None:
            raise HTTPException(404, "Select a decision from the official archive.")
        match = re.search(r"(\d+(?:\.\d+)?)\s+second", decision["decision"], flags=re.I)
        if not match:
            return {"status": "insufficient_evidence", "reason": "This record does not specify a time penalty in seconds."}
        observed = float(match.group(1))
        evidence = {"label": f"FIA document {decision['document_number']} — {decision['driver_name']}",
                    "url": decision["source_document_url"], "sha256": decision["sha256"],
                    "source_type": "official_fia", "record_id": decision["id"]}
    else:
        session = session_or_404(claim.session_id)
        ids = session["lap_ids"]
        if claim.lap_a_id not in ids:
            raise HTTPException(422, "Driver A must be a lap from the selected session.")
        a = service.laps[claim.lap_a_id]
        observed = a.lap_time
        label = f"{session['name']} — {a.driver}, lap {a.lap_number}"
        if claim.kind == "lap_delta":
            if claim.lap_b_id not in ids or claim.lap_a_id == claim.lap_b_id:
                raise HTTPException(422, "Choose two different laps from the same session.")
            b = service.laps[claim.lap_b_id]
            observed -= b.lap_time
            label += f" minus {b.driver}, lap {b.lap_number}"
        evidence = {"label": label, "source_type": session["source_type"],
                    "url": "/telemetry/laps/" + a.id + "/telemetry",
                    "source_urls": session.get("source_endpoints", []),
                    "session_id": session["id"], "lap_a_id": a.id,
                    "lap_b_id": claim.lap_b_id if claim.kind == "lap_delta" else None}
    difference = abs(claim.value - observed)
    return {"status": "supported" if difference <= 0.001000001 else "contradicted",
            "claimed": claim.value, "observed": round(observed, 6), "unit": "seconds",
            "tolerance_seconds": 0.001, "evidence": evidence,
            "scope": "Numerical record check only; does not establish causality, intent, or general truth."}
