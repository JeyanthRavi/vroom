# Vroom interview notes

## Core next-lap model

**Question:** Can recent lap, tyre, and race-state history predict the next recorded lap duration?

**Why a simple baseline can win:** lap pace is locally persistent, while rare
interruptions create large errors that a small learned model may not anticipate.

**What the result means:** 2025 model selection looked encouraging, but the
previously examined 2026 regression shows that improvement does not transfer to
every metric. The correct lesson is about shift and baseline discipline.

**Next:** open the preregistered forward holdout once enough new verified races exist.

Hard questions:

1. **Why did the median beat your model on 2026?** Regime shift, sparse interruption examples, and high-impact long laps. I did not tune on 2026 because that would invalidate the check.
2. **What would a truly unseen test look like?** Races starting after the protocol commit, opened once, with at least the preregistered minimum count and no model changes after labels are read.
3. **Why keep R² if it is weak?** It is descriptive and exposes pooled-tail failure; equal-race MAE is the preregistered headline.

## RQ1 — pace and hazard

**Question:** Does separating green-flag pace from neutralisation risk improve interpretation and prediction?

**Why a simple baseline can win:** hazards are rare and circuit-dependent; a
base rate can be hard to beat without more independent races.

**Meaning now:** the deterministic fixture proves contracts, class weighting,
calibration, TCN execution, and breakdowns—not real hazard skill.

**Next:** run the frozen real-data adapter without changing thresholds.

Hard questions: How is future leakage prevented? Features are cutoff-bounded and
tested. Why PR-AUC? The event is imbalanced. Can this predict a crash? No; it is
a historical neutralisation-onset task, not causal crash prediction.

## RQ2 — conformal intervals

**Question:** Can the system attach useful empirical uncertainty bounds?

**Why a simple baseline can win:** residual distributions can shift sharply and
wide intervals may achieve coverage without being useful.

**Meaning now:** disjoint calibration and test plumbing works; Formula 1
coverage is not yet established.

**Next:** evaluate rolling-origin real-data coverage and interval width together.

Hard questions: Why Wilson intervals? Coverage is binomial and sample counts can
be small. Why Mondrian abstention? Tiny groups give unstable quantiles. Are the
intervals causal? No.

## RQ3 — drift

**Question:** Where does distribution and error shift appear?

**Why a simple baseline can win:** a median is robust to feature-schema and
strategy changes that can invalidate learned relationships.

**Meaning now:** the fixture detects an injected shift; it does not explain the
real 2026 gap.

**Next:** apply the fixed PSI/KS/adversarial and rolling-error diagnostics to
rights-reviewed audited splits.

Hard questions: Does adversarial AUC prove drift cause? No. Why grouped CV?
Rows from one race are dependent. Why no adaptation claim? Real-data selection
has not run under the frozen folds.

## RQ4 — sequence fairness

**Question:** Do GRU/TCN sequence biases help beyond boosting and an MLP?

**Why a simple baseline can win:** the dataset is small at the race level and
the local median already captures most short-horizon persistence.

**Meaning now:** all ablations and seeds run reproducibly on fixtures; no
architecture superiority is supported.

**Next:** run matched CPU budgets with validation early stopping on audited data.

Hard questions: Why a TCN? It is a compact non-recurrent sequence control. Why
three seeds? To expose neural variance. Why not a transformer? The evidence size
does not justify the complexity.

## StewardLens

**Question:** Can retrieval and penalty classification be measured without an LLM?

**Why a simple baseline can win:** the corpus is tiny and explicit lexical rule
IDs are strong signals. A transformer would overfit and add unverifiable cost.

**Meaning:** the feasibility run exposes rare-class failure and citation gaps;
it is not an official-decision predictor.

**Next:** expand only with rights-cleared, independently annotated cases.

Hard questions: Why no fine-tuning? Sample size is too small. What does the bias
audit show? Name-swap sensitivity on bundled cases only. Is citation validity
the same as correctness? No; existence and overlap do not prove the claim.

## Rights and deployment

**Is the public demo allowed to show this data?** The aggregate default avoids
lap-level redistribution, but final permission remains unresolved. I would not
publish the full replay until the owner records clearance.

**Why not call it production?** There is no approved licence, remote CI result,
operational SLA, monitoring, or independent forward evaluation. “Historical
research replay” is accurate.
