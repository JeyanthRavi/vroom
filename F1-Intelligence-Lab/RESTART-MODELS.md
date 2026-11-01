# Restart-aware next-lap models — 28 October 2026

Follow-up: [frozen 2026 regression results](RESTART-2026-RESULTS.md) are now
available. The no-2026 statements below describe the training/tuning experiment,
not the subsequent evaluation. Long-lap recovery improved; explicit restart
state parsing still needs correction. No model has been promoted.

## Outcome

Implemented and trained restart-aware gradient boosting and a three-seed PyTorch
GRU ensemble. The changes remove extreme historical laps from the prediction
reference while retaining event information. They substantially reduce synthetic
interruption sensitivity, but do not beat unchanged boosting on ordinary 2025
validation. No model has been automatically promoted; existing website inference
is unchanged. The new research section exposes the comparison, not a live forecast.

| Model | Validation equal-race MAE (s) | Reused 2025 benchmark MAE (s) | Synthetic stress equal-race MAE (s) |
|---|---:|---:|---:|
| Rolling median | 1.181 | 2.057 | **2.126** |
| Unmodified sequence boosting | **0.840** | **1.018** | 830.646 |
| Restart-aware boosting | 0.870 | 1.020 | 2.414 |
| Restart-aware GRU ensemble | 0.978 | 1.200 | 9.287 |

Stress means multiplying the last observed lap duration by ten and leaving the
target unchanged. It is a sensitivity diagnostic, NOT measured real restart
accuracy. Median still wins this stress comparison. The selected ratio identifies
zero immediately preceding long laps in the 2025 benchmark: real-event recovery
has therefore not been validated by that benchmark. Future stoppages cannot be
predicted from information unavailable at the prediction cutoff.

## Data and selection

- Train: 6,083 contiguous ten-lap histories from 13 verified 2025 races.
- Validation: 2,285 examples from five separate 2025 races.
- Reused benchmark: 1,452 examples from three 2025 races. Previously examined;
  not a pristine holdout. Opened only after this run's selection was saved.
- Excluded 793 older-year training histories. The original experiment had
  included two older races; the unmodified comparator was retrained on exactly
  the same 2025-only cohort as the new candidates for this comparison.
- No 2026 data loaded or scored during this experiment. Previously observed
  2026 failures motivated the design, so a future rerun would be a regression
  check, not an independent generalization claim.
- Equal-race MAE is the selection metric; pooled MAE, RMSE, R² and per-race/state
  diagnostics are also saved. All original elapsed-time targets are retained.
- Six predeclared boosting configurations: history thresholds 1.5/2/3 times
  reference, maximum leaves 7/15. Validation chose ratio 2 and 15 leaves.
- The selected representation then feeds GRUs with seeds 11, 29 and 47.
  Validation chooses checkpoints; the three predictions are averaged.
- Three expanding-window training-race checks favored the robust tree over
  median. These are descriptive checks, not independent nested CV estimates.
- Feature ranking used training data only, with all predeclared features retained.
  Each candidate was logged in the experiment tracker.

## What changed

The reference is the median of the shortest five of ten completed laps. The
prediction anchor is the most recent history lap below the selected threshold,
not an interrupted last lap. Extreme pace inputs are replaced with the reference;
sequence deltas are bounded. Added signals retain long-lap count, previous-long
flag, recency, bounded duration ratio, and transitions from known RED/SC/VSC states
to GREEN. Both tree and GRU predict residuals relative to this robust anchor.

Only historical laps and race-control information known at cutoff are used.
Labels are neither clipped nor consulted by preprocessing. Several consecutive
interruptions are supported, but a history dominated by slow/interrupted laps
can still corrupt the reference. A statistical long-lap flag is not an official
red-flag annotation. Missing control information is not treated as GREEN.

## Reproduce locally

Verification: 151 tests pass across all three projects. A complete repeat run
reproduced every score, seed metric, forward-validation result, stress result,
and benchmark prediction CSV exactly. The saved tree and GRU inference helper
also reproduced all 1,452 benchmark predictions exactly after checksum checks.
The new API and rendered website comparison were verified locally.

Run from F1-Intelligence-Lab using the environment with pinned project dependencies
and PyTorch. Choose a new output directory; existing experiments are never replaced.

```bash
PYTHONPATH=src python -m f1_intelligence_lab.robust_train \
  --dataset /absolute/path/to/ml-prep/audit-2026-10-27-final \
  --source-root /absolute/path/to/source-data \
  --frozen-run /absolute/path/to/sequence-gru-2026-10-27 \
  --output /absolute/path/to/new-run
```

The successful local run is `.local-data/ml-runs/robust-2025-v2-2026-10-28`.
It contains the protocol, selection, all six tree models, three GRU checkpoints
and encoders, metrics, predictions, training-only feature ranking, experiment log,
and checksum manifest. The original models remain intact. Checksums detect
corruption, not malicious replacement of artifacts and their manifest together;
only load trusted local joblib files.

Set `F1_ROBUST_RUN` to the successful run directory to expose the read-only
`/api/ml/restart-research` report and the race-detail `#restart-research` section.
`robust_train.predict_saved` provides explicit checkpoint-verified experimental
tree/GRU inference; it does not change the production selection.
