# Datasheet for Vroom research data

## Motivation

The data supports an educational study of next-lap forecasting, race-control
state reconstruction, simulated steward review, and deterministic telemetry
comparison. It was not collected for operational race strategy.

## Composition

- Git-ignored provider caches and an audited SQLite race library.
- Frozen, checksum-verified feature and evaluation artifacts.
- An aggregate public replay without driver-lap observations or lap durations.
- Small bundled StewardLens metadata/synthetic cases and a two-lap telemetry fixture.

Literal session, row, split, and class counts belong in generated results tables
or their source artifacts; they are not manually duplicated here.

## Collection and provenance

Historical provider responses were cached locally. FIA final-classification
documents were used for an independent audit where already available. The
Phase 5 extension did not scrape PDFs: it uses existing checksummed decision
metadata plus original synthetic cases. Source URLs and hashes are retained in
the corresponding manifests.

## Preprocessing

The pipeline quarantines unverified sessions and invalid laps, reconstructs
race state at the feature cutoff, forms contiguous history windows, and keeps
whole races in chronological splits. Targets include interruptions unless a
pre-registered conditional task says otherwise. No target-lap features may
enter the model input.

## Uses and out-of-scope uses

Appropriate uses are reproducible research, teaching, and retrospective error
analysis. The data is not suitable for live timing, betting, safety decisions,
driver ranking, causal inference, or official sporting decisions.

## Distribution and rights

Provider access and linked official documents do not establish a redistribution
grant. Raw caches, PDFs, checkpoints, and full lap exports remain local or
otherwise restricted. The checked-in public default contains aggregate metrics
only. See [`NOTICE.md`](NOTICE.md) and the
[`DATA-RIGHTS-REVIEW.md`](F1-Intelligence-Lab/DATA-RIGHTS-REVIEW.md).

## Maintenance

There is no automatic refresh or production promotion. New data requires audit,
new immutable run directories, refreshed manifests, generated tables, and human
review. The forward holdout may be opened only under the pre-registered rule.
