# Implementation status — 26 October 2026

**Subsequent implementation:** [historical library](../HISTORICAL-LIBRARY.md) now adds reusable provider imports, persistent SQLite storage, shared telemetry sessions and three verified real races. The slice inventory below describes the earlier baseline; historical ingestion/session persistence are no longer wholly unimplemented. Public multi-user scale and validated ML remain future work.

## Revised product boundary

User confirmed two focused products: **Analysis Lab** and **News & Stories**. Both may explain races, but the Lab owns data exploration and eventual ML research; News owns editorial coverage. Earlier single-ecosystem navigation assumptions are superseded by this split. Shared identity and links are possible later; neither product should depend on the other to function.

## Delivered in this slice

- Race Lab is the default local homepage, also `/race-lab/`.
- Existing six tools remain available at `/workstations/` and their original routes.
- Pure Python CSV validation and deterministic race/stint statistics behind small HTTP adapters.
- Interactive driver/eligible-lap filters, SVG pace trace, observed stint blocks and marked pit-in laps.
- Beginner/analyst explanation modes, exact records, source-type labels, import errors and JSON export.
- Fictional 30-lap exercise plus ephemeral user CSV imports. No historical full-race dataset was acquired.
- No added runtime dependency, paid service, external request, login, public deployment or trained model.

## Not delivered yet

Historical full-race ingestion, persistent session management, matched-condition comparisons, validated strategy simulation, ML training/evaluation, synchronized race replay, the separate news site, Android and widgets. Existing lap replay remains lap-relative; CSV race imports do not populate that catalogue.

## Verification

38 automated tests passed for the combined portal, including new CSV validation, synthetic provenance, eligible-lap exclusions, sparse trends, import isolation and routes. JavaScript syntax checked with Node. Browser checks confirmed loading, analyst mode, driver filtering and the no-selected-drivers empty state in the in-app browser. This is not a complete accessibility or multi-device certification.

## Next bounded milestone

Add an explicit full-race historical import adapter with provenance, coverage and source terms documented. Validate it on one permitted race before introducing race-relative gaps or strategy models. Maintain offline fixtures so tests do not require live provider access.
