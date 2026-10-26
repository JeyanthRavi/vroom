# 03 — Engineering, data, editorial operations and AI

The key architectural decision is to separate **producing knowledge** from **serving readers**. A student laptop can produce a small reviewed dataset; a static site can serve that dataset while the laptop is off. This does not provide real-time updates, arbitrary server-side computation or cloud account synchronization.

## 1. Current baseline

The existing FastAPI portal imports StewardLens and Telemetry Pit Crew, provides shared catalogue/replay/scout/check endpoints, and renders six local tools. Its scope is one recorded session, one synthetic session and two official decision records. Replay is lap-relative, ScoutGrid compares only cached laps, and ClaimCheck supports three numeric claim types. Treat this as reusable research code, not a production data platform.

Preserve existing tests and APIs. Add adapters and new packages incrementally. Do not replace Python analytics solely to unify the frontend framework. Public deployments must not assume `127.0.0.1:8765` is the user's server.

## 2. Stage A — no recurring paid services

```text
Allowed sources / manual editorial notes
                 ↓
Local ingestion → local SQLite + permitted raw cache
                 ↓
Python analysis → schema validation → editorial review
                 ↓
Publication export: HTML + versioned JSON + original assets
                 ↓
Static website on eligible free hosting
                 ↓
Web UI / Android snapshot reader / cached widgets
```

- Next.js + TypeScript in static-export mode; React charts only where interactive behavior earns their cost.
- Existing Python/FastAPI remains local for analysis and editor tools; SQLite stores metadata/draft state; Parquet or bounded files store telemetry.
- Published content can start in structured Markdown/JSON with schema checks; do not build a complex CMS before drafting a dozen real items.
- `SnapshotRepository` abstraction serves browser and Android readers. Public numeric checks run only against approved published records; complex jobs are precomputed or unavailable.
- Bookmarks, follows and spoiler preferences live in IndexedDB/browser storage and Room/DataStore respectively. Export/import bridges devices until sync is justified.
- Static host candidate: Cloudflare Pages free tier, subject to account eligibility, terms and limits. No paid plan, paid add-on or card-backed overage is authorized by this plan.
- Use a provider subdomain initially; a custom domain is optional expenditure later.
- Publish manually in batches while validating the product. The laptop is not a production server and is not exposed through a public tunnel.

Next.js documents static export and its distinction from server-required features. Static output cannot support arbitrary runtime API handlers, server actions or database access; do not accidentally design a free static deploy around them. [Static export documentation](https://nextjs.org/docs/app/guides/static-exports).

At the source-check date, Pages Free documents 500 builds/month, one concurrent build, 20,000 files/site and a 25 MiB per-file limit. Batch publishing, cap artifacts below limits and do not ship huge telemetry archives or APKs as ordinary page assets without checking size/distribution options. Functions consume separate quotas. [Pages limits](https://developers.cloudflare.com/pages/platform/limits/).

## 3. Stage B — only after evidence and budget

Introduce a hosted FastAPI modular monolith, PostgreSQL, a durable job worker and object storage when accounts, editorial concurrency or approved dynamic workloads require them. Redis is optional, not a first-day dependency. A small single deployment is easier to operate than microservices.

Keep domain entities/use cases independent of HTTP/ORM implementations. Suggested contexts: Catalogue, Sources, Publishing, Analysis, UserPreferences and Delivery. Domain modules expose ports; concrete source fetchers, SQLite/PostgreSQL repositories and model APIs are adapters. Controllers validate/translate, use cases enforce rules, repositories handle persistence.

Extraction to separate services is a later response to measured operational pressure, not a symbol of ambition. Keep read-mostly content on the static/CDN path even after dynamic APIs exist.

## 4. Proposed repository structure

```text
F1-Intelligence-Lab/
  apps/web/                  static-first TypeScript frontend
  apps/android/              native Android client
  src/f1_intelligence_lab/
    domain/                  framework-light entities and rules
    application/             publish/export/analyse use cases
    adapters/                existing services, sources, storage
    api/                     optional hosted API boundary
  content/                   original approved editorial source
  contracts/                 JSON schemas + shared test fixtures
  scripts/                   local ingest/validate/export tools
  tests/                     unit/integration/contract/data checks
  docs/                      methods, runbooks and decisions
  private-data/              ignored, permitted local raw material
```

This is a target layout; don't move existing source wholesale without migration tests. Confirm repository boundaries/AGENTS.md instructions at implementation time. Never commit tokens, signing keys, raw private research interviews or restricted content.

## 5. Domain model and invariants

| Entity | Important fields | Invariants |
|---|---|---|
| Season/Event/Session | stable ID, provider mapping, UTC times, format/status | Schedule revisions retained; TBC is not zero-time |
| Driver/Team/Membership | stable ID, aliases, effective interval | A driver's team is resolved for the event date |
| SourcePolicy | publisher, URL pattern, permitted uses, expiry, review state | Unknown permission means no public redistribution |
| SourceRevision | URL, retrieved/published time, checksum, parser version | Immutable revision; retention follows rights policy |
| Claim | exact proposition, type, status, evidence links | Unsupported is not contradicted |
| EvidenceLink | source revision, section/page, support relation | Must point to actual retained/accessible evidence |
| Moment | event/session/time, kind, summary, spoiler fields | Clock basis required; no unlabelled demo data |
| NewsItem | claim cluster, original text, status, revision | Every public revision has approval and sources |
| RegulationVersion | season, issue, effective interval, article/page | Event-date applicability checked before use |
| Incident/Decision | drivers, location, official state, appeal state | Official and model outcomes stored separately |
| Upgrade | team/component, deployment, declared intent, fitment | Unknown effects/fitment preserved |
| Lap/Stint | driver/session, duration, compound/age, quality | Missing is null/unknown, never synthetic zero |
| AnalysisRun | input hashes, version, seed, parameters, outputs | Reproducible, bounded and tied to input revisions |
| Story/ClipReference | original text, provider URL, timestamp, rights | No implicit download rights; availability tracked |
| Publication | included revisions, manifest hash, generated time | One complete release is atomic |

Use milliseconds or explicit decimal precision for timing values; include units. Distinguish position, lap-relative progress and session-relative position. Store UTC instants and original source time-zone context; display local time. A copyright checksum demonstrates file identity, not factual truth or a licence.

## 6. Public snapshot contract

Illustrative, not deployed:

```json
{
  "schema_version": "1.0",
  "publication_id": "pub-0001",
  "generated_at": "<UTC ISO-8601>",
  "data_as_of": "<UTC ISO-8601 or null>",
  "mode": "historical",
  "coverage": {"events": ["event-id"], "complete": false},
  "resources": [{"path": "events/event-id.json", "sha256": "<hash>"}],
  "withdrawn_ids": [],
  "minimum_reader_schema": "1.0"
}
```

Each content resource includes ID, revision, title/summary, body blocks, entity links, evidence IDs, classification, source/event/publication timestamps, spoiler policy and correction metadata. Do not use a global “confidence: 98%” field for uncalibrated judgments.

Publish immutable resource files first and switch the manifest last as part of an atomic deployment. Readers stage and validate a complete compatible snapshot before replacing the prior cache. On partial download, checksum failure or incompatible schema, retain last-known-good and show freshness. Hashes detect corruption; trust/authenticity still requires HTTPS and controlled publishing credentials.

Provide retention/withdrawal semantics. On reconnect, clients process tombstones and delete withdrawn cached content. Previously downloaded offline copies cannot be reliably recalled immediately; disclose this limitation in rights decisions.

## 7. Later API contracts

| Endpoint family | Behavior |
|---|---|
| GET `/api/v1/feed` | Cursor pagination, explicit filters, published-only content |
| GET `/api/v1/events/{id}` | Event aggregate with coverage/freshness |
| GET `/api/v1/moments/{id}` | Revisioned explanation and references |
| GET `/api/v1/sources/{id}` | Permitted metadata, not unrestricted raw document access |
| POST `/api/v1/analysis-runs` | Validated bounded input, idempotency key, returns job ID |
| GET `/api/v1/analysis-runs/{id}` | Queued/running/succeeded/failed/cancelled status |
| GET `/api/v1/search` | Typed results; no source permission leakage |
| PUT/DELETE `/api/v1/me/bookmarks/{id}` | Authenticated per-user scope when accounts ship |
| GET `/api/v1/widget-snapshot` | Small cached payload, last observation/publication timestamps |

Errors use stable codes such as `SOURCE_STALE`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_SCENARIO`, `RATE_LIMITED`, `SCHEMA_INCOMPATIBLE`. No stack traces or credentials in responses. Versioned OpenAPI/JSON Schema fixtures test Python, web and Android compatibility.

## 8. Data acquisition and publication rights

Source register per provider: approved domain/endpoints, access method, quotas, caching limits, excerpt rights, attribution, public redistribution, commercial use, logo/image/video rights, expiry, contact and approval evidence.

Use manual curation or documented permitted API/RSS access before writing a crawler. Robots.txt compliance is necessary where applicable but is not a content licence. Do not bypass access controls, subscriptions or anti-bot restrictions. Do not send private cookies or subscriptions through a public ingestion server.

OpenF1 is a candidate historical provider, not a blanket licence for a commercial app. Its published materials distinguish historical/live access and intended uses. Confirm permission for intended redistribution and growth before public publishing of derived datasets. FastF1 remains an optional local adapter; its code licence does not settle underlying data rights. [OpenF1](https://openf1.org/).

F1's intellectual-property guidelines cover timing/statistics, audiovisual material and branding as well as articles. Link-first, original writing and independently created graphics reduce dependencies but do not automatically resolve every legal issue. Public release is gated on the intended use and jurisdiction. [F1 guidelines](https://www.formula1.com/en/information/guidelines.4EOKE9RRqevL4niTK9kWyt).

Provider outage path: retain permitted cached evidence, mark stale, stop unsupported conclusions, and never silently replace real data with synthetic data. Restricted source path: remove from export, retain only allowed metadata, invalidate derived publications as needed.

## 9. Editorial state machine

```text
discovered → fetched → parsed → deduplicated → drafted
                         ↘ quarantined
drafted → evidence_checked → rights_checked → reviewed → published
                                                     ↘ rejected
published → corrected / withdrawn / superseded
```

Approval attaches to a content revision, not a mutable record. Any material edit invalidates approval. A source update opens a review task; it must not silently change the published claim. The publication ledger records actor, time, reason, input revisions and affected surfaces.

MVP can implement this with validated files and Git history plus a local review command. A later GUI displays draft alongside evidence, conflict flags and rights constraints. Never put the local editor console on the public static host.

Editorial templates:

- News: changed fact, attribution, context, what is unknown, related entity/event.
- Incident: timeline, official finding, applicable rules, independent explanation, uncertainty.
- Strategy: information set, observed choice, alternatives, model assumptions, actual versus simulated outcome.
- Upgrade: documented change, stated objective, evidence of deployment, confounders.
- Story: chronology, citations, contested accounts, authorized clips, final fact-check.

Proposed solo cadence: two short briefs and one deeper piece per week off-race; one preview, one reviewed post-session/after-race brief and one deep dive on covered weekends. Full every-session coverage is not promised. Measure actual editorial hours before increasing cadence.

## 10. AI and agent topology

No external model is required for v1. Rules-based extraction, deterministic calculations and human writing can produce the initial experience. An existing chat subscription should not be assumed to provide free production API access. Local models are optional only after checking hardware, licence, speed and accuracy; never buy a GPU for the MVP by default.

If AI adds measurable value, use a bounded sequential pipeline:

1. Collect approved source IDs and permitted text.
2. Extract structured candidate facts/entities.
3. Retrieve relevant evidence and event-date rules.
4. Draft an explanation constrained to that evidence.
5. Validate schema, numerical facts, citations and unsupported claims.
6. Human approves publication.

Independent rules and strategy retrieval can run in parallel later, but agent agreement is not evidence. Disagreement routes to review; never lower a voting threshold to force a result. The publisher has no model-controlled permissions.

Handoff envelope: job_id, stage, schema_version, input hashes, allowed source IDs, output claims/evidence, missing information, failure code, model/prompt version, latency and token/cost usage. Tools are allowlisted. Retrieved text cannot change system prompts, issue shell commands, access secrets or trigger publication.

Hard limits proposed for a later pilot: maximum two model stages plus one validation pass for a brief; one retry for transient model failure; no recursion; per-job timeout; token ceiling; daily money cap defaulting to zero until approved. If quality is inadequate, fall back to human drafting rather than multiplying agents.

## 11. Retrieval design and evaluation

Initial corpus assumptions: tens to hundreds of approved documents, English, structured decisions/regulations plus original editorial content. These are planning assumptions, not current corpus size. Queries include exact rule lookup, historical incident comparison and multi-source strategy explanation.

Start with SQLite/PostgreSQL lexical search and entity/date filters. Regulations use document-aware chunks preserving article/subclause/page; decisions retain complete reasoning paragraphs; articles split at headings/paragraphs. Starting chunk experiment: roughly 300–600 tokens, small contextual overlap, no split that detaches a condition from its exception.

If lexical retrieval fails on measured queries, compare hybrid lexical+dense retrieval and a reranker. Add pgvector only with a hosted PostgreSQL stage or a suitable local index for research. Select embedding models from actual benchmark/cost/licence checks, not stale model-name claims. Never leak future rules through semantic similarity.

Evaluation set: at least 100 hand-reviewed questions balanced across rule lookup, ambiguous incidents, numerical statements, contradictory sources, unanswerable questions and wrong-season traps. Reserve a held-out portion before tuning. Measure Recall@k, Precision@k, ranking quality, citation entailment, unsupported material claims, abstention quality and latency. Precision@5 means relevant retrieved items divided by five, not “percentage of queries with all five correct.”

Proposed release bars: no wrong-season rule in critical test cases; every public material factual claim has supporting evidence; at least 95% support in blinded claim-level review of the evaluation sample; failures reported with sample size and confidence bounds. These are goals, not achieved scores. Automated model judges assist triage but do not establish truth alone.

Cache keys include source revisions, rule versions, query intent and model/prompt versions. Any relevant correction invalidates the answer. Do not stream an unverified accusatory conclusion before citations have been checked.

## 12. Strategy model and scientific standards

Baseline model: lap pace as a function of compound, tyre age, fuel proxy, track evolution, traffic and conditions, with explicit unknowns. Estimate pit-lane loss separately from stationary stop time. Model safety-car states separately; do not train normal-race degradation on mixed safety-car laps without handling them.

Cleaning: identify pit-in/out, yellow/red flag, wet-transition, missing and outlier laps; document exclusions instead of deleting inconvenient examples. Require minimum data coverage before fitting. Use simple explainable regression before complex ML.

Training/evaluation split by complete events and time, not random neighbouring laps. Compare to naive constant-pace and tyre-age baselines. Report MAE by phase/compound, interval coverage and error under distribution shift. Use bootstrap/sensitivity scenarios where defensible; don't treat unknown fuel/tyre state as observed truth.

Counterfactuals are model scenarios, not labels with known ground truth. Validate observed-path reconstruction and plausibility constraints, then show sensitivity ranges for alternatives. Do not claim “the team lost exactly 8.4 seconds” when the model ignores traffic or opponents' responses.

Version model artifacts, code, input IDs, seeds and assumptions. Separate educational branch challenges from validated predictive research. A model card documents intended use, unavailable inputs, evaluation data, failure cases and out-of-scope tracks/seasons.

## 13. Privacy and security

Zero-account launch minimizes data collection but hosting providers still process request metadata; publish an accurate notice rather than claiming “no data ever leaves your device.” Do not collect precise location, contacts, date of birth or advertising IDs. Timezone can be chosen manually or inferred locally from device settings.

Analytics initially uses opt-in research participants and coarse aggregate host statistics if available/appropriate. Do not fingerprint anonymous users to recover retention measurements. Define deletion/retention before adding identifiable analytics or accounts. Obtain jurisdiction-appropriate privacy advice before broad release or targeting minors; “everyone can use it” is not a compliance assessment.

Threat controls: source allowlists and SSRF protection; block private-network redirects; bounded decompression/PDF parsing; HTML sanitization; safe external URLs; CSP; dependency/secret scanning; no credentials in web bundles/APKs; authenticated editor roles and audit log if hosted; rate limits on future costly APIs.

Signing keys and deployment credentials stay outside source control with least privilege and backups. Android export/import validates file size/schema; imported data cannot execute scripts or replace trusted source policies. Simulations constrain numeric ranges, iterations and memory.

## 14. Reliability and scaling

Static v1 serves last-known-good content during producer outages. Separate site availability from editorial freshness. Add a visible coverage statement instead of a misleading service-level promise.

Capacity planning example, not a forecast: 1,000 readers × four page views × 250 KB/page is roughly 1 GB transferred before cache/media variation. 100,000 readers at the same profile is roughly 100 GB. Review hosting acceptable use and actual payloads before publicity; free tier is not an unlimited operational guarantee.

For a hosted stage: cache shared content, precompute common analyses, batch requests, use durable queues, idempotency keys, bounded retries and dead-letter review. A single popular story should not trigger one LLM call per visitor. Load shedding disables optional simulation before core reading.

Backup local editorial sources and database to a second user-approved location; don't assume a Git repository backs up ignored evidence/signing material. Test restoration. Maintain a release manifest and a previous static deploy for rollback. On source correction, republish affected items and invalidate caches; on suspected credential leakage, revoke/rotate and inspect audit history.

## 15. What changes when money is available

Only purchase against a measured bottleneck: reliable hosting for actual dynamic demand; commercial data rights for a defined use; a domain for identity; Play registration for validated Android distribution; AI credits if demonstrably reducing editorial effort without quality loss. Never equate sponsor access to an API with a commercial redistribution licence.
