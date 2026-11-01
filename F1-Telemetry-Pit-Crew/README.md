# Telemetry Pit Crew

> **Data-rights notice:** this is an unofficial research project. OpenF1/FastF1-derived data and all third-party marks remain with their owners. See [the repository notice](../NOTICE.md) and [the current data-rights review](../F1-Intelligence-Lab/DATA-RIGHTS-REVIEW.md).

A web-based, evidence-linked multi-agent Formula 1 lap analysis project. It compares telemetry traces, computes deterministic evidence, and asks four specialist agents to explain the most important performance differences.

![Status](https://img.shields.io/badge/status-runnable-34c759) ![Python](https://img.shields.io/badge/python-3.9%2B-3776ab)

## What is included

- A polished responsive dashboard with lap and session selectors.
- Dependency-free SVG overlays for speed and throttle telemetry.
- Braking, cornering, traction and straight-line specialist agents.
- A race-engineer synthesis with evidence IDs, confidence and limitations.
- A compact real-data fixture: Norris vs Piastri in 2024 Monza qualifying.
- An explicit synthetic fallback that works without internet access.
- Optional on-demand session loading through the official FastF1 Python package.
- FastAPI endpoints suitable for a separate React or mobile client later.

## Run the website

```bash
cd F1-Telemetry-Pit-Crew
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn telemetry_pit_crew.main:app --reload --port 8001
```

Open <http://127.0.0.1:8001>. The real cached Monza comparison is selected automatically. No API key or network connection is required.

## Load another real session

Install the optional FastF1 dependency:

```bash
pip install -e '.[f1,dev]'
```

Expand **Load another session with FastF1** in the website and provide a year, event, session code and at least two three-letter driver abbreviations. The initial download can take several minutes and is cached in `.fastf1-cache`.

The equivalent Python call is:

```python
from telemetry_pit_crew.ingestion import load_fastest_laps

metadata, laps = load_fastest_laps(2024, "Monza", "Q", ["NOR", "PIA"])
```

Normal startup never performs a network request. The on-demand endpoint is intentionally explicit:

```http
POST /sessions/fastf1
Content-Type: application/json

{"year": 2024, "event": "Monza", "session_code": "Q", "drivers": ["NOR", "PIA"]}
```

## API

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/sessions` | List synthetic, cached and runtime-loaded sessions |
| `GET` | `/laps?session_id=…` | List selectable laps without bulky sample arrays |
| `GET` | `/laps/{lap_id}/telemetry` | Return chart-ready telemetry |
| `POST` | `/comparisons` | Run the multi-agent debrief |
| `POST` | `/sessions/fastf1` | Explicitly download fastest laps through FastF1 |
| `GET` | `/docs` | Interactive OpenAPI documentation |

## Test

```bash
pytest -q
```

The tests use local fixtures only and never require network access.

## Data provenance and limitations

The bundled `data/2024_monza_q.json` fixture contains compact, processed telemetry from the [OpenF1](https://openf1.org/) `laps` and `car_data` endpoints for session key `9586`. The exact source endpoint URLs are stored in the fixture. It includes the fastest qualifying laps of Lando Norris and Oscar Piastri at Monza in 2024. Distance is approximated by integrating sampled speed, so analytical phase boundaries are not official corner boundaries.

The optional runtime adapter uses [FastF1](https://docs.fastf1.dev/) and its documented public timing-data interface. FastF1 software is MIT-licensed; the underlying Formula 1 timing data, names and marks remain subject to their original rights and terms. This educational project is unofficial and is not affiliated with Formula 1, the FIA, any team or driver. Do not use its output for safety-critical, betting or official sporting decisions.

Public telemetry does not expose steering angle, tyre temperature, fuel load or car setup. Agent findings describe measured correlations; they do not prove a driver's intent or a car's underlying setup.
