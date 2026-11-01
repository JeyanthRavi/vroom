# Three decisions I can defend in an interview

These are concise speaking notes, not claims to memorize word-for-word. Lead
with the decision, explain the failure it prevents, and finish with the evidence
or next experiment.

## 1. Leakage prevention

**Short answer:** I split by whole races in chronological order and constructed
every feature from information available at the prediction cutoff. I did not
randomly split laps, because adjacent laps from the same driver and race are
strongly correlated and would make validation look better than deployment.

**Why it matters:** A random row split can put lap 31 in training and lap 30 in
validation. The model then benefits from the same circuit, weather, driver,
stint and race state on both sides of the split. That tests interpolation inside
an already-seen event, not generalization to another race.

**What I implemented:**

- whole-race chronological train, validation, test and future-season cohorts;
- features computed at event time rather than from final race outcomes;
- explicit labels for in-sample, model-selection and previously examined data;
- artifact hashes connecting an evaluation to the exact training run;
- no claim that the examined 2026 cohort is a pristine independent holdout.

**Evidence to point to:** `ML-DATA-PREPARATION.md`, `DATASHEET.md`, and the
cohort labels in the aggregate demo.

## 2. Why the baseline matters

**Short answer:** A sophisticated model is only valuable if it beats a cheap,
credible decision rule. Lap time is highly autocorrelated, so a rolling median
is a strong baseline. Comparing against a weak mean predictor would exaggerate
the value of boosting or a GRU.

**What the result taught me:** The restart-aware learned models improved the
equal-race MAE in the examined 2026 cohort, but the rolling median retained the
better pooled RMSE and R². Long interruption laps dominate squared error. I
therefore report multiple metrics and do not claim an overall model victory.

**Why this is a strength:** The project demonstrates model evaluation and
engineering judgement, not just training code. A negative or mixed result is
useful when it identifies where model complexity is not yet justified.

**Evidence to point to:** `MODEL-CARD.md`, `SEQUENCE-RESULTS.md`,
`RESTART-2026-RESULTS.md`, and the frozen comparison in the public demo.

## 3. What I would improve next

**Short answer:** I would collect a genuinely untouched future-season holdout,
improve the race-state representation, and predict a distribution or event
regime before optimizing another point regressor.

**Priority order:**

1. Freeze the pipeline before acquiring a new season, then evaluate once.
2. Separate normal green-flag pace from safety-car, red-flag and restart regimes.
3. Add uncertainty intervals and calibration, not only point-error metrics.
4. Increase the number of independent races and quantify results per circuit,
   weather condition and interruption type.
5. Compare the GRU against equally tuned tabular and sequence baselines under
   the same cohort and compute budget.

**Why not simply make the network larger:** The limiting factor is independent
race coverage and regime definition, not parameter count. A larger network on
the same small, correlated sample would increase overfitting risk without
answering the generalization question.

## 20-second project explanation

“Vroom is a FastAPI Formula 1 research platform that joins race analysis,
telemetry and stewarding tools with a leakage-controlled next-lap prediction
study. I compared rolling baselines, tree models and a compact GRU using
chronological whole-race splits. The learned models produced mixed results, so
I published the limitations and an aggregate-only reproducible demo instead of
overstating accuracy.”
