# Consolidated research results

## Evidence status

The Phase 4 RQ1–RQ4 runs are **fixture-only: not evidence** because the audited split files needed by the new adapters were unavailable. They demonstrate deterministic pipelines, artifact contracts, metrics, leakage checks, and model execution. They do not support Formula 1 model-performance or résumé-number claims.

## RQ1 — Pace and hazard

Method: a conditional green-lap pace regressor is combined with H=1/H=3 neutralisation classifiers. Base rate, weighted logistic regression, and histogram boosting report PR-AUC, ROC-AUC, Brier, log loss, ten-bin calibration, and mixed-target regression against the rolling-median baseline.

Interpretation: the fixture verifies the two-stage code path. Synthetic scores are deliberately not interpreted as improvement. Real-data success/failure remains pending.

## RQ2 — Conformal uncertainty

Method: 2025-style train/calibration/test fixture races remain disjoint. Split conformal and CQR report 80%/90% coverage, Wilson intervals, widths and interval scores; Mondrian output abstains when a group has fewer than 30 calibration rows.

Interpretation: bounds and calibration accounting execute deterministically. Synthetic coverage is not evidence of real calibration. Real-data success/failure remains pending.

## RQ3 — Shift diagnostics

Method: the fixture injects a known synthetic shift, then exercises PSI, KS, race-grouped adversarial validation, a rolling error timeline, plots and alt text.

Interpretation: the pipeline detects the intentionally injected fixture shift. This does not explain real 2025→2026 degradation. Adaptation comparison remains pending audited splits.

## RQ4 — Sequence fairness

Method: every 5/10/15-lap × race-state on/off × tyre on/off cell runs sequence boosting, GRU, TCN and parameter-matched MLP controls. Neural candidates use seeds 11, 29 and 47 and always show the rolling-median baseline.

Interpretation: architecture, ablation, deterministic seed and artifact paths execute on fixtures. No superiority conclusion is permitted. CPU timing and real-data model comparison remain pending.

## Forward holdout

**Forward holdout pending.** It requires at least three verified races starting strictly after 2026-11-02 and must be opened once by the frozen script.
