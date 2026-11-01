# Ten-lap GRU research experiment

## Question and fixed protocol

Does a compact recurrent model improve next-lap forecasting over boosted trees
on the same verified race/lap examples? Primary metric remains equal-weight
race-average MAE in seconds; secondary metrics include pooled MAE, RMSE, R²,
90th-percentile error and per-race/state/pit-out diagnostics.

This is an extension experiment, not a claim that deep learning must be better.
The 2025 test races have already been inspected in the first experiment, so this
document calls them a **reused benchmark**, not a pristine holdout. 2026 remains
unopened. No new independent-generalization claim may be based on this benchmark.

## Dataset and leakage controls

Use the original verified split loader and source-cache SHA-256 hashes. Require
10 contiguous valid completed laps before each target's recorded start. Histories
stay within one driver and one race. No padding or interpolation. Missing or
ambiguous tyre histories are excluded. All comparison models share these targets
and training rows, so results are not directly comparable with the earlier
three-lap experiment's headline score.

Each sequence step contains pace relative to the last completed lap, lap number,
tyre compound/age/stint lap, pit-out status, and race-control state at that lap's
start. The existing 13-feature context supplies the latest cutoff state and
short-term pace. Target time, target compound, target flags, future stint ends,
driver IDs and final classifications are not model inputs. Classification is used
only in the inherited source audit/eligibility checks. Historical corrections and
publication latency remain unknown; this is event-time reconstruction, not a
certified live-feed backtest.

## Candidates

- Last-lap, three-lap mean and median baselines.
- Retrained 13-feature histogram boosting baseline on the same cohort.
- Histogram boosting with the same flattened 10-lap history plus context.
- GRU with 24 hidden units, a 16-unit context branch, a 32-unit prediction head,
  and a residual output added to the last completed lap time.
- GRU ablations remove tyre features or race-control features from **both** the
  sequence and context; all other settings and examples remain fixed.

All learned models optimize absolute error with equal total training weight per
race. GRU training uses AdamW (learning rate .001, weight decay .0001), batch size
256, gradient clipping at 1, at most 30 epochs and patience 5. Checkpoints are
chosen by validation race-average MAE. Three seeds (11, 29, 47) are all retained;
the GRU family prediction is their arithmetic mean, not the best seed. Seed-level
results and epoch curves are recorded. This is CPU-only, with deterministic
PyTorch algorithms and one compute thread.

Encoding and scaling fit only training data. All predeclared features remain in
the full model; the training-only skill feature ranking is descriptive. Three
expanding training-race validation folds provide an additional diagnostic for
the full GRU versus last-lap baseline. Those folds also select checkpoints, so
they are **not unbiased outer cross-validation estimates**.

The full GRU ensemble competes with baselines and fixed tree candidates on
validation. Ablations are diagnostic, not selection candidates. Architecture,
seeds, preprocessing and checkpoints are fixed before this run reads benchmark
labels. There is no tuning after benchmark evaluation and no automatic promotion
over the existing website model.

## Run

```sh
python -m pip install -e '.[dl]'
python -m f1_intelligence_lab.dl_train \
  --dataset /absolute/path/to/audited-dataset \
  --source-root /absolute/path/to/original-local-data \
  --output .local-data/ml-runs/new-sequence-run
```

An optional `--skill-tools` points to the data-scientist skill's scripts for
feature ranking and experiment logging. Outputs include frozen protocol,
coverage/exclusion counts, source/data/code hashes, train/validation/benchmark
metrics, checkpoint epochs, seed metrics, weights, encoders, benchmark prediction
CSV, selection record and report. Files are local and git-ignored; no paid
service or GPU account is required. Only load trusted local artifacts.

## Resume claims

After a completed run, describe the dataset, matched baselines, actual GRU
architecture, multi-seed evaluation and ablations. Report measured results and
limitations, including losses to simpler models. Do not claim deployment of the
GRU, a new untouched holdout, causal strategy optimization, or improved accuracy
unless the evidence actually supports it.

Implementation references: [PyTorch GRU](https://docs.pytorch.org/docs/main/generated/torch.nn.GRU.html)
and [official PyTorch version installation](https://pytorch.org/get-started/previous-versions/).
