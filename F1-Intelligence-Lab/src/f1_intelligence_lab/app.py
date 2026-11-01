"""Unified ASGI entry point for both F1 intelligence projects."""

from __future__ import annotations

from typing import Dict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from stewardlens.api import app as stewardlens_app
from telemetry_pit_crew.api import app as telemetry_app

from .web import HOME_HTML
from .ecosystem import router as ecosystem_router
from .ecosystem_web import ecosystem_page
from .race_api import router as race_router, page as race_page
from .library_api import router as library_router
from .race_detail import router as detail_router
from .ml_api import router as ml_router
from .demo_api import router as demo_router


app = FastAPI(
    title="F1 Intelligence Lab",
    version="0.1.0",
    description="One local portal for two evidence-linked Formula 1 agent systems.",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return race_page()


@app.get("/workstations/", response_class=HTMLResponse, include_in_schema=False)
def workstations() -> str:
    return ecosystem_page("hub")


@app.get("/pitwall/", response_class=HTMLResponse, include_in_schema=False)
def pitwall() -> str:
    return ecosystem_page("pitwall")


@app.get("/scoutgrid/", response_class=HTMLResponse, include_in_schema=False)
def scoutgrid() -> str:
    return ecosystem_page("scoutgrid")


@app.get("/claimcheck/", response_class=HTMLResponse, include_in_schema=False)
def claimcheck() -> str:
    return ecosystem_page("claimcheck")


@app.get("/archive/", response_class=HTMLResponse, include_in_schema=False)
def archive() -> str:
    return ecosystem_page("archive")


app.include_router(ecosystem_router)
app.include_router(race_router)
app.include_router(library_router)
app.include_router(detail_router)
app.include_router(ml_router)
app.include_router(demo_router)


@app.get("/health", tags=["operations"])
def health() -> Dict[str, object]:
    """Report portal readiness and the mounted application topology."""

    return {
        "status": "ok",
        "services": {
            "stewardlens": {"status": "mounted", "path": "/stewardlens/"},
            "telemetry": {"status": "mounted", "path": "/telemetry/"},
        },
    }


# Both original frontends currently use root-absolute API paths. Re-exporting
# their routers without documentation keeps those existing pages functional
# inside the portal while their canonical APIs remain available at the mounted
# prefixes below. Portal routes are registered first, so its home and health
# pages retain ownership of `/` and `/health`.
app.include_router(stewardlens_app.router, include_in_schema=False)
app.include_router(telemetry_app.router, include_in_schema=False)

app.mount("/stewardlens", stewardlens_app, name="stewardlens")
app.mount("/telemetry", telemetry_app, name="telemetry")


__all__ = ["app"]

