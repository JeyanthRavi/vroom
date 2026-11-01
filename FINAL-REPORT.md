# Vroom final-release report

Date: 2026-11-02  
Branch: `final-release`

## Outcome

Vroom is now a reproducible, rights-aware research repository rather than a
collection of local prototypes. It has an aggregate-only public default,
authenticated import/write paths, a committed preregistration, deterministic
RQ1–RQ4 research harnesses, a measured StewardLens feasibility path, generated
results tables, CI, clean setup, and a checksum-verified static site.

The new research runs are fixture-only and explicitly **not evidence**. The
existing 2026 evaluation remains a regression check on previously examined
races, not an independent holdout. The forward holdout is pending.

## Literal final gates

| Gate | Outcome |
|---|---|
| Ruff | All checks passed |
| mypy | No issues in 59 source files |
| Tests without PyTorch | 187 passed, 7 explicit skips |
| Tests with PyTorch 2.8.0 | 209 passed |
| Demo checks | 8 passed |
| Generated results check | Current |
| Internal Markdown links | Current |
| Coverage | 79% total; 3,935 statements, 833 missed |
| Clean clone | `make setup` completed; 209 tests passed |

The release machine is documented in [`HARDWARE.md`](HARDWARE.md). Docker and
actionlint were unavailable locally; both image builds are configured as
required CI work and await the first remote run.

## Evidence summary

The generated tables in [`README.md`](README.md),
[`MODEL-CARD.md`](F1-Intelligence-Lab/MODEL-CARD.md), and
[`research/RESULTS.md`](research/RESULTS.md) are the canonical summaries. They
are rebuilt by `scripts/make_results_tables.py`; CI/tests fail if they drift.

The strongest defensible existing finding is negative and useful: on the
previously examined 2026 cohort, the rolling-median baseline remains a critical
reference and learned models do not improve every metric. RQ1–RQ4 currently
demonstrate research engineering only. StewardLens exposes its rare-class
failure rather than promoting an aggregate score.

## Safety, rights, and security

- Aggregate export is the default and contains no lap durations or driver-lap tables.
- The final static package is checksum-protected and 132 KB on disk.
- Import/write endpoints require `F1_ADMIN_TOKEN`, except explicit loopback-only local mode.
- No outreach was sent and no source-code licence was selected.
- Secret review found configuration names and test placeholders only; no secret value or `.env` is committed.
- `NOTICE.md`, the rights review, status log, and rollback procedure remain authoritative.

## Reproduce

```bash
make setup
source F1-Intelligence-Lab/.venv/bin/activate
make lint type test test-torch demo docs
python scripts/make_results_tables.py --check
scripts/reproduce.sh
```

With no local paths, the reproduction script announces and runs fixture-only
pipelines. For a rights-reviewed local replay, supply `F1_DATA_ROOT`,
`F1_FROZEN_RUN`, and `F1_ORIGINAL_2026_EVAL`; all outputs go to a fresh
timestamped directory.

## Known limitations and open decisions

- Public redistribution permission for lap-level provider data is unresolved.
- The owner must choose a source-code licence and whether to publish the final aggregate demo.
- Forward-holdout evaluation needs enough verified post-boundary races.
- Automated browser accessibility and remote Docker CI results remain pending.
- Real-data RQ1–RQ4 adapters still need a rights-reviewed audited split source.
- Telemetry representation learning was deferred because the bundled corpus has only two laps.

See [`OPEN-QUESTIONS.md`](OPEN-QUESTIONS.md), [`MOBILE-QA.md`](MOBILE-QA.md),
and [`PROGRESS-LOG.md`](PROGRESS-LOG.md) for the exact handoff.
