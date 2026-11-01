# Restart regression test on 2026 — 28 October 2026

## Verdict: substantial recovery improvement, not a complete restart fix

Frozen 2025-only models were scored on 7,195 eligible targets from 15 verified
2026 races. No fitting, tuning, checkpoint changes, reselection or deployment.
The same cached cohort was used for every model. Of 8,343 audited target rows,
1,148 lacked usable ten-lap histories; three unverified races remain excluded.
This is a regression test on previously examined 2026 data, not an untouched
generalization study.

| Model | Equal-race MAE, seconds | Pooled RMSE, seconds | Pooled R² |
|---|---:|---:|---:|
| Last-lap baseline | 8.2882 | 110.2463 | -1.1195 |
| Rolling median | 6.0457 | **74.3542** | **0.0359** |
| Original boosting (mixed-year training) | 7.6842 | 109.8353 | -1.1037 |
| Original GRU (mixed-year training) | 7.1835 | 99.4247 | -0.7238 |
| Unmodified boosting, retrained on 2025 only | 7.5025 | 109.7079 | -1.0988 |
| Restart-aware boosting, 2025 only | **5.0590** | 74.6158 | 0.0291 |
| Restart-aware GRU, 2025 only | 5.0688 | 74.6457 | 0.0284 |

The new boosting model reduces equal-race MAE by 32.6% against the same-cohort
2025-only unmodified comparator, and 16.3% against rolling median. Both new models
beat rolling median's MAE on all 15 races, but median still has slightly better
pooled RMSE and R². These metrics answer different questions; no universal winner
or automatic model promotion is implied.

Exploratory paired race-bootstrap MAE differences against median:
boosting −0.987 s (95% interval −1.280 to −0.699), GRU −0.977 s
(−1.229 to −0.736). Resampling assumes exchangeable races and does not undo
prior exposure to the 2026 failures.

## What improved

- Immediately after a historical lap exceeding the frozen 2× reference threshold:
  11 examples, all Monaco. Pooled MAE falls from 2,059.18 s for same-cohort
  unmodified boosting to 25.65 s for restart boosting and 26.68 s for the new
  GRU. Median remains better on this narrow slice, at 22.58 s.
- Across the first three laps after a flagged long history lap: 29 examples in
  two races. Pooled MAE is 814.59 s unmodified boosting, 41.11 s restart boosting,
  38.53 s restart GRU and 43.97 s median.
- A supplemental source-message-based red-flag resumption window contains
  16 eligible targets, all Monaco. MAE falls from 833.67 s for same-cohort
  unmodified boosting to 27.64 s restart boosting and 27.94 s restart GRU,
  versus 34.52 s median. This is a post-hoc diagnostic, not a new selection set.
- Full Monaco race MAE falls from 74.64 s for same-cohort unmodified boosting
  to 36.87 s restart boosting; GRU is 36.76 s, median 37.97 s.

## What is NOT fixed

1. **Long target laps themselves:** on 11 targets over 180 seconds across three
   races, pooled MAE remains roughly 1,784 s for both new models. Better recovery
   after an interruption does not mean predicting a future stoppage.
2. **Explicit restart feature coverage:** both stored state-transition slices
   contain zero examples. The parser expects a RED flag field, while the cached
   Monaco suspension is `RED FLAG - RACE SUSPENDED` with a null flag. Local
   yellow/clear events can also overwrite session-wide safety-car state.
   Thus the evidence supports the robust historical reference, not an effective
   learned restart-state signal.
3. **Ordinary pace trade-off:** excluding long targets and recent long histories,
   equal-race MAE is 2.623 s for same-cohort unmodified boosting versus 2.706 s
   restart boosting and 2.724 s restart GRU. Robustness has a modest cost here.
4. **Limited restart evidence:** the source-annotated resumption window covers
   one race, with residual errors around 28 seconds. Not all restart types,
   safety-car endings, weather changes or missing-history cases are validated.

The supplemental annotation pairs an actual `SESSION STARTED` message with a
preceding red suspension, then includes eligible targets starting at/after that
message on the event's lap through event lap +2. Announcements such as “will
resume” and infringement notices do not count. This annotates evaluation rows
only: neither frozen features nor predictions were modified. Raw event evidence
and checksums are saved with the result. The official meaning of each event has
not been independently adjudicated.

## Verification and artifacts

All trained artifact checksums were verified before evaluation and again after.
The initial run and the supplemental diagnostic run have identical aggregate
model scores. Predictions are aligned by row ID and actual target against the
prior frozen evaluation before comparison. Baselines, three error metrics,
per-race/slice metrics, feature limitations and experiment logs are retained.
No feature selection was rerun on 2026; training-only ranking remains in the
2025 experiment.

Final local artifacts: `.local-data/ml-runs/restart-2026-v2-2026-10-28/`
(`REPORT.md`, `results.json`, `predictions.csv`, `protocol.json`, experiment log
and checksum manifest). The earlier run is retained separately.

```bash
PYTHONPATH=src python -m f1_intelligence_lab.restart_evaluate \
  --dataset /absolute/path/to/ml-prep/audit-2026-10-27-final \
  --source-root /absolute/path/to/source-data \
  --robust-run /absolute/path/to/robust-2025-v2-2026-10-28 \
  --original-evaluation /absolute/path/to/cross-season-2026-10-28 \
  --output /absolute/path/to/new-evaluation --evaluate-2026
```

## Next corrective step

Separate session-wide RED/SC/VSC state from local sector flags; recognize
explicit suspension/resumption messages without interpreting pit-exit green
lights as an unrestricted racing restart. Add fixture tests, reconstruct 2025
features, and retrain/tune on 2025 only. Preserve this frozen regression result;
use genuinely unseen races for future independent validation. This evaluation
does not change the website's active prediction model.
