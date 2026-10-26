from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .service import TelemetryService
from .web import page

app = FastAPI(title="Telemetry Pit Crew", version="0.2.0")
service = TelemetryService()


class ComparisonRequest(BaseModel):
    lap_a_id: str
    lap_b_id: str


class FastF1SessionRequest(BaseModel):
    year: int = Field(ge=2018, le=2100)
    event: str = Field(min_length=2, max_length=80)
    session_code: str = Field(pattern="^(FP1|FP2|FP3|Q|SQ|S|R)$")
    drivers: list[str] = Field(min_length=2, max_length=6)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return page()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/sessions")
def sessions() -> list[dict]:
    return service.list_sessions()


@app.post("/sessions/fastf1")
def load_session(request: FastF1SessionRequest) -> dict:
    try:
        return service.load_fastf1_session(
            request.year, request.event, request.session_code,
            [driver.strip().upper() for driver in request.drivers if driver.strip()],
        )
    except (RuntimeError, ValueError, OSError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/laps")
def laps(session_id: Optional[str] = Query(default=None), offset: int = Query(default=0, ge=0), limit: int = Query(default=500, ge=1, le=500)) -> list[dict]:
    try:
        return service.list_lap_summaries(session_id)[offset:offset+limit]
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/laps/{lap_id}/telemetry")
def telemetry(lap_id: str) -> dict:
    if lap_id not in service.laps:
        raise HTTPException(404, "Unknown lap id")
    return service.laps[lap_id].model_dump()


@app.post("/comparisons")
def compare(request: ComparisonRequest) -> dict:
    try:
        return service.compare(request.lap_a_id, request.lap_b_id).model_dump()
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
