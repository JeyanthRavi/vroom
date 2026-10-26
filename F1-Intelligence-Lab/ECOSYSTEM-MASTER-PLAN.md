# F1 ecosystem: product and delivery plan

> Updated planning reference: the [detailed blueprint](blueprint/README.md) supersedes this document where they differ. It incorporates the confirmed beginner-first audience and approximately ₹0 initial budget. This earlier plan is preserved for context.

Planning baseline: 26 October 2026. Proposed work, not implemented functionality.
Working product name: Paddock Atlas (availability and trademark clearance not checked).

## 1. Product promise and scope

Understand what happened in Formula 1, why it happened, and what evidence supports the explanation.

Audience: curious fans graduating from highlights to race understanding, plus technically minded fans who want to inspect data. Beginner explanations and analyst views share the same evidence.

Primary loop: read an update → open its race/team/driver → inspect strategy or incident → watch an authorized linked clip → follow the next development.

Start as a non-commercial research prototype. Public launch is a separate gate requiring source permissions and applicable rights review; a disclaimer alone is not permission.

### Pre-build risk review

- Verdict: high product risk, manageable staged engineering risk. Breadth, reliable editorial work and content rights are the hardest parts.
- Main assumption: fans will return for connected explanations rather than read headlines elsewhere.
- Smallest evidence: recruit 10–15 fans, publish one complete race dossier, and observe use over two race weekends. Proposed continuation threshold: at least five voluntarily return and three use the evidence/analysis links; this is a learning threshold, not a market benchmark.
- Demand: not validated. Interview fans about their last confusing race moment, not whether they like the idea.
- Positioning: an evidence-linked race companion, not another undifferentiated news feed.
- Retention: race-weekend updates, followed teams, spoiler-safe catch-up and daily short briefs.
- Distribution: original explainers shared in communities that allow them, search-indexable educational pages, and opt-in beta invitations. No automated spam.
- Monetization: defer subscriptions until recurring use and commercial rights are established. Possible paid value is advanced analysis/workspaces, not repackaged publisher articles.
- Adoption: make each tool reachable from a real story. A directory of unused dashboards is not success.
- Delay: global live coverage, comments, betting, automatic video refereeing, iOS and complex microservices.

## 2. Existing foundation versus proposed scope

Existing local MVPs: Telemetry Pit Crew, StewardLens, Pitwall Replay, ScoutGrid, ClaimCheck and FIA Archive. Current data: one recorded Monza qualifying session, one synthetic session, two official decision records. There is no production news ingestion, full-race replay, public account service, trained scouting model or Android app.

Retain working analysis services and regression tests. Replace the current inline-HTML portal incrementally with a component-based frontend; do not rewrite the analysis engines first. Keep compatibility routes until their consumers migrate.

## 3. Product modules

| Area | User experience | Initial release | Later release |
|---|---|---|---|
| Paddock Wire | Latest updates, driver replacements, contracts, injuries, personnel and calendar changes | Curated source-linked briefs; confirmed/reported/rumour labels | Permitted automated ingestion with review queue |
| Race Centre | One destination for a whole weekend | Schedule, results, stories, incidents and strategy tabs | Licensed live event timeline and timing |
| Upgrade Garage | What changed on each car and why | Team/component/event cards with declared intent and sources | Comparable deployment history and cautious performance analysis |
| Strategy Lab | Why a team pitted, alternatives and outcomes | Historical stint charts and decision-point explainers | Calibrated what-if simulator with uncertainty bands |
| StewardLens | Understand overtakes, incidents and penalties | Actual official decision alongside clearly separate analysis | Searchable precedent comparison and reviewed visual annotations |
| Pitwall Replay | Revisit the important moments | Existing lap-relative replay plus authored event timelines | True race-time alignment once data coverage supports it |
| Telemetry Pit Crew | Compare braking, speed and lap traces | Expand validated cached sessions | Reproducible analysis jobs and saved comparisons |
| ScoutGrid | Explore driver performance | Scoped same-session comparisons | Context-adjusted longitudinal research, not unsupported talent scores |
| ClaimCheck | Inspect what a claim is based on | Existing numeric checks and evidence cards | Reviewed text-claim evidence retrieval with abstention |
| Legends | Great races, rivalries, recoveries and innovations | Original illustrated, source-linked stories and clip links | Curated collections and interactive historical timelines |
| My Paddock | Personal companion | Follow teams/drivers locally; bookmarks; spoiler settings | Optional accounts and cross-device sync |
| Evidence Library | Browse sources behind everything | Versioned regulations, decisions, citations and provenance | Research workspace and export |

“Replacement” updates distinguish temporary substitute, confirmed permanent signing, reserve promotion and speculative seat report. Component replacement is separate from aerodynamic upgrades, with grid penalties linked only when documented.

## 4. Screen inventory and navigation

Web navigation: Home / Race Centre / Explore / Stories / My Paddock; global search and an expandable tools menu. Do not expose every internal project as a competing top-level navigation item.

Android bottom navigation: Today / Race / Explore / Saved. Team and driver following lives in onboarding and settings, without mandatory login.

Required public screens:

1. Today: weekend strip, top confirmed updates, short brief, team follows, latest explainer, story pick.
2. News index: category/team/driver filters, chronological ordering, source and publication/update timestamps.
3. News detail: summary, what changed, why it matters, sources, correction history and related race/analysis.
4. Race hub: overview, sessions, results, strategy, incidents, upgrades, clips and sources.
5. Driver/team profile: season-specific membership, history, news, upgrades and analyses.
6. Upgrade index/detail: component, deployment event, evidence, declared objective, uncertainty.
7. Strategy workbench: stint timeline, lap chart, decision markers, observed versus simulated toggle.
8. Incident detail: incident clock, clip links, diagrams, applicable rule version, official outcome, independent explanation.
9. Replay and telemetry: data coverage labels, playback, linked charts and accessible table alternatives.
10. ScoutGrid and ClaimCheck: retain explicit limitations; link each output to source inputs.
11. Legends index/story: editorial reading layout, chapter navigation, timeline, sources and clip availability.
12. Search: entities, news, races, incidents, rules and stories with content-type filters.
13. Saved/following and settings: spoiler mode, timezone, units, text size, notification categories, offline storage and privacy.
14. Editor console: ingestion inbox, duplicates, drafts, evidence inspector, approvals, scheduling, corrections, rights expiry and failures.

### Design contract

- Independent motorsport identity: graphite surfaces, restrained racing red, warm white text, original graphic assets and commercially usable fonts. Do not copy official logos/typeface.
- Condensed display headings; readable body text; tabular numerals for timing. Clear spacing and chart hierarchy take priority over decoration.
- Calm editorial pages; denser analyst workbenches. Provide light mode and system theme.
- Every card shows content type, timestamp and evidence status. Never label stale cached data “live”.
- Beginner/analyst toggle changes explanation depth, not facts or confidence.
- Spoiler mode hides results in feeds, search snippets, widgets and notifications consistently.
- Responsive coverage: phone, tablet, desktop; keyboard interaction, screen-reader labels, AA contrast, reduced motion and no colour-only chart encoding.
- Reusable components: SourceBadge, EvidenceDrawer, DriverChip, SessionStrip, StintChart, IncidentTimeline, ClipCard, FreshnessLabel and CorrectionNotice.
- Every data screen has loading, empty, offline, stale, partial-data and error states.

## 5. Editorial and evidence model

Each publishable item stores canonical source URL, publisher, source publication time, retrieval time, event time where known, content class, related entities, evidence references, rights state and revision history. Store permitted excerpts or metadata rather than assuming full-article copying is allowed.

Source status and analysis status are separate: official/attributed/unverified source; observed/inferred/simulated interpretation. An official team statement confirms what the team said, not every claimed performance benefit.

News workflow: approved source → fetch within policy → normalize → deduplicate → extract entities/claims → draft brief → verify citations → editor approval → publish → correction monitor.

Require review for rumours, replacements, safety/injury stories, blame, technical performance claims and rules interpretations. Repeated reports sourced from the same original report are not independent corroboration. Corrections update all derived cards and retract affected alerts where possible.

Suggested cadence is a configuration proposal, subject to source permission and quotas: ordinary news checks every 30–60 minutes; more frequent race-weekend checks only where allowed. Scheduled publishing is not a guarantee that sources are fresh. Preserve last successful sync and stale indicators.

## 6. Overtake and mistake analysis

Present these blocks in order:

1. What happened: event, session, lap/turn, drivers, footage angles and available data.
2. What officials decided: issued/no further action/pending/not investigated/unknown; exact document and outcome.
3. Applicable material: season, regulation issue, effective date, article, page and driving guidance. Driving guidance and binding regulations are not interchangeable.
4. Explanation: positioning, control, room, track limits and context supported by evidence.
5. Alternatives: illustrative safer choices, clearly identified as analysis.
6. Limitations: missing footage, missing steering/brake data, ambiguous visibility or no official finding.

Never infer a rule violation just because an overtake looked aggressive or a model predicted a penalty. No retrospective application of today's rules to a historical incident. Keep demonstration fixtures separate from published real incidents.

## 7. Strategy analysis and research

Inputs: lap/stint times, compound and tyre age, pit duration/loss, traffic, gaps, race control, weather and documented team explanations. Public data cannot reveal all private team objectives or forecasts.

For each decision, freeze the information available at that moment. Show observed choice; plausible motives; expected trade-offs; actual outcome; and alternatives. Distinguish decision quality from outcome luck.

Build in stages: transparent tyre-degradation baseline → pit-loss and traffic model → candidate-stop simulation → scenario/Monte Carlo uncertainty → out-of-sample evaluation. Use earlier races for training and hold out later races or complete events; do not randomly split neighbouring laps and call it generalisation.

Evaluate lap-time prediction error, uncertainty coverage, sensitivity to pit loss/weather/traffic, and historical replay consistency. Do not promise exact counterfactual finishing places. Simulated “two laps earlier” outcomes must display assumptions and ranges.

Upgrade analysis should control or discuss circuit, weather, tyres, fuel and driver differences. Before/after pace alone does not prove causal upgrade benefit.

## 8. Clips and storytelling

Curate outbound links to official F1/team/creator uploads with uploader, title, race context and optional verified timestamps. Embed only when the rights holder and platform permit the intended use. An enabled embed is not a blanket commercial licence.

Do not download/rehost broadcasts, extract unauthorized compilations or bypass subscriptions. Keep a text explanation available when videos are removed, age/region restricted or unavailable. Do not imply linked video synchronization is exact without a verified clock offset.

Stories are original editorial work with citations: event context → turning points → consequences → contested interpretations → authorized related clips. Initial collection should cover a mix of strategic wins, recovery drives, innovations and rivalries; choose final subjects after checking adequate sources and clip rights.

## 9. Android app and widgets

Proposed native stack: Kotlin, Jetpack Compose, Glance widgets, Room local cache, WorkManager scheduled sync, DataStore preferences and optional Firebase Cloud Messaging. Share backend contracts with web; do not duplicate analysis logic on the phone.

Widgets:

- Next session, small: event, session, local-time countdown and deep link.
- Weekend schedule, medium: remaining sessions and timezone-aware times.
- Paddock brief, wide: up to three approved headlines, last-update label and refresh action.
- Favourite team, medium: latest confirmed update and next session.
- Standings snapshot, medium: last confirmed standings, spoiler-safe option.
- Race status, later: coarse latest state and freshness, only with licensed supported data; tapping opens richer in-app view.

Widgets must handle resize, dark/light themes, process death, no network, notification denial and multiple independent instances. Cached state survives restarts. Respect Android scheduling and battery limits; no second-by-second network polling or guaranteed exact refresh schedule. Prefer a local countdown plus cached schedule over network updates for every tick.

App adds offline saved explainers, deep links from widgets, notification channels by topic/team, quiet hours, spoiler controls and optional biometric-free normal sign-in only if sync becomes useful. Store keys on the backend, never in APKs. Delete/export account data if accounts ship.

## 10. Architecture and data contracts

Start with a modular monolith, one shared API and background workers, not a microservice fleet.

Approved sources → ingestion jobs → normalized database + permitted source storage → deterministic analysis/retrieval → review queue → published content API → web / Android / widgets.

Proposed components:

- Web: React + TypeScript with Next.js for indexable editorial routes; client charts for interactive analysis.
- Backend: existing FastAPI services, gradually namespaced under /api/v1.
- Storage: PostgreSQL for content/entities; Parquet for large telemetry; object storage for permitted artifacts; Redis only when queues/caching justify it.
- Jobs: one durable worker queue with idempotent ingestion, bounded retries, backoff, dead-letter/review queue and per-provider rate limits.
- Search: PostgreSQL full-text initially. Add vector retrieval only after an evaluation demonstrates a benefit.
- Deployment: containers, managed database, HTTPS, staging and production separation, CI tests and explicit migrations.

Core entities: Season, Event, Session, Driver, Team, DriverTeamMembership, Source, SourceRevision, NewsItem, Claim, EvidenceReference, Upgrade, Incident, RegulationVersion, Decision, Lap, Stint, StrategyRun, Story, ClipReference, Follow and Bookmark.

Temporal joins are explicit: driver teams and rules change. Use stable internal IDs, provider ID mappings, UTC storage and user-local display. Evidence references capture source revision and supported claim, not just a generic bibliography.

APIs: feed cursor pagination; event aggregate; entity profiles; analysis job create/status/result; evidence retrieval; search; follows/bookmarks; widget snapshots. Response metadata includes schema version, generated_at, data_as_of, coverage, provenance and stale status. Queue costly work; never block a request on a full session ingestion.

## 11. AI/agent responsibilities

These are planned bounded pipeline roles, not deployed autonomous publishers:

- Collector finds items only from approved sources.
- Entity linker maps drivers/teams/races and flags ambiguous identity.
- News editor drafts concise original briefs with claim-level sources.
- Rules researcher retrieves event-date documents and relevant excerpts.
- Strategy analyst explains deterministic model output; does not invent telemetry.
- Story researcher assembles an evidence-backed outline and clip candidates.
- Verifier flags unsupported claims, conflicts, duplicate sourcing and missing rights.
- Human editor approves publication, especially contested claims.

All retrieved content is untrusted input. Agents cannot execute source instructions, read secrets, change permissions or publish directly. Cap calls/tokens/cost per job; cache reusable results; retain model/prompt/source revisions. Use deterministic numeric calculations and require abstention when evidence is missing.

## 12. Delivery roadmap and gates

Indicative effort: 20–30 focused developer-weeks for a dependable small beta with web plus native Android; substantially longer part-time and dependent on content work, licensing and model scope. This is a planning estimate, not a completion promise. Live coverage and mature ML are additional tracks.

| Phase | Effort | Deliverable | Exit gate |
|---|---|---|---|
| 0. Discovery and rights | 1–2 weeks | Fan interviews, approved-source register, one race dossier, screen map | Useful evidence loop demonstrated; permitted source list |
| 1. Shared foundation | 2–3 weeks | Database, stable IDs, provenance, API contracts, staging, CI, editor skeleton | Migrations/restore tested; existing services still pass regression tests |
| 2. Connected web alpha | 3–4 weeks | Today, news detail, race hub, incidents, strategy, Legends, shared navigation | One historical race links end-to-end with no fake live data |
| 3. Editorial ingestion | 3–4 weeks | Permission-aware connectors, deduplication, review/corrections, source health | Reprocessing is idempotent; failures/staleness visible; no unreviewed sensitive claims |
| 4. Analysis depth | 4–6 weeks | Historical strategy baseline, richer incident evidence, upgrades, analysis exports | Held-out evaluation published; simulations labeled; event-date rules verified |
| 5. Android beta | 4–6 weeks | Native app, offline reads, deep links, first three widgets, notification controls | Real-device checks across process death/offline/timezone/resize; spoiler consistency |
| 6. Hardening and release | 3–5 weeks | Performance/security testing, rights review, backups, privacy, store materials, support | Restore drill, staged release, monitoring and rollback verified |

Order is dependency-driven; do not build every module simultaneously. More people can overlap editorial/design/client work after API contracts stabilize, but coordination and review still cost time.

First vertical slice: a single historical race hub with five original briefs, one sourced incident, one strategy explainer, one story, verified outbound clips and links into existing tools. Then add the next-session Android widget using the same API.

## 13. Testing and operating the product

Automated: source parsing fixtures; entity mapping; timestamp/timezone boundaries; regulation effective dates; missing telemetry; claim provenance; ingestion duplicate/retry tests; API contracts; migration tests; numerical model regression; browser journeys; widget state tests.

Manual: editor source inspection; disputed incidents; video availability/rights; desktop/mobile/tablet layouts; accessibility; Android small/large fonts, launchers, battery-saving modes and interrupted sync.

Release requirements: every published factual brief has linked evidence; zero seeded fake-live states; all critical journeys pass; source failures are visible; privilege checks cover editor APIs; budget limits tested; no secrets in clients; database restoration demonstrated.

Security: sanitize source HTML, defend ingestion from SSRF with source allowlists and private-network blocks, isolate PDF parsing, enforce upload limits, protect admin with MFA, enforce roles/rate limits, redact logs, audit publish actions and pin dependencies.

Operations: source lag, job failures, publication corrections, API latency/errors, cache hit rate, crash-free sessions, cost per analysis, widget stale age and broken clip rate. Alert only on actionable thresholds. Back up daily initially and test restoration; choose explicit recovery targets before production.

Editorial workload is ongoing. Assign someone to source review, corrections, rights requests and incident coverage. If nobody is available, reduce coverage rather than auto-publish uncertain stories.

## 14. Budget and launch boundaries

Treat spending figures as provisional budget envelopes, not verified vendor quotes: local prototype using existing hardware can avoid new hosting spend; reserve roughly US$30–100/month for a small hosted pilot, then measure real compute, storage and egress. Model calls, live feeds, commercial data/media licences, store registration, domains and editorial labour are separate and may dominate. Obtain current quotations before selecting paid services.

Cap ingestion volume and model usage; precompute shared results; do not run an LLM independently for every visitor. Begin without paid AI if templates and human editing suffice.

Private alpha → invited web beta → Android internal/closed testing under current Play requirements → staged public launch after rights/security/privacy gates → optional live integration. Keep an immediate rollback path and content unpublish mechanism.

Success metrics: voluntary return on the next race weekend, readers opening evidence, story-to-analysis transitions, useful saved items, correction rate and widget retention. Page views alone are insufficient.

## 15. Explicit non-goals until justified

No broadcast streaming/rehosting; no claims of official affiliation; no guaranteed penalty prediction; no claims to know private team strategy; no complete field scouting from two laps; no guaranteed live widgets; no fake generated breaking news; no social network or betting layer in the first release.

## 16. Source checks used in this plan

- OpenF1 docs: https://openf1.org/docs/ — historical data since 2023; live access requires subscription. Access does not settle redistribution rights.
- OpenF1 intended use/licensing: https://openf1.org/ — educational/personal/research/non-commercial fan use; contact provider for other uses.
- FIA regulation index: https://www.fia.com/regulations/category/110 — resolve actual event-date version before analysis.
- FIA driving guidance: https://api.fia.com/sites/default/files/2026_f1_driving_standards_guidelines.pdf — guidance involves contextual assessment, not a single simplistic overtaking rule.
- F1 intellectual-property guidelines: https://www.formula1.com/en/information/guidelines.4EOKE9RRqevL4niTK9kWyt — linking/branding/content restrictions; obtain advice/permissions for intended public usage.
- Android Glance: https://developer.android.com/develop/ui/compose/glance — native widget implementation.
- Widget state and updates: https://developer.android.com/develop/ui/compose/glance/glance-app-widget — persistent application data and lifecycle-aware updates.
- YouTube integration requirements: https://developers.google.com/youtube/terms/required-minimum-functionality — official player requirements; links are the initial default.

These references informed feasibility, not legal clearance or a guarantee of future provider availability. Recheck policies and Android/Play requirements before implementation and release.
