# Model card: Vroom historical next-lap regressors

## Model details

Vroom compares rolling baselines, histogram gradient boosting, a GRU ensemble,
and fixture-only research controls. The checked-in replay is a read-only
aggregate export. Registry entries remain `staging`; no code path promotes a
model to production automatically.

## Intended use

Educational, retrospective Formula 1 model evaluation, reproducibility work,
and error analysis. Outputs predict the next recorded lap duration from
completed contiguous history, prior tyre context, and reconstructed race state.

## Out-of-scope use

Live team decisions, betting, safety decisions, causal tyre or strategy claims,
official stewarding, or guaranteed forecasts.

## Data

The frozen historical artifacts use checksum-verified local OpenF1 caches and
the documented FIA classification audit. Splits keep whole races together and
use reconstructed event time; provider publication latency was not captured.
See [`DATASHEET.md`](../DATASHEET.md) for composition, processing, rights, and
maintenance details.

## Evaluation

Model selection used 2025 whole-race validation only. The 2026 cohort is a
regression check on previously examined data, not an independent holdout. Every
model metric is shown with the rolling-median baseline from the same rows.

<!-- BEGIN GENERATED: model-card-metrics -->
| Evaluation | Model | Equal-race MAE (s) | Baseline MAE (s) | Pooled RMSE (s) | R² | Rows |
|---|---|---:|---:|---:|---:|---:|
| 2025 validation | Selected restart boosting | 0.842 | 1.181 | 2.461 | 0.935 | 2285 |
| Examined 2026 regression | Restart boosting | 5.171 | 6.046 | 74.497 | 0.032 | 7195 |
| Examined 2026 regression | Restart GRU | 5.187 | 6.046 | 74.685 | 0.027 | 7195 |

Source: `demo-export-final/data.json`; 2026 is previously examined and non-independent.
<!-- END GENERATED: model-card-metrics -->

## Limitations

Interruption laps and distribution shift remain difficult; sparse race-level
samples limit interval precision. Fixture-only RQ1–RQ4 outputs validate code and
artifacts but are not Formula 1 performance evidence. Race-level bootstrap
intervals assume exchangeability that may not hold across circuits and rulesets.

## Ethical considerations and caveats

The project is unofficial. Public redistribution permission for lap-level data
is unresolved, so the deployment default is aggregate-only. Driver names and
marks belong to their owners. StewardLens is simulated and is not an official
decision system.

## Reproducibility and lifecycle

Pinned dependencies, fixed CPU seeds, immutable run directories, checksum
manifests, and CI gates are documented at the repository root. Data refreshes
require human review; there is no automatic retraining or promotion.
