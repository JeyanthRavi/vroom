# Consolidated research results

## Evidence status

The Phase 4 RQ1–RQ4 runs are **fixture-only: not evidence** because the audited split files needed by the new adapters were unavailable. They demonstrate deterministic pipelines, artifact contracts, metrics, leakage checks, and model execution. They do not support Formula 1 model-performance or résumé-number claims.

## RQ1 — Pace and hazard

<!-- BEGIN GENERATED: rq1-results -->
**Fixture-only: not evidence.**

| Horizon | Model | Brier | PR-AUC | ECE |
|---:|---|---:|---:|---:|
| 1 | base_rate | 0.069 | 0.075 | 0.008 |
| 1 | logistic | 0.002 | 1.000 | 0.047 |
| 1 | boosting | 0.243 | 0.057 | 0.298 |
| 1 | small_tcn | 0.250 | 0.075 | 0.425 |
| 3 | base_rate | 0.119 | 0.138 | 0.000 |
| 3 | logistic | 0.293 | 0.613 | 0.447 |
| 3 | boosting | 0.334 | 0.107 | 0.383 |
| 3 | small_tcn | 0.246 | 0.164 | 0.357 |
<!-- END GENERATED: rq1-results -->

Method: a conditional green-lap pace regressor is combined with H=1/H=3 neutralisation classifiers. Base rate, weighted logistic regression, and histogram boosting report PR-AUC, ROC-AUC, Brier, log loss, ten-bin calibration, and mixed-target regression against the rolling-median baseline.

Interpretation: the fixture verifies the two-stage code path. Synthetic scores are deliberately not interpreted as improvement. Real-data success/failure remains pending.

## RQ2 — Conformal uncertainty

<!-- BEGIN GENERATED: rq2-results -->
**Fixture-only: not evidence.**

| Method | Nominal | Coverage | Wilson 95% | Width (s) |
|---|---:|---:|---|---:|
| cqr_80 | 0.800 | 0.562 | [0.453, 0.666] | 7.933 |
| cqr_90 | 0.900 | 0.925 | [0.846, 0.965] | 60.461 |
| split_80 | 0.800 | 0.375 | [0.277, 0.485] | 1.641 |
| split_90 | 0.900 | 0.925 | [0.846, 0.965] | 50.591 |
<!-- END GENERATED: rq2-results -->

Method: 2025-style train/calibration/test fixture races remain disjoint. Split conformal and CQR report 80%/90% coverage, Wilson intervals, widths and interval scores; Mondrian output abstains when a group has fewer than 30 calibration rows.

Interpretation: bounds and calibration accounting execute deterministically. Synthetic coverage is not evidence of real calibration. Real-data success/failure remains pending.

## RQ3 — Shift diagnostics

<!-- BEGIN GENERATED: rq3-results -->
**Fixture-only: deliberately injected shift; not evidence.**

| Feature | PSI | KS statistic |
|---|---:|---:|
| cars_in_pit_window | 0.000 | 0.000 |
| lap | 0.000 | 0.000 |
| local_yellows | 0.000 | 0.000 |
| pace_variance | 9.140 | 1.000 |
| rolling_median_5 | 12.434 | 0.963 |
| tyre_age_gap | 0.000 | 0.000 |
<!-- END GENERATED: rq3-results -->

Method: the fixture injects a known synthetic shift, then exercises PSI, KS, race-grouped adversarial validation, a rolling error timeline, plots and alt text.

Interpretation: the pipeline detects the intentionally injected fixture shift. This does not explain real 2025→2026 degradation. Adaptation comparison remains pending audited splits.

## RQ4 — Sequence fairness

<!-- BEGIN GENERATED: rq4-results -->
**Fixture-only: one pre-specified ablation cell; not evidence.**

| Model | Parameters | Equal-race MAE (s) |
|---|---:|---:|
| rolling_median_5 | — | 3.077 |
| gru | 344 | 4.953 |
| mlp | 721 | 3.496 |
| sequence_boosting | tree_not_comparable | 3.200 |
| tcn | 333 | 3.466 |
<!-- END GENERATED: rq4-results -->

Method: every 5/10/15-lap × race-state on/off × tyre on/off cell runs sequence boosting, GRU, TCN and parameter-matched MLP controls. Neural candidates use seeds 11, 29 and 47 and always show the rolling-median baseline.

Interpretation: architecture, ablation, deterministic seed and artifact paths execute on fixtures. No superiority conclusion is permitted. CPU timing and real-data model comparison remain pending.

## StewardLens feasibility evaluation

<!-- BEGIN GENERATED: steward-results -->
**Small mixed metadata/synthetic feasibility set; not official-decision performance evidence.**

| Cases | Retrieval recall@k | MRR | Citation integrity | Identity swaps | Flip rate |
|---:|---:|---:|---:|---:|---:|
| 10 | 0.900 | 0.733 | 0.838 | 3 | 0.000 |

The per-class report in the source artifact includes a zero-recall class; no aggregate score is promoted as a claim.
<!-- END GENERATED: steward-results -->

Interpretation: the small mixed metadata/synthetic set validates the evaluation
path and exposes class failures. It does not establish that StewardLens predicts
official outcomes. Retrieval and identity-swap metrics are scoped to this fixture.

## Forward holdout

**Forward holdout pending.** It requires at least three verified races starting strictly after 2026-11-02 and must be opened once by the frozen script.
