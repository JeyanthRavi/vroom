# Vroom: Reproducible Evaluation of Historical Formula 1 Lap Forecasts Under Shift

## Abstract

Vroom is an unofficial research platform for retrospective Formula 1 analysis.
Its central task predicts a driver's next recorded lap duration from completed
contiguous history, prior tyre context, and reconstructed race-control state.
This report focuses on the engineering and evaluation problem rather than a
claim of predictive superiority. The repository combines whole-race temporal
splits, strong rolling baselines, gradient boosting and compact sequence models,
checksum-verified artifacts, and a rights-safe aggregate replay. Existing model
selection used 2025 races; the 2026 cohort has already been examined and is
reported only as a non-independent regression check. A pre-registered extension
separates green-flag pace from neutralisation risk, adds conformal uncertainty,
diagnoses shift, and compares GRU, TCN, MLP, and sequence-boosting controls. At
release time those extensions have fixture-only outputs, so they validate the
research software but provide no new Formula 1 performance evidence. The main
finding is methodological: simple baselines, data rights, split integrity, and
negative results are first-class parts of an honest portfolio ML system.

## 1. Introduction

Lap-time prediction appears to be a straightforward regression problem, but a
recorded race lap mixes several regimes. Green-flag pace is locally persistent;
pit entry and exit alter the target; safety-car, virtual-safety-car, and red-flag
periods change both the duration and its meaning. A model can achieve attractive
validation error by learning a narrow set of circuits or regimes and then fail
under a new season, ruleset, or interruption pattern.

Vroom began as three connected prototypes: an Intelligence Lab with a historical
race library and ML pipeline, StewardLens with deterministic evidence-linked
incident review, and Telemetry Pit Crew with lap-trace comparison. The final
release asks a narrower question: can these components be made reproducible and
honest enough that every portfolio claim points to code and an artifact?

The work makes four contributions. First, it establishes a rights-aware release
boundary: local raw caches and full exports remain restricted, while the public
default contains aggregate metrics. Second, it freezes a research protocol
before new experiment code. Third, it implements deterministic, offline RQ1–RQ4
pipelines with leakage checks and race-level statistics. Fourth, it exposes the
limitations of learned models beside rolling baselines rather than selecting a
single favourable metric.

No claim is made that Vroom supports live strategy, causal inference, official
stewarding, betting, or production deployment.

## 2. Related work

The evaluation design follows the general principle that time-dependent ML
systems should use forward or rolling-origin validation rather than random row
splits [CITATION NEEDED]. It also adopts model-card and dataset-documentation
ideas associated with transparent reporting [CITATION NEEDED]. Prediction
interval evaluation uses split conformal and conformalized quantile-regression
concepts [CITATION NEEDED]. The neural controls use standard gated recurrent and
temporal-convolutional architectures [CITATION NEEDED].

Formula 1 analytics literature covers lap-time modelling, tyre degradation,
pit strategy, and telemetry comparison, but this draft does not cite a specific
study without a verified bibliography. A future version should add a systematic
literature review and replace each placeholder with a source the author has read.

## 3. Data and rights

Historical provider responses are stored in git-ignored local caches. An audit
compares candidate race sessions with already available FIA final-classification
evidence and quarantines incomplete or inconsistent sessions. The feature
pipeline retains provenance, input hashes, and a contract that forbids target-lap
sectors, target compound, final results, and other future information.

The public-data boundary is deliberately conservative. Access to an endpoint or
link to an official document does not establish a redistribution grant. The
checked-in final replay therefore contains race/model summaries, histograms,
and calibration summaries without driver-lap tables or observed durations. FIA
PDFs, raw provider caches, and model checkpoints are not added by this work.

StewardLens uses two already checksum-verified decision metadata records and
clearly labelled synthetic cases. Descriptions are fresh paraphrases; no new PDF
was scraped. Telemetry Pit Crew retains a compact two-lap Monza fixture. That
fixture is too small for a meaningful representation-learning evaluation, so
the optional autoencoder experiment is deferred.

## 4. Task and split design

The frozen core task predicts the next recorded lap duration in seconds from a
window of completed contiguous laps, previous tyre information, and race state
known at the cutoff. Whole races stay together. The 2025 development period is
partitioned chronologically for training, validation, and a reused benchmark.
The 2026 cohort is explicitly labelled previously examined and may not be used
for tuning or described as independent.

The preregistered forward holdout consists of verified races starting strictly
after the protocol commit boundary. It may be opened once by a dedicated script
that writes `protocol.json` before reading labels. If fewer than the required
number of races exist, the correct outcome is “forward holdout pending.” That is
the state of this release.

Every comparison includes last lap, rolling mean, rolling medians, and a
per-circuit-prior median where applicable. Equal-race MAE is the headline metric
because pooled rows would give longer races more weight. Pooled RMSE and R² are
reported descriptively. Paired race differences use a race-level bootstrap; the
race is the resampling unit, and cross-race exchangeability is acknowledged as
an imperfect assumption.

## 5. Methods

### 5.1 Pace and interruption risk

RQ1 separates conditional green-flag pace from the onset of SC, VSC, or red-flag
neutralisation. The pace model excludes non-green targets and pit-in/out laps.
The hazard task predicts onset within short horizons using cutoff-available race
state, lap position, recent variance, local yellow counts, cars in the pit
window, and tyre-age context. It compares a base rate, weighted logistic
regression, histogram gradient boosting, and a compact TCN. Evaluation includes
PR-AUC, ROC-AUC, Brier score, log loss, calibration error, reliability bins, and
race/circuit breakdowns. The two-stage combined forecast is compared against a
single-stage regressor and rolling median on identical rows.

### 5.2 Conformal uncertainty

RQ2 reserves whole calibration races disjoint from model training and testing.
It implements split conformal residual bounds and conformalized quantile
regression at predeclared nominal levels. Coverage is reported with Wilson
intervals, mean width, and interval score. Group-conditional output abstains
when the calibration group is below a fixed support threshold. This prevents a
small subgroup from producing a confident-looking but unstable bound.

### 5.3 Drift diagnostics

RQ3 measures feature shift using population stability index and Kolmogorov–
Smirnov statistics, and trains a race-grouped adversarial classifier to
distinguish periods. A rolling-origin error timeline shows where baseline error
changes. Proposed adaptations—recency weighting, circuit normalisation, and a
rolling-median residual target—must be selected on 2025 folds only before any
labelled 2026 regression check.

### 5.4 Sequence fairness

RQ4 compares sequence boosting, GRU, TCN, and a parameter-matched MLP across
history windows and state/tyre ablations. Neural candidates use fixed seeds and
CPU-only execution. The rolling median appears in every cell. Model size and
seed variance are retained; timing is excluded from deterministic fixture
artifacts because it is machine-dependent.

### 5.5 StewardLens feasibility

StewardLens evaluates TF-IDF regulation retrieval with recall@k, MRR, and
per-clause misses. Penalty-category feasibility uses TF-IDF plus structured
tokens and stratified logistic regression. The dataset is too small for
transformer fine-tuning. Citation integrity requires cited IDs to exist and
overlap retrieved evidence. Identity swaps report a flip rate and Wilson
interval, with the explicit limitation that name swaps do not establish broad
fairness.

## 6. Experiments and results

The canonical numeric tables are generated in `research/RESULTS.md` from
committed `results.json` artifacts. The existing frozen core results show a
material gap between favourable 2025 validation and the previously examined
2026 cohort. On that cohort, the rolling median remains an essential comparator;
restart-aware learned variants improve equal-race MAE in the recorded table but
do not improve every pooled metric. Rare long interruption laps remain a severe
error slice.

RQ1–RQ4 results in this release are deterministic synthetic fixtures. They prove
that manifests, plots, metrics, leakage guards, calibration separation, model
execution, and byte-identical result checks work. They do not permit conclusions
about real pace, hazards, coverage, drift, or neural superiority. In particular,
a fixture score that favours one model is not promoted as a result.

The StewardLens feasibility run is intentionally small and mixed. Its generated
per-class report contains a class with no correctly retrieved predictions. This
negative result is valuable: it blocks any claim that the classifier reproduces
official penalty decisions and explains why transformer fine-tuning was skipped.

## 7. Software quality and reproducibility

Each experiment creates a new directory containing a protocol, environment,
results, per-race/per-case output, predictions where applicable, report, and
SHA-256 manifest. Fixed seeds and CPU execution reduce nondeterminism. Tests run
with and without PyTorch. CI covers supported Python versions, a CPU-Torch path,
demo verification, and Docker builds.

A one-command script runs the fixture pipelines when local data paths are absent
and announces that the outputs are not evidence. With complete rights-reviewed
paths it executes audit, training, evaluation, aggregate export, and final-site
generation into timestamped directories. Generated-table markers prevent docs
from silently diverging from artifacts.

## 8. Limitations

The real research extension has not been executed on audited splits. The forward
holdout is pending. Provider event timestamps are not verified feed-arrival
timestamps. Race counts are small, circuits are heterogeneous, and bootstrap
exchangeability is imperfect. Rights clearance remains unresolved. Remote CI
and Docker builds await their first external run. The manual accessibility pass
requires a browser and assistive technology.

The project also has product limitations. It is not a live system, has no SLA,
does not monitor feature streams, does not automatically retrain, and refuses
automatic model promotion. Its static demo is a historical replay.

## 9. Ethics

Motorsport analytics can encourage unjustified claims about driver ability,
intent, or blame. Vroom restricts its language to observed historical patterns
and avoids causal or official conclusions. StewardLens citations can be valid
without making the associated claim correct, and identity swaps cover only a
narrow sensitivity check. Public data minimisation is treated as an engineering
control rather than a substitute for permission.

## 10. Conclusion

Vroom's final release is strongest as an example of disciplined ML engineering:
it retains negative findings, exposes baselines, freezes protocols, separates
fixtures from evidence, and makes documentation mechanically traceable to
artifacts. The next scientific step is not a larger model. It is execution of
the frozen protocol on a rights-reviewed audited dataset, followed by the single
pre-registered forward-holdout opening when enough new races exist.
