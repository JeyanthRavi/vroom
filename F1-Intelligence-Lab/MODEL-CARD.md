# Model card: Vroom state-v2 next-lap regressors

**Owner:** Vroom research project. **Version:** state-v2-2025 (28 October 2026).
**Status:** public historical replay; model registry remains staging, not production
or live inference. [Open the replay](https://vroom-race-replay-jeyanth.quantum-banana.chatgpt.site).

- **Task:** predict elapsed next-lap duration in seconds from ten completed
  contiguous laps, prior tyre context and race-control information at cutoff.
- **Algorithms:** scikit-learn histogram gradient boosting (absolute-error loss,
  residual target, race weighting); PyTorch GRU, three-seed ensemble.
- **Selection:** whole-race chronological 2025 validation, equal-race MAE.
  Default replay model is restart boosting, ratio 1.5, 15 leaves.
- **Data:** checksum-verified cached OpenF1 records with the existing FIA
  classification audit. 13 training, five validation, three reused benchmark
  races from 2025; 15 verified 2026 races for regression only.
- **Coverage:** 6,083 training sequences; 7,195 evaluated 2026 sequences.
  Missing contiguous/tyre history excludes targets. This is not all race laps.
- **Outputs:** historical predictions and retrospective errors, not uncertainty
  bounds, probabilities, causal explanations or optimized race strategies.
- **Performance:** 0.8423 s equal-race validation MAE; 5.1714 s on previously
  examined 2026 regression versus 6.0457 s median baseline. 2026 RMSE 74.4971 s
  and R² 0.0322 show substantial residual interruption errors.
- **Limitations:** evaluated on previously examined 2026 races; not an independent holdout; sparse restart slices; delayed
  source-publication risk, conservative states when events are missing, regime
  changes and outlier target laps. No claim of superiority on every metric.
- **Comparison:** corrected-state versions slightly worsen overall 2026 MAE
  versus the preceding robust version, but improve the observed Monaco GRU
  resumption-window error. See ML-RELEASE.md for exact comparisons.
- **Appropriate use:** education, portfolio demonstration, reproducible offline
  research, error inspection. **Inappropriate use:** live team decisions,
  betting advice, guaranteed predictions or claims of official FIA analysis.
- **Integrity:** trusted local checkpoints only; checksum manifests detect
  corruption, not simultaneous malicious replacement of files and manifest.
  Public demo serves predictions, not executable model files.
- **Reproducibility:** training replay reproduced scores and predictions exactly
  in the local pinned environment. Source, splits and seeds are documented.
- **Lifecycle:** manual review on data refresh; no autonomous retraining or
  production promotion. Retain prior exports for rollback.

See [release, architecture and reproduction guide](ML-RELEASE.md).
