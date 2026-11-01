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

