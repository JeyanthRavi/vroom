# First model — 27 October 2026

Selected: histogram gradient boosting predicting the change from last-lap time.
Training: 7,884 rows / 15 races. Validation: 2,632 / 5. Test: 1,655 / 3.
The separate 2026 holdout was not opened. No website inference integration yet.

| Candidate | Validation race-average MAE (s) | Test race-average MAE (s) | Test pooled RMSE (s) | Test pooled R² |
|---|---:|---:|---:|---:|
| Last lap | 2.0237 | 2.7052 | 8.1256 | 0.4078 |
| Rolling three-lap mean | 2.4213 | Not evaluated | — | — |
| Rolling three-lap median | 2.0954 | Not evaluated | — | — |
| Ridge | 5.1602 | Not evaluated | — | — |
| Histogram gradient boosting | 1.6082 | 2.0039 | 6.0970 | 0.6666 |

The selected model reduced test race-average MAE by approximately **25.9%**
against the validation-selected baseline. It improved mean error on all three
test races, but not every metric or scenario. Expanding training-race CV MAEs
were 2.460, 4.368, 3.455 seconds versus baseline 3.245, 3.928, 3.645; the model
lost one fold. This is a promising first experiment, not universal superiority.

Test MAE was 0.918 seconds for known-green-at-cutoff rows, 2.598 seconds for
other cutoff states, and 6.975 seconds following a pit-out lap. No test target
exceeded 180 seconds, so this test does not establish performance on very long
disruptions. Only three test races are available and laps are correlated.

The protocol was fixed before execution; selection was saved before opening
test. Preprocessing and models were fitted on train only. No test-driven tuning
or refitting was performed. Three chronological training-only CV folds were
diagnostic. All 13 prespecified features were retained; a training-only skill
feature-ranking report and five experiment-tracker entries were saved.

Environment: Python 3.9.6, scikit-learn 1.6.1, NumPy 2.0.2, joblib 1.5.3.
The rejected ridge candidate emitted matrix-multiplication numeric warnings on
this machine despite finite predictions. Independent einsum contraction checks
matched prediction values within 2.2e-14; the warning is recorded, not suppressed.
The selected tree model did not emit these warnings. An independent ridge
coefficient calculation matched within 9.8e-13. All 126 tests passed; replay
metrics and test CSVs were identical, artifact hashes verified, and reloaded
selected-model predictions matched exactly. Replay was a reproducibility check,
not a second tuning experiment.

Run artifacts (git-ignored): `.local-data/ml-runs/first-model-2026-10-27/`.
They include models, prediction CSVs, provenance, checksums, CV/per-race/slice
metrics, protocol and selection records. Replay is in the adjacent `-replay`
directory. See [training instructions](ML-TRAINING.md) and
[data limitations](ML-DATA-PREPARATION.md).
