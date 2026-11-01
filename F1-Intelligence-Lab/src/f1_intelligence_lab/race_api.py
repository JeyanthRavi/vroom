"""HTTP adapter for ephemeral race analysis."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from .race_analysis import analyze, demo_csv

router = APIRouter()
ASSETS = Path(__file__).parent / "static"


class RaceImport(BaseModel):
    name: str = Field(default="Imported race", min_length=1, max_length=100)
    csv: str = Field(min_length=1, max_length=500_000)


@router.get("/race-lab/", response_class=HTMLResponse, include_in_schema=False)
def page():
    return (ASSETS / "race.html").read_text()


@router.get("/race-assets/{asset}", include_in_schema=False)
def asset(asset: str):
    types = {"race.css": "text/css", "race.js": "application/javascript"}
    if asset not in types:
        raise HTTPException(404, "Asset not found")
    return Response((ASSETS / asset).read_text(), media_type=types[asset])


@router.get("/api/races/demo", tags=["race analysis"])
def demo():
    return analyze(demo_csv(), "Switchback · 30-lap strategy exercise", "synthetic")


@router.get("/api/races/template", response_class=PlainTextResponse, tags=["race analysis"])
def template():
    return PlainTextResponse(demo_csv(), headers={"Content-Disposition": 'attachment; filename="synthetic-race-template.csv"'})


@router.post("/api/races/analyze", tags=["race analysis"])
def import_race(payload: RaceImport):
    try:
        return analyze(payload.csv, payload.name.strip() or "Imported race")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
