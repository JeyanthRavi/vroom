# F1 Intelligence Lab

Planning the next stage: [complete website and Android ecosystem blueprint](blueprint/README.md). This is proposed work, separate from the implemented local tools described below.

F1 Intelligence Lab is a local analysis product, separate from the planned News & Stories product. The default homepage is now **Race Lab**; the original directory is at `/workstations/`.

## Race Lab — first race-level slice

**Historical data is now supported:** open `/library/` to import real sessions and retain them across restarts. [Historical library guide and measured limits](HISTORICAL-LIBRARY.md). Saved races are preferred over the demo; imports are shared with ScoutGrid, Replay, Telemetry and ClaimCheck. The CSV path below remains ephemeral.

Open `http://127.0.0.1:8765/` (or `/race-lab/`). Includes responsive lap-pace charts, driver filters, beginner/analyst explanations, observed stint timelines, pit-in markers, eligible-lap medians, unadjusted stint trends, exact lap tables and JSON export.

The bundled 30-lap, three-driver exercise is **synthetic**, not a real Grand Prix. Import a UTF-8 CSV through the UI using the downloadable template. CSV imports are analyzed in memory, not persisted or shared with the original workstation catalogue. Refresh restores the selected saved race, or a saved default, or the demo when no races are available. No paid service, external AI, trained ML model or live feed is required.

CSV header: `driver,lap,lap_time,compound,stint,pit,flag`. Times are seconds; pit=1 marks the pit-in lap; flags are GREEN/SC/VSC/RED/UNKNOWN. Maximum 500 KB, 5,000 records and 30 drivers. Duplicate driver/lap pairs, nonfinite times and inconsistent stints are rejected. Eligible pace excludes lap 1, non-GREEN laps, pit-in laps and their following out-laps. Stint slope requires three eligible laps and is **not isolated tyre degradation**. No classification or causal strategy claim is inferred.

API: `GET /api/races/demo`, `GET /api/races/template`, `POST /api/races/analyze` with `{ "name": "My race", "csv": "..." }`. Run locally; this is not an authenticated public upload service.

Its directory preserves the six original tools:

- **StewardLens** — an evidence-grounded, multi-agent simulated steward review.
- **Telemetry Pit Crew** — a multi-agent lap-comparison and engineering debrief.
- **Pitwall Replay** — playback, pause, speed selection and scrubbing of cached lap telemetry on a shared lap-relative clock.
- **ScoutGrid** — sortable recorded-lap comparisons, sampled speed extrema and JSON report export.
- **ClaimCheck** — numerical checks of lap times, signed lap differences and official time penalties, with source references and report export.
- **FIA Archive** — searchable official decisions with source PDFs and SHA-256 references.

The original projects remain separately runnable. The new tools live in
`src/f1_intelligence_lab/ecosystem.py` and `ecosystem_web.py`, and reuse the
original service and repository instances. No duplicate telemetry dataset is maintained.

### Current scope

This is a set of local, deterministic research MVPs. The bundled catalogue has
one real session (2024 Monza qualifying, Norris and Piastri), one synthetic session,
and two official FIA decisions. FastF1 sessions loaded through Telemetry appear
in the other tools without restarting the service. There is no live race feed,
external LLM integration, scouting talent model, or general-purpose fact checker.

Pitwall Replay aligns laps at elapsed lap time zero; it does not reconstruct
simultaneous race positions. It holds each recorded sample until the next timestamp,
and displays missing coverage explicitly. Its progress bars represent elapsed
lap time, not GPS position. ScoutGrid ranks only the available laps in the chosen
session, not the entire field. ClaimCheck accepts three structured numeric claim
types; unsupported claim types are rejected. Its comparison tolerance is 0.001 seconds.

The portal does not merge their source code. It imports and mounts the existing
FastAPI applications at `/stewardlens/` and `/telemetry/`, keeping both projects
independently testable and runnable.

## Requirements

- Python 3.9 or newer.
- The neighboring `F1-StewardLens` and `F1-Telemetry-Pit-Crew` directories.

The expected workspace layout is:

```text
projects folder/
├── F1-Intelligence-Lab/
├── F1-StewardLens/
└── F1-Telemetry-Pit-Crew/
```

## One-command setup

From the workspace root:

```bash
bash F1-Intelligence-Lab/scripts/setup.sh
```

The script creates `F1-Intelligence-Lab/.venv` and installs the portal and both
neighboring projects in editable mode, including the optional FastF1 adapter.

## Run

```bash
cd F1-Intelligence-Lab
source .venv/bin/activate
uvicorn f1_intelligence_lab.app:app --reload
```

Then open <http://127.0.0.1:8000>.

| URL | Purpose |
| --- | --- |
| `/` | Unified project portal. |
| `/stewardlens/` | StewardLens browser interface. |
| `/telemetry/` | Telemetry Pit Crew browser interface. |
| `/pitwall/` | Pitwall Replay playback workbench. |
| `/scoutgrid/` | ScoutGrid driver/lap explorer. |
| `/claimcheck/` | ClaimCheck numerical evidence checks. |
| `/archive/` | Searchable FIA decision archive. |
| `/api/ecosystem/catalog` | Shared project and session catalogue. |
| `/api/ecosystem/scout?session_id=2024-monza-q` | Recorded-lap statistics. |
| `/api/ecosystem/replay?session_id=2024-monza-q` | Replay data and timing scope. |
| `/api/ecosystem/check` | POST a supported numeric claim. |
| `/health` | Portal and mount readiness. |
| `/docs` | Portal OpenAPI documentation. |

The two existing browser interfaces use root-absolute fetch paths. The portal
provides hidden compatibility routes for those requests while keeping each
canonical API available under its mounted prefix.

## Test

```bash
cd F1-Intelligence-Lab
source .venv/bin/activate
pytest
```

The integration tests verify the landing page, health contract, both mounted
applications, their sample datasets, compatibility routes, and portal schema.

## ML dataset foundation

The historical race audit and leakage-controlled feature pipeline are documented in
[ML-DATA-PREPARATION.md](ML-DATA-PREPARATION.md). It preserves the source library,
quarantines unverified sessions, and creates whole-race chronological partitions.
This is dataset preparation, not a trained-model accuracy claim.

## Container deployment

The Dockerfile expects the workspace folder containing all three neighboring
projects as its build context:

```bash
docker build -f F1-Intelligence-Lab/Dockerfile -t f1-intelligence-lab .
docker run --rm -p 8000:8000 f1-intelligence-lab
```

Hosting services should start the container with their assigned `PORT`
environment variable. No API key is required for the reproducible baseline.

## Data and usage notice

This is an educational research prototype. StewardLens includes a small
checksum-verified official FIA document archive alongside clearly separated
agent-demo fixtures. Telemetry Pit Crew supports cached public FastF1 data and
an explicit synthetic fallback. Neither project is an official Formula 1,
team, or FIA system, and its outputs are not official stewarding or
engineering advice.

