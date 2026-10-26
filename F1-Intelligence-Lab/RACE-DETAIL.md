# Race detail dossiers

Open `/race-detail/?session=openf1-9912` or use **Full race dossier** on a library card.

The race picker covers every saved race with timing. Each dossier combines:

- OpenF1 session results, including laps, gaps, points and DNF/DNS/DSQ flags. Classification is never inferred from lap timing.
- Stored race-analysis clean pace and an interactive driver lap-time trace. The flag and pit-lap exclusion methodology remains visible.
- Raw provider stint boundaries and compound timelines; incomplete boundaries stay in the table, not the diagram.
- Pit-lane duration and stationary stop duration in separate columns. Missing values stay missing.
- Searchable race-control messages, sorted by UTC timestamp.
- FIA event-document links, filtered by season and exact mapped Grand Prix filename prefix. Summons are explicitly distinguished from decisions. The document index is weekend-wide and not guaranteed exhaustive.

## Data and operation

`GET /api/race-details/{sid}` reads saved data; `POST /api/race-details/{sid}/load` starts a single-process background load. GET does not trigger external downloads. The POST reuses the existing OpenF1 cache and fetches the FIA index. It is not a force-refresh of historical OpenF1 cache entries. This remains a single-worker local research server, not a public multi-worker service.

The SQLite `race_details` table stores section-level availability and provenance separately from existing session/lap tables. A source failure does not replace genuine data with fabricated rows. Dossier retrieval time is the assembly time; reused OpenF1 responses may be older. Individual source URLs are exposed in the UI.

On 2026-10-27, dossiers were assembled for all 50 saved races: 24 from 2025, 18 from 2026, and eight older races. FIA links are available for 49; the provider's Kuala Lumpur 2026 session has no verified FIA event mapping and is explicitly unavailable. Existing provider sessions have not been independently reconciled against the official calendar. FIA PDF contents are linked, not parsed into automated legal/incident verdicts.

Sources: https://openf1.org/docs/ and https://www.fia.com/documents . Access to source data does not imply redistribution rights.
