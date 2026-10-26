# Vroom — F1 Race Intelligence

A research web platform for exploring Formula 1 results, driver pace, tyre stints, pit stops, race-control events, telemetry, and official FIA decisions.

## Project layout

- [F1 Intelligence Lab](F1-Intelligence-Lab/README.md): unified website, historical race library, race detail pages, and ML dataset pipeline.
- [StewardLens](F1-StewardLens/README.md): evidence-grounded simulated steward reviews and FIA document archive.
- [Telemetry Pit Crew](F1-Telemetry-Pit-Crew/README.md): lap comparisons and engineering debriefs.

## Run locally

Requires Python 3.9 or newer.

```bash
bash F1-Intelligence-Lab/scripts/setup.sh
cd F1-Intelligence-Lab
source .venv/bin/activate
uvicorn f1_intelligence_lab.app:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765/. Import historical races through the library; the original machine's saved race database and downloaded caches are not included. Bundled sample fixtures remain included and are identified in the component documentation.

## Machine learning status

The project includes an audited next-lap prediction dataset pipeline with 13 features, whole-race chronological splits, and a separate 2026 holdout. The local audit accepted 38 races. Generated datasets and audit outputs are excluded from this repository; see [data preparation](F1-Intelligence-Lab/ML-DATA-PREPARATION.md) for the workflow and limitations.

**No model has been trained yet.** Baseline comparison and first-model training are the next step. Existing analysis and simulated agents do not require a trained ML model or paid LLM service.

## Scope and safety

This is a local educational prototype, not a production-hardened public service. Do not expose its import endpoints publicly without authentication and operational hardening. It is not affiliated with Formula 1, the FIA, or any team. Linked documents and third-party data remain subject to their owners' rights and terms; analysis is not official stewarding or engineering advice.

The ecosystem blueprint describes proposed features, not completed functionality.
