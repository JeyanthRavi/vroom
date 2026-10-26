# Historical session library

Implemented 26 October 2026. This extends data coverage and local storage, not validated ML capabilities or public multi-user deployment.

## Current full-season import status — 26 October 2026

| Season | Saved races | Usable lap records | Driver telemetry laps |
|---|---:|---:|---:|
| 2025 | 24 | 26,192 | 464 |
| 2026 | 18 | 20,693 | 0 |
| Older saved races | 8 | 8,484 | 149 |
| Entire library | 50 | 55,369 | 613 |

Every provider-listed 2025 race is saved. Every past-dated 2026 entry was attempted: Sakhir (11261) and Jeddah (11269) returned HTTP 404 and remain absent. Future-dated 2026 Mexico City, Interlagos, Las Vegas, Lusail and Yas Marina were excluded. These counts describe the provider catalogue and returned records, not independent verification of the official calendar.

2026 coverage is race timing only. The four earlier full imports returned no usable telemetry; the remaining 14 use explicit `include_telemetry=False`, so their telemetry availability has **not** been checked. This mode is race/sprint-only and refuses to replace saved telemetry. Metadata, Race Lab warnings and library cards distinguish not-requested telemetry from missing telemetry. Cards without telemetry expose Race Lab rather than empty telemetry tools. Reimport normally to request telemetry later.

Verification: local Race Lab data and ScoutGrid APIs checked for all 42 sessions from 2025–2026; saved record counts and telemetry-row counts matched metadata. All 60 automated tests pass, including timing-only import, no car-data requests, and prevention of telemetry overwrite. No ongoing downloader or automatic future-race synchronization is configured.

## Use it

1. Open `/library/` in the local site.
2. Select a season, unambiguous circuit (e.g. Monza, Silverstone, Bahrain), session and provider.
3. Import; the job runs outside the web request. The page reports progress, completion or failure.
4. Open the saved session in Race Lab, ScoutGrid, Replay, Telemetry or ClaimCheck.
5. Restart the server: saved sessions remain available. Race Lab prefers a saved historical race; its synthetic exercise remains an explicit option.

OpenF1 is the default, with documented historical coverage from 2023 onwards: https://openf1.org/docs/. A requested event must resolve uniquely and be completed. Session indexes refresh after six hours; successful historical responses are cached locally. Downloads are sequential, paced, and retry bounded transient/429 failures. Provider availability varies. Empty responses are not permanently cached.

FastF1 is an optional adapter for the years exposed by the importer. During this implementation its upstream live-timing endpoint returned HTTP 401 and the import failed; this restriction was not bypassed. The functioning real-session validation used OpenF1. Install the optional `historical` dependency group if FastF1 is needed; OpenF1 uses the standard library.

## Data coverage

- Race Lab: every available valid lap timing with known driver/stint and start time, not just two selected drivers. Missing/unusable records are counted.
- Other performance workstations: one fastest usable telemetry lap per available driver, with up to three candidate laps tried. Not all telemetry for every lap.
- ScoutGrid sorts the loaded subset; it is not a talent model or race classification.
- Replay remains lap-relative playback; it is not synchronized race positions.
- ClaimCheck still supports only lap time, signed lap difference and archived time-penalty checks. It is not general natural-language fact checking.
- StewardLens remains a demonstration over supplied evidence. More timing data does not add incident facts or authoritative rulings. FIA Archive still has its existing document scope.

## Earlier selected-race snapshot (superseded by full-season totals above)

| Historical race | Saved usable lap records | Drivers with telemetry |
|---|---:|---:|
| Monza 2024 | 1,008 | 20 / 20 |
| Silverstone 2024 | 959 | 19 / 20 |
| Bahrain / Sakhir 2025 | 1,128 | 20 / 20 |
| Singapore 2023 | 1,083 | 18 / 19 |
| Zandvoort 2023 | 1,340 | 20 / 20 |
| Monaco / Monte Carlo 2024 | 1,217 | 16 / 20 |
| Suzuka 2024 | 904 | 18 / 20 |
| Spa-Francorchamps 2024 | 841 | 20 / 20 |
| Interlagos 2024 | 1,132 | 18 / 20 |
| Melbourne 2025 | 921 | 17 / 20 |
| Silverstone 2025 | 822 | 18 / 20 |
| Monza 2025 | 974 | 19 / 20 |
| Suzuka 2025 | 1,059 | 20 / 20 |
| Monaco / Monte Carlo 2025 | 1,423 | 20 / 20 |
| Spa-Francorchamps 2025 | 879 | 20 / 20 |
| Singapore 2025 | 1,229 | 20 / 20 |
| Melbourne 2026 | 960 | 0 / 22 |
| Silverstone 2026 | 1,111 | 0 / 22 |
| Monza 2026 | 1,052 | 0 / 22 |
| Austin 2026 | 1,163 | 0 / 22 |
| Total: 20 races | 21,205 | 303 telemetry laps |

Second expansion: eight 2025 races and four 2026 races are now saved, alongside the eight older races. All four 2026 imports returned usable race timing but no usable car telemetry: use Race Lab for those sessions, not telemetry comparisons or replay. All 12 sessions from 2025–2026 were checked against the local race and ScoutGrid APIs, including expected empty ScoutGrid rows for 2026. Missing provider compound values now map explicitly to UNKNOWN; a regression assertion verifies this. Combined tests: 58 passed. These are selected races, not complete seasons.

Expanded 26 October 2026 with nine additional races. Race and ScoutGrid endpoints returned HTTP 200 for all 12 sessions. Driver denominators reflect provider entries, not an independently verified starting grid. Melbourne exposed null stint boundaries; the importer now ignores unbounded stints and counts unmatched lap records as omitted rather than guessing boundaries. A failing-then-passing regression test covers this case; the combined suite passes 57 tests. The focused-fix scope was limited to the importer and its regression test; this document records the resulting data expansion.

These are real locally downloaded provider records, not generated fixtures. Availability and exclusions are recorded per session. Names/timing/content remain subject to provider and underlying rights; this does not authorize redistribution or commercial publication.

## Statistical limitations

OpenF1 flags are conservatively reconstructed from race-control messages. A yellow sector excludes overlapping laps. A safety-car ending announcement does not identify the exact restart: subsequent laps remain UNKNOWN until an explicit green event. This can exclude later stints from eligible statistics; the all-laps chart and exact table still show them. The UI must not imply that the remainder of a race actually ran under a safety car. Deleted/pit-out laps are excluded where identifiable from supplied records.

FastF1 uses its provider accuracy/generated/deleted flags when available. Neither path controls fuel, traffic or track evolution. Stint trends remain unadjusted slopes, not validated tyre degradation or causal strategy effects.

OpenF1 telemetry distance is approximated by integrating sampled speed. The source URLs, provider identity, retrieval time and coverage notes are stored with each session. CSV hashes identify exported bytes, not independent evidence certification.

## Storage and job model

- SQLite WAL database at `.local-data/library.sqlite3`, ignored by Git. Override the root with `F1_LAB_DATA` before starting the server.
- Separate session metadata, lap summaries and telemetry payloads. Catalogue/list calls do not hydrate all telemetry. Per-lap requests load the selected payload from disk.
- A session replacement is transactional: a failed import cannot publish a half-written session or erase the previous valid version.
- One background import subprocess per local server, 15-minute timeout. Duplicate in-progress requests reuse the job; another session receives HTTP 409. Progress/jobs persist in SQLite. Interrupted entries older than 16 minutes are marked failed when submitting the next import, enabling retry.
- Provider cache and per-job logs live under `.local-data`. Inspect `job-<id>.log` for diagnostics. No automatic disk deletion. Monitor disk growth; full archive storage is not unlimited.
- Existing independent app routes remain compatible. Cross-session telemetry comparisons are now rejected. `/laps` supports `offset` and `limit` (maximum 500) and reads saved summaries without loading sample arrays.
- CSV uploads remain ephemeral; they are not automatically added to the shared library.

Use **one localhost-bound uvicorn worker** for this implementation. Do not expose this unauthenticated download API publicly. Multi-user deployment requires authentication, quotas, durable cross-process scheduling, disk policies, monitoring and a deployment-specific load test. The single-process queue lock is not a distributed scheduler.

## Verification and scale evidence

Automated coverage includes persistence, restart reads, atomic replacement/rollback, lazy summaries, duplicate jobs, busy-job refusal, failed-job retry, timeout handling, flag boundaries, CSV validation and cross-session guards. Existing portal and Telemetry tests are included.

Live local API checks on all three real datasets returned HTTP 200 for race analysis, ScoutGrid, Replay and comparisons; numerical lap-time ClaimCheck returned supported for source values. Observed single-request times on this machine were approximately 16–21 ms for race responses, 32–45 ms for ScoutGrid, and 93–106 ms for Replay. These are smoke measurements, not SLOs or concurrent-load results.

`scripts/benchmark_library.py` builds a **temporary synthetic** 100-session/2,000-telemetry-lap library (301 samples per lap). Observed results: ~2.1 s total write, 0.6 ms metadata catalogue, 0.3 ms one-session summaries and 0.6 ms one-lap load. Temporary data is removed by the script. This validates a bounded storage path; it does not demonstrate thousands of simultaneous users or completeness of an F1 archive.

## Next scale boundary

The importer is reusable across supported historical events; additional sessions are not hard-coded. Before expanding to hundreds of downloads, add a user-controlled batch manifest and storage budget. Before downloading every lap's telemetry, introduce per-lap on-demand jobs and retention limits. Before public launch, complete source-rights review, auth, job isolation, distributed coordination and a realistic load test.
