# Evidence-backed résumé bullet bank

Use only bullets whose scope matches the cited artifact. Fixture-only work can
support engineering claims, not model-performance claims.

## 1. Reproducible ML evaluation

**Bullet:** Built a leakage-controlled Formula 1 next-lap forecasting pipeline with whole-race chronological splits, rolling baselines, gradient boosting, GRU models, immutable manifests, and race-level evaluation.

**Evidence:** `research/PROTOCOL.md`; `F1-Intelligence-Lab/MODEL-CARD.md`; `F1-Intelligence-Lab/demo-export-final/data.json`.

**Numbers:** Use only the generated table in `F1-Intelligence-Lab/MODEL-CARD.md`.

**Do not say:** unseen 2026, live prediction, production model, or universally outperformed the baseline.

## 2. Honest evaluation under shift

**Bullet:** Diagnosed cross-season degradation and kept a rolling-median baseline beside learned models, reporting the previously examined 2026 cohort as a non-independent regression check.

**Evidence:** `README.md#results-summary`; `research/runs/rq3-fixture/results.json`; `F1-Intelligence-Lab/CROSS-SEASON-2026.md`.

**Numbers:** Generated in `README.md`; the RQ3 values are fixture-only.

**Do not say:** proved the cause of drift or validated on an untouched 2026 holdout.

## 3. Calibrated-uncertainty engineering

**Bullet:** Implemented split conformal and conformalized quantile-regression evaluation with disjoint calibration races, Wilson coverage intervals, interval scores, and additive API bounds.

**Evidence:** `research/PROTOCOL.md#rq2`; `research/runs/rq2-fixture/manifest.json`; `F1-Intelligence-Lab/tests/test_research_conformal.py`.

**Numbers:** **NOT YET SUPPORTED** on real data; fixture table is generated in `research/RESULTS.md`.

**Do not say:** calibrated Formula 1 uncertainty until the audited real-data protocol runs.

## 4. Event-risk modelling

**Bullet:** Built a two-stage pace and race-neutralisation research pipeline comparing base-rate, logistic, boosted-tree, and compact TCN hazard models with calibration and per-race/per-circuit diagnostics.

**Evidence:** `research/runs/rq1-fixture/manifest.json`; `F1-Intelligence-Lab/src/f1_intelligence_lab/research/hazard.py`.

**Numbers:** **NOT YET SUPPORTED** on real data.

**Do not say:** predicts real safety cars or improves real race forecasts.

## 5. Fair sequence-model comparison

**Bullet:** Implemented CPU-reproducible GRU, TCN, MLP, and sequence-boosting ablations across history length, race-state, tyre context, and three fixed seeds.

**Evidence:** `research/runs/rq4-fixture/manifest.json`; `research/RESULTS.md#rq4--sequence-fairness`.

**Numbers:** Fixture-only parameter and MAE table is generated; no superiority claim is supported.

**Do not say:** deep learning beats boosting.

## 6. Measured NLP system

**Bullet:** Extended a deterministic steward simulator with offline TF-IDF retrieval, stratified logistic-regression feasibility evaluation, strict citation integrity, Wilson-scored identity swaps, and an optional model-agent boundary.

**Evidence:** `research/runs/stewardlens-feasibility/results.json`; `F1-StewardLens/tests/test_evaluation.py`; `F1-StewardLens/tests/test_model_agent.py`.

**Numbers:** Generated in `research/RESULTS.md`; small mixed metadata/synthetic set only.

**Do not say:** AI steward, FIA decision predictor, unbiased system, or transformer-trained system.

## 7. Safe static deployment

**Bullet:** Shipped a checksum-verified aggregate replay with authenticated write paths, CSP/security headers, rights-safe defaults, generated methodology views, and a sub-megabyte static package.

**Evidence:** `F1-Intelligence-Lab/demo-export-final/manifest.json`; `NOTICE.md`; `F1-Intelligence-Lab/tests/test_demo_api.py`.

**Numbers:** Final package size and release tests are recorded in `FINAL-REPORT.md`.

**Do not say:** rights-cleared public data, production SLA, or official Formula 1 application.

## 8. Release engineering

**Bullet:** Added Python 3.9/3.12 CI, no-Torch and CPU-Torch gates, Docker build jobs, pinned environments, one-command reproduction, generated result tables, and clean-clone verification.

**Evidence:** `.github/workflows/ci.yml`; `requirements-lock.txt`; `scripts/reproduce.sh`; `PROGRESS-LOG.md#phase-9--final-qa--2026-11-02`.

**Numbers:** Use the literal final gate counts in `FINAL-REPORT.md`.

**Do not say:** remote CI/Docker verified until the GitHub Actions run passes.
