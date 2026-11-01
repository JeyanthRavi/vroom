# Next-lap baseline and first models

[First completed experiment: results and limitations](FIRST-MODEL-RESULTS.md).

This is an offline, CPU-only experiment, not a prediction service. Read
[the data contract](ML-DATA-PREPARATION.md) first. Dataset labels include long
laps and disruptions; none are removed to improve metrics.

## Reproduce

From this directory, after setting up the project:

```sh
python -m pip install -e '.[ml,audit,dev]'
python -m f1_intelligence_lab.ml_train \
  --dataset /absolute/path/to/audited-dataset \
  --output .local-data/ml-runs/new-experiment
```

The output directory must be new. The dataset must pass the manifest-verified
loader. This checkout's original audited dataset is in the original project
folder, not in GitHub. Never substitute `candidates_NOT_FOR_TRAINING.csv`.

An optional `--skill-tools /path/to/data-scientist/scripts` runs
`feature_selector.py` on training features only and records every candidate
with `experiment_tracker.py`. These external skill utilities are not required
for model fitting. All runs also save their own complete `results.json`.
The tracker assumes larger metrics are better when comparing, so do not use its
automatic ranking for error metrics; use `selection.json` instead.

## Frozen experiment

- Primary metric: mean of per-race MAE, weighting each race equally. Secondary:
  pooled-lap MAE, RMSE, R² and 90th-percentile absolute error.
- Baselines: last completed lap, previous three-lap mean, previous three-lap median.
- First learned model: standardized, one-hot encoded ridge regression, alpha 10.
- Second fixed candidate: histogram gradient boosting with absolute-error loss,
  150 iterations, 15 leaves, learning rate 0.05, minimum leaf size 30, L2 1,
  random seed 42. Random early-stopping splits are disabled.
- Learned models predict the change from last-lap duration; the last lap is then
  added back. No prediction clipping or label trimming is applied.
- All 13 prespecified features retained. Training-only feature ranking is
  descriptive, not causal importance or a statistical significance test.
- Three expanding, whole-race folds inside training provide diagnostic CV;
  each fold fits its own preprocessing and model. No hyperparameter search.
- Train on the training partition only. Select on validation. Write the selection
  record before opening test. Score only the validation-selected baseline and
  learned model on test; do not refit or change the winner using test performance.
- The 2026 future holdout is not opened.

## Artifacts

The run directory contains frozen protocol, dataset/source hashes, package
versions, training/CV/validation/test metrics, per-race metrics, diagnostic slices,
test prediction CSVs, feature selection record, trained models and readable report.
`selected.joblib` may represent a baseline if neither learned model beats it on
validation. `ridge.joblib` and `hist_absolute.joblib` retain both learned models.

Load only trusted locally generated joblib artifacts (pickle can execute code):

```python
import joblib
from f1_intelligence_lab.ml_train import predict
bundle = joblib.load('path/to/selected.joblib')
predicted_seconds = predict(bundle['name'], bundle['model'], feature_rows)
```

`feature_rows` must contain exactly the 13 contract features, not metadata or
labels. Values must be finite and categorical values nonempty. The fitted
encoder ignores unseen categories. Runtime semantic validation beyond the
audited dataset contract is not a public API guarantee.

## Interpretation limits

Only three final test races are available. Laps are correlated, and strict timing
eligibility excludes many records. This is not a live-arrival-time backtest,
a causal pit strategy model, or evidence of generalization to 2026. Cutoff-state
slices cannot identify all future disruptions. The target-over-180-seconds slice
is a hindsight diagnostic only. Audit verification is bounded to classification
and fastest-lap anchors, not every underlying timing record.

Local generated data and binaries remain git-ignored.

## Local website integration

Race-detail pages include an ML predictions section served by
`GET /api/ml/races/{sid}`. Set these operator-controlled environment variables
before starting the server:

```sh
export F1_ML_DATASET=/absolute/path/to/audited-dataset
export F1_ML_RUN=/absolute/path/to/first-model-run
export F1_LAB_DATA=/absolute/path/to/existing-race-library
uvicorn f1_intelligence_lab.app:app --host 127.0.0.1 --port 8765
```

Install the `ml` extra first. Configure only trusted, locally generated artifacts;
checksums detect corruption but do not authenticate maliciously replaced files.
The service checks model, results, dataset hashes, feature contract and sklearn
version before serving. It loads lazily, serializes inference access and caches
validated splits in memory. Restart after changing model or dataset files.

This is historical batch inference on frozen audited features, not live feature
generation. It displays predictions for train/validation/test with explicit split
labels, a driver selector, a comparison chart and exact errors. Unverified races
are unavailable; the 2026 holdout is never opened. Missing configuration disables
ML gracefully. Integrity or runtime failures return a sanitized 503 and log the
operator diagnostic. To roll back, unset F1_ML_RUN and restart; race browsing
continues without ML. No paid infrastructure, uploads or automatic retraining.

No production SLA, drift monitoring or public deployment is claimed for this
local frozen-dataset viewer. The browser displays the artifact version to make
the served model identifiable.
