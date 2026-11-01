# Vroom: measured ML / DL research results

Year-audit correction: the original training split included 13 races from 2025,
2023 Singapore and 2024 Suzuka. Any description of this original run as
2025-only was inaccurate. The [restart experiment](RESTART-MODELS.md) trains
and tunes strictly on 2025; original artifacts and metrics remain unchanged.

Update, 28 October: [2026 evaluation](CROSS-SEASON-2026.md) is now complete and
revealed a substantial generalization gap. References below to an unopened 2026
set describe the original 27 October experiment, not its current status.

Completed 27 October 2026, CPU-only with PyTorch 2.8.0. Fixed training run took
26 seconds after dependencies were installed. No paid compute was used.

Verification: 139 tests passed. A complete second training run reproduced every
aggregate metric, every seed metric and the benchmark prediction CSV exactly.
The website comparison and existing inference endpoint were checked locally.

## What was built

- A 10-completed-lap sequence pipeline, restricted to one driver/race and checked
  against frozen source hashes and prediction timestamps.
- A 4,857-parameter GRU plus context branch, predicting residual next-lap time.
- Three seeds per variant: full, no tyre features, and no race-control features.
- Last-lap, rolling mean/median, 13-feature boosting, and sequence-feature boosting
  comparators on exactly the same rows.
- Train-only encoders, deterministic CPU training, early stopping, restricted
  weight reloads, source/artifact hashes, and per-race/condition diagnostics.
- A read-only experiment comparison on the race-detail website. The existing
  three-lap prediction service is unchanged; this is not live GRU deployment.

## Data and metrics

Training: 6,876 examples / 15 races. Validation: 2,285 / 5 races.
Reused 2025 benchmark: 1,452 / 3 races. All 23 races are chronological partitions.
2026 remains reserved and was not read. Incomplete histories are excluded, not
interpolated. This cohort differs from the original three-lap experiment.

| Model | Validation race MAE (s) | Benchmark race MAE (s) | Benchmark pooled RMSE (s) | Benchmark pooled R² |
|---|---:|---:|---:|---:|
| Last lap | 1.4882 | 2.0479 | 6.8085 | 0.1170 |
| Rolling mean | 1.5126 | 2.5093 | 7.1865 | 0.0162 |
| Rolling median | 1.1807 | 2.0570 | 7.2710 | -0.0071 |
| 13-feature boosting | 0.9699 | 1.1768 | 4.4502 | 0.6227 |
| Sequence boosting | **0.8521** | **0.9872** | **3.2731** | **0.7959** |
| Full GRU ensemble | 1.0244 | 1.2566 | 4.7828 | 0.5643 |
| GRU without tyre inputs | 0.9846 | 1.2909 | 4.9116 | 0.5405 |
| GRU without control inputs | 0.9722 | 1.3155 | 5.1418 | 0.4964 |

MAE averages each race equally. GRU ensemble averages all three seeds' predictions.
Full-model seed validation MAEs: 1.0215, 1.0136, 1.0636 seconds. Do not call seed
variability a confidence interval over future races.

Sequence boosting was selected on validation, not benchmark scores. The full GRU
improved on last-lap baseline but did not beat either boosting comparator on the
benchmark. Ablations show different validation/benchmark ordering: no universal
feature-importance or causal claim is justified.

Three training-only expanding validation folds yielded GRU/baseline MAE pairs
2.2884/2.9602, 3.3134/3.7239, and 2.4282/3.3154 seconds. Those folds also selected
checkpoints, so these are diagnostic validation results, not unbiased outer CV.

## Limitations and next gate

The 2025 benchmark was inspected in an earlier experiment; it is not a pristine
holdout. Historical event timestamps do not certify real-time data availability.
Long laps remain in evaluation, and only three benchmark races are available.
No claim of reliable live strategy, causal tyre degradation, or future-season
performance follows. Freeze a cross-season evaluation protocol before opening
the reserved 2026 set; do not repeatedly tune against it.

Artifacts are under `.local-data/ml-runs/sequence-gru-2026-10-27/`: weights,
encoders, epoch curves, exact predictions, experiment logs, hashes and REPORT.md.
See SEQUENCE-EXPERIMENT.md for commands and protocol.

## Defensible resume description

Built an F1 next-lap forecasting research pipeline using PyTorch GRUs and gradient
boosting, with 10-lap histories across 23 races, chronological evaluation,
three-seed ensembles, feature ablations, leakage checks, and a FastAPI research
dashboard. On a reused three-race benchmark, sequence boosting achieved 0.987 s
race-average MAE versus 2.048 s last-lap baseline; the GRU achieved 1.257 s.

Use this only once you can explain the code, split design, limitations and why
the simpler model won. Do not describe GRU deployment or an untouched test set.
