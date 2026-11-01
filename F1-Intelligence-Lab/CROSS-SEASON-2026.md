# Frozen 2026 evaluation — 28 October 2026

## Outcome

Correction from the subsequent year audit: the original training cohort included
13 races from 2025 plus 2023 Singapore and 2024 Suzuka. It was not 2025-only.
The frozen metrics below are unchanged. The separate [restart experiment](RESTART-MODELS.md)
excludes those older races and does not re-evaluate 2026.

The existing models were evaluated without fitting, tuning,
checkpoint changes or reselection. Sequence boosting remained the candidate
selected before opening 2026. **This result does not justify promotion for live
forecasting:** the rolling-median baseline beats all learned candidates on the
primary metric. No model has been automatically promoted or deployed publicly.

| Frozen model | Equal-race MAE (seconds) | Pooled RMSE (seconds) | Pooled R² |
|---|---:|---:|---:|
| Last lap | 8.2882 | 110.2463 | -1.1195 |
| Rolling mean | 8.3425 | 86.4759 | -0.3040 |
| Rolling median | **6.0457** | **74.3542** | **0.0359** |
| 13-feature boosting | 7.8654 | 109.5399 | -1.0924 |
| Sequence boosting | 7.6842 | 109.8353 | -1.1037 |
| Full GRU ensemble | 7.1835 | 99.4247 | -0.7238 |
| GRU without tyre inputs | 7.1527 | 98.8434 | -0.7037 |
| GRU without control inputs | 7.2065 | 99.2374 | -0.7173 |

## Coverage and interpretation

- 7,195 matched eligible target laps across 15 verified 2026 races, from the
  existing frozen audit snapshot—not a claim of the complete 2026 calendar.
- Original eligible three-lap rows: 8,343. Ten-lap checks exclude 1,133 incomplete
  histories, 11 ambiguous tyre histories, and 4 missing tyre histories.
- Three unverified races remain excluded: openf1-11234 (fastest-lap anchor
  mismatches), openf1-11396 (event/year not confirmed), openf1-11731 (no unambiguous
  FIA final classification). Full audit reasons are retained.
- All eight candidates use identical rows. Long laps remain; no post-evaluation
  label trimming or exclusion of difficult races was performed.

Sequence boosting beats last-lap in 13/15 races, with a mean paired difference
of -0.6041 seconds and an exploratory 95% paired race-bootstrap interval
[-0.8182, -0.3792] seconds. This comparison does **not** establish superiority
to the stronger rolling-median baseline. The interval resamples races 10,000
times, not individual laps, and assumes exchangeable races; temporal dependence
and the small race set limit interpretation.

Monaco is a major failure case: sequence boosting MAE is 74.674 seconds versus
37.965 for rolling median. Eleven target laps exceed 180 seconds across the
evaluated set; sequence boosting MAE for that diagnostic slice is 1,784 seconds.
Long-lap aftermath also creates large errors on otherwise normal target laps.
These are diagnostic findings, not grounds to remove rows from headline metrics.

Sequence boosting's prior reused 2025 benchmark MAE was 0.9872 seconds, versus
7.6842 here. The full GRU changed from 1.2566 to 7.1835. Circuit mix, event
conditions and eligibility differ: this comparison alone cannot identify the
cause of the generalization gap or attribute it specifically to regulations.
Historical corrected timestamps are not proof of live data availability.

## Reproduction and artifacts

Verification: run `make test` from the repository root for the current suite. A complete second evaluation reproduced all
aggregate and seed metrics, bootstrap intervals, and row-level predictions
exactly. The report endpoint and dashboard were checked locally.

```sh
python -m f1_intelligence_lab.cross_season --evaluate-2026 \
  --dataset /absolute/path/to/audited-dataset \
  --source-root /absolute/path/to/local-data \
  --frozen-run /absolute/path/to/sequence-gru-2026-10-27 \
  --output /absolute/path/to/new-evaluation-directory
```

The evaluator checks frozen model hashes and the original dataset manifest, then
writes protocol.json **before** accessing holdout labels or source caches.
Default training loaders still refuse the future partition. Optional skill
experiment logging is available through `--skill-tools`.

Local output: `.local-data/ml-runs/cross-season-2026-10-28/` contains protocol,
source/model hashes, scores by race and condition, seed metrics, paired intervals,
row-level predictions, experiment logs and REPORT.md. Original model artifacts
remain unchanged. Set `F1_CROSS_SEASON_RUN` to this directory to serve the saved
report through `/api/ml/cross-season` and race-detail section 09. No weights or
raw source caches are served by this endpoint.

## Holdout status and next research task

**2026 has now been evaluated. It is no longer untouched for later development.**
Do not tune on it and then present the same scores as independent validation.

Next: investigate long-lap/restart behaviour with 2025 development data, clarify
whether the target should be full elapsed lap time or an explicitly conditional
racing-pace target, and test a prespecified robust baseline/model design on
development-only chronological folds. A new final evaluation must use genuinely
unseen races collected later. This is a separate experiment, not a retroactive
change to this result.
