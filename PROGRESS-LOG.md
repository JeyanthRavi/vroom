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

