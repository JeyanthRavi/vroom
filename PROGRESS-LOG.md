# Vroom final-release progress log

## Phase 0 — Baseline and environment   (2026-11-02)

Done:

- Created and checked out the `final-release` branch.
- Updated `F1-Intelligence-Lab/scripts/setup.sh` so the three sibling projects install their documented development, audit, FastF1, and deep-learning extras.
- Built isolated Python 3.9 virtual environments with and without PyTorch.
- Recorded a complete pinned Python environment in `requirements-lock.txt`.
- Confirmed `F1-Intelligence-Lab/.local-data/` is present (59 MB, 10 files at depth two) and remains excluded from version control.
- Created `OPEN-QUESTIONS.md`; the source-code licence and public-demo privacy choice remain owner decisions.

Verified:

- With PyTorch: `PYTHONPATH=src:../F1-StewardLens/src:../F1-Telemetry-Pit-Crew/src pytest -q tests ../F1-StewardLens/tests ../F1-Telemetry-Pit-Crew/tests --import-mode=importlib -rs` → `164 passed in 8.64s`.
- Without PyTorch: the same command → `146 passed, 4 skipped in 5.73s`; the four skips explicitly report that `torch` is not installed.
- Versions: Python 3.9.6; PyTorch 2.8.0; scikit-learn 1.6.1; NumPy 2.0.2.

Not done / blocked:

- None for the Phase 0 gate.

Claims changed in docs:

- None.

## Phase 1 — Safety, rights and honesty   (2026-11-02)

Done:

- Added aggregate/full export modes in `F1-Intelligence-Lab/src/f1_intelligence_lab/export_demo.py`; aggregate is the CLI default and removes driver/lap rows and observed durations.
- Added manifest schema 2 with `export_mode`, legacy-manifest compatibility, checksummed asset validation, a sanitized metadata route, and visible aggregate/full/legacy badges.
- Generated the new default `F1-Intelligence-Lab/demo-export-aggregate/` (36 race summaries, 108 KB). The frozen legacy full package remains unchanged for local audit; it is not the Docker/default deployment input.
- Added CSP, `X-Content-Type-Options`, and `Referrer-Policy` headers to every replay response.
- Added `F1_ADMIN_TOKEN` authentication to provider import and race-detail network/write endpoints. With no token they return 403, except when `F1_ALLOW_LOCAL_IMPORT=1` and both client and configured bind host are loopback.
- Added and tested the documented 500 KB CSV ceiling.
- Added `NOTICE.md`, rights banners to all four READMEs, a blank permission status log, a precise owner-run privacy rollback procedure, and owner decisions to `OPEN-QUESTIONS.md`. No message or hosting change was made.
- Marked all six blueprint chapters **PROPOSED — NOT IMPLEMENTED**.
- Replaced résumé copy in `F1-Intelligence-Lab/ML-RELEASE.md` with a pointer to the Phase 10 generated claims document.
- Reviewed the requested overclaim terms across Markdown, HTML, JavaScript, and Python. Remaining matches are either explicit limitations, source descriptions (for example, linked official FIA documents), measured/frozen findings, internal variable names such as `best`, or clearly proposed plans.

Verified:

- Focused safety suite: `46 passed in 4.84s`.
- Full repository suite with PyTorch: `171 passed in 6.50s`.
- Full repository suite without PyTorch: `152 passed, 5 skipped in 4.10s`; all skips explicitly require PyTorch.
- Aggregate-package smoke test: checksum-verified health and metadata endpoints returned successfully; schema 2 contained 36 race summaries and no `sessions` key.
- `pip-audit` was unavailable in the clean environment. Fallback `pip list --outdated` reported `mpmath 1.3.0 → 1.4.1`, `pypdf 5.9.0 → 6.21.4`, and `setuptools 58.0.4 → 82.0.1`; no dependency was changed without compatibility testing.
- Tracked-file secret-pattern review found environment-variable names, test-only placeholder tokens, and documentation references only; no credential file, private key, `.env`, or committed secret value was found.
- `git diff --check`: clean.

Not done / blocked:

- Public redistribution permission remains unresolved. The owner must decide whether to make the current hosted full replay private and must record any later permission response.
- Source-code licence choice remains an owner decision.

Claims changed in docs:

| Location | Previous wording | Release wording / treatment |
|---|---|---|
| `F1-Intelligence-Lab/README.md` | “2026 is no longer an untouched holdout” | “evaluated on previously examined 2026 races; not an independent holdout” |
| `F1-Intelligence-Lab/MODEL-CARD.md` | “previously seen test season” | Uses the standard previously-examined/non-independent wording |
| Replay UI and export limitations | “previously seen regression set” / “2026 regression” | Uses the standard previously-examined/non-independent wording |
| Replay landing copy | “Real cached race data” with lap-level explorer assumed | States aggregate summaries are the default and labels full/legacy packages |
| Blueprint chapters | Feature prose could be read as current capability | Every chapter now opens with **PROPOSED — NOT IMPLEMENTED** |
| `ML-RELEASE.md` résumé section | Hand-maintained résumé metrics | Removed; points to artifact-generated `RESUME-CLAIMS.md` |

## Phase 2 — Repository quality   (2026-11-02)

Done:

- Added root `pyproject.toml` and `Makefile` targets for setup, lint, permissive legacy typing, fast/full tests, PyTorch tests, demo verification, and documentation links.
- Added pinned Ruff, mypy, pytest-cov and coverage dependencies to `requirements-lock.txt`. Ruff enforces release-blocking syntax/name errors; mypy is permissive for legacy modules and strict for the new security module. Research modules receive stricter overrides when added.
- Added `.github/workflows/ci.yml` with Python 3.9/3.12 no-Torch tests, CPU-Torch tests, lint/type, demo verification, pip caching, and builds for both Dockerfiles.
- Expanded `race_state.py` coverage for red-flag restart, pit-exit green, safety-car-ending announcements, local sectors, cutoff isolation, and unordered events.
- Rewrote the top-level README as the single entry point with a 60-second quickstart, Mermaid architecture, project/data map, artifact-linked results summary, limitations, and rights notice. Subproject READMEs now link to the root setup.
- Added `CONFIGURATION.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, a local Markdown link checker, and repository hygiene exclusions for checkpoints and tool caches.
- Removed stale hard-coded test counts from project documentation; literal historical/current outcomes remain only in this progress record and the final report.

Verified:

- `make lint`: Ruff reported `All checks passed!`.
- `make type`: mypy reported `Success: no issues found in 46 source files` under the documented permissive-legacy policy.
- `make docs`: `Internal Markdown links: ok`.
- `make test` without PyTorch: `156 passed, 5 skipped in 5.06s`.
- `make test-torch`: Torch 2.8.0; `175 passed in 9.81s`.
- Coverage run: `175 passed`; 3,132 statements, 777 missed, **75% total**. Target modules: `race_state.py` 96%, `export_demo.py` 47%, `restart_evaluate.py` 38%, `repository.py` 88%.
- CI workflow parsed successfully as YAML. `git diff --check`: clean.

Not done / blocked:

- `actionlint` and Docker are not installed on this machine. Workflow syntax was YAML-parsed locally; image builds are configured as a required CI job but await the first GitHub Actions run.

Claims changed in docs:

- Replaced obsolete hard-coded suite counts with the current `make test` verification command.
- Replaced the stale “2026 holdout remains reserved” root README narrative with the measured, limitation-first summary and standard previously-examined wording.

## Phase 3 — Research design   (2026-11-02)

Done:

- Created `research/PROTOCOL.md` before any RQ1–RQ4 experiment code.
- Fixed questions, hypotheses, 2025 rolling-origin development, whole-race splits, baselines, metrics, paired 10,000-resample race bootstrap, decision rules, claims language, and artifact/determinism requirements.
- Fixed the forward-holdout boundary as race start strictly after 2026-11-02. Previously examined 2026 data is regression-only and cannot substitute.

Verified:

- Protocol checked against the non-negotiable rules: no 2026 tuning, no live/causal/official claim, whole-race splits, calibration disjointness, baseline comparison, fixed seeds, and fixture-only labeling are explicit.
- `git diff --check`: clean.

Not done / blocked:

- Forward holdout is pending until at least three verified races start after the protocol boundary.

Claims changed in docs:

- None; this phase pre-registers conditions under which future claims would be allowed.

## Phase 4 — Reproducible research harness   (2026-11-02)

Done:

- Implemented the preregistered RQ1 pace/hazard pipeline with rolling-median, logistic, boosted-tree, single-stage, and compact TCN comparators. Hazard outputs include PR-AUC, ROC-AUC, Brier score, log loss, ECE, reliability bins, and per-race/per-circuit breakdowns.
- Implemented RQ2 split conformal and conformalized quantile regression fixtures with calibration/test separation, coverage, width, interval score, rolling-origin results, and additive interval fields in the historical prediction API.
- Implemented RQ3 drift diagnostics using PSI, KS, grouped adversarial validation, rolling race MAE, and preregistered trigger reporting.
- Implemented RQ4 GRU, TCN, MLP, and sequence-aware boosting comparisons across 5/10/15-lap windows, state-history ablations, tyre-history ablations, and seeds 11/29/47.
- Added shared leakage guards, deterministic synthetic data, paired 10,000-resample race bootstrap intervals, Wilson intervals, reliability/ECE utilities, immutable artifact manifests, environment records, plots, and text alternatives.
- Added a forward-holdout opener that writes its protocol before reading labels and remains pending until three post-boundary races are available.
- Generated four checksum-verifiable fixture runs under `research/runs/`. Every report and result labels itself **fixture-only: not evidence**; these outputs validate plumbing and reproducibility, not Formula 1 model quality.
- Added explicit `research` dependencies and preserved functional no-Torch installation through test-level skips for the two PyTorch-specific suites.
- Fixed the demo Make target so repository paths containing spaces are handled safely.

Verified:

- `make lint`: Ruff reported `All checks passed!`.
- `make type`: mypy reported `Success: no issues found in 55 source files`.
- Full repository suite with PyTorch 2.8.0: `191 passed in 48.70s`.
- Full repository suite without PyTorch: `169 passed, 7 skipped in 12.12s`; all seven skips explicitly report the missing optional PyTorch dependency.
- Research-only no-Torch suite: `12 passed, 2 skipped in 19.68s`.
- Aggregate demo gate: `6 passed`; health and aggregate metadata smoke checks passed.
- Internal Markdown links: `ok`.

Not done / blocked:

- Audited real-data RQ1–RQ4 results are not produced because a rights-reviewed, split-ready real-data adapter is not yet available. The repository includes the exact adapter contract and run procedure.
- The independent forward holdout remains pending until at least three verified races start strictly after 2026-11-02.

Claims changed in docs:

- Research result summaries explicitly separate fixture engineering validation from empirical evidence.
- Prediction intervals are optional additive fields and are not described as calibrated on real Formula 1 outcomes until the real-data protocol is executed.

## Phase 5 — StewardLens measured NLP extension   (2026-11-02)

Done:

- Added `F1-StewardLens/data/eval/cases.jsonl`, built only from the two already checksum-verified decision metadata records and clearly labelled synthetic cases. Descriptions are original paraphrases; no PDF was scraped or copied.
- Added a deterministic TF-IDF retriever and an optional injected sentence-embedding retriever with an explicit TF-IDF fallback that never downloads a model during default runs or tests.
- Added stratified cross-validation for a TF-IDF/logistic-regression penalty classifier, with class counts, per-class precision/recall/F1, and a sample-count confusion matrix.
- Added retrieval recall@k, MRR, per-clause misses, agent citation-integrity scoring, and actual identity-swap flip reporting with a Wilson interval and a narrow limitation statement.
- Added `ModelAgent`, a deterministic mock, and an environment-gated provider adapter. Provider output remains subject to strict packet citation validation; successful prompts/outputs log only to git-ignored `runs/`.
- Generated checksum-verifiable `research/runs/stewardlens-feasibility/`. Its `results.json` prominently labels the work a small mixed metadata/synthetic feasibility demonstration.
- Rewrote the StewardLens README section to distinguish rule-based, learned, measured, and simulated components.

Verified:

- New evaluation/retrieval/model-agent tests: `12 passed in 1.96s`.
- Full StewardLens suite without PyTorch: `49 passed in 2.49s`.
- Ruff: `All checks passed!`.
- mypy: `Success: no issues found in 57 source files`.
- The generated outcome artifact reports 10 cases across three penalty labels and exposes the failed reprimand recall rather than treating the result as a performance claim.

Not done / blocked:

- Transformer fine-tuning was intentionally not attempted: the saved evaluation set is too small to justify it.
- The sentence-embedding path requires an explicitly supplied local encoder or the optional `[nlp]` dependency; the default remains TF-IDF and offline.

Claims changed in docs:

- StewardLens is described as a deterministic simulator with measured feasibility components, not an AI steward or official-decision predictor.
- The identity-swap audit is explicitly limited to name sensitivity on the bundled synthetic cases and is not presented as a general fairness finding.

## Phase 6 — Optional telemetry representation experiment   (2026-11-02)

Done:

- Audited the available bundled corpus and documented the decision in `research/TELEMETRY-NOTE.md`.

Verified:

- The bundled Monza fixture contains two laps, which is adequate for the existing comparison demonstration but not for a held-out embedding or nearest-neighbour evaluation.

Not done / blocked:

- The optional PCA/autoencoder experiment was not run. It is deferred until a rights-reviewed local corpus contains enough independent laps, drivers, and sessions.

Claims changed in docs:

- Added an explicit no-result statement; no telemetry representation claim is made.

## Phase 7 — Website and demo finalisation   (2026-11-02)

Done:

- Added generated fixture-only neutralisation-hazard reliability, conformal interval coverage, and drift-timeline views to the static model demo. Every view places its baseline or nominal target beside the model output and carries a visible scope/limitation box.
- Added a static methodology page generated at export time from `research/PROTOCOL.md` and `research/RESULTS.md`; no runtime network or Markdown renderer is required.
- Added checksum-protected `research.json` and `methodology.html` assets, plus export mode, version, and Git commit metadata in the footer.
- Added keyboard focus treatment, semantic status/chart labels, adjacent chart text alternatives, responsive layout down to 360 px, reduced-motion handling, and `MOBILE-QA.md`.
- Added `site_export.py`, immutable build tests, accessibility source checks, and the final aggregate package at `F1-Intelligence-Lab/demo-export-final/`.
- Updated the default demo Make target and demo Docker image to use the final aggregate package.

Verified:

- Final aggregate site size: 132 KB on disk, below the 1 MB transfer budget before compression.
- `data.json` contains no `actual`, `driver`, `prediction_at`, `lap_number`, or `duration` keys.
- JavaScript syntax: `node --check` passed.
- Demo gate: `8 passed in 9.28s`; health, aggregate metadata, and research-asset smoke checks passed.
- Ruff, mypy (58 source files), and internal Markdown links passed.

Not done / blocked:

- Automated axe/Playwright tooling is not installed. The manual browser and assistive-technology release checklist is in `MOBILE-QA.md` and remains an owner pre-publication task.
- The research views contain fixture outputs only; real 2025 research evaluation and the forward holdout remain pending.

Claims changed in docs:

- The demo calls the new views pipeline demonstrations, not model-performance evidence.
- The footer exposes the loaded aggregate mode and build identity and repeats the unofficial/data-rights limitation.

## Phase 8 — Reproducibility and tracking   (2026-11-02)

Done:

- Added `scripts/reproduce.sh`. With complete local paths it runs audit → state-v2 training → examined-2026 regression → aggregate export → final site into fresh directories. Without them it announces and runs the fixture-only RQ1–RQ4 and StewardLens pipelines, then prints SHA-256 checksums.
- Added `scripts/make_results_tables.py` and marker-protected generated sections in the root README, model card, and consolidated research results. A test fails when committed sections are stale.
- Reworked `MODEL-CARD.md` into intended use, out-of-scope use, data, generated metrics/baselines, limitations, ethics, and lifecycle sections.
- Added `DATASHEET.md`, `HARDWARE.md`, and a staging-only registry API/policy. The API rejects `production` status rather than promoting automatically.
- Kept dependency pins in `requirements-lock.txt`; generated runs retain environment and Git-commit records.

Verified:

- Fixture fallback reproduction completed in a fresh `/tmp/vroom-reproduce-phase8` directory and printed hashes for every output file.
- Result generation followed immediately by `--check`: `Generated result sections: current`.
- Generated-doc and registry tests: `2 passed in 0.09s`.
- Ruff, mypy (59 source files), and internal Markdown links passed.

Not done / blocked:

- The real-data branch of `reproduce.sh` was not executed in this phase because the required frozen-run environment paths were not supplied to the script. Its fixture fallback is the verified default.

Claims changed in docs:

- Experiment numbers in the three maintained summary documents now come from committed JSON artifacts through a checkable generator.
- The model card no longer duplicates hand-maintained metrics and explicitly pairs learned-model results with the rolling-median baseline.

