# 05 — Execution, backlog, testing and release

## 1. Delivery strategy

Ship complete user journeys in small releases. A beautiful empty ecosystem is less valuable than one excellent race dossier. Keep research-heavy features behind explicit gates rather than letting them block useful editorial work.

Default team assumption: one student builder, occasional volunteer testers, no hired editor or paid services. Separate engineering time from editorial time and learning time. Tasks in this document are planned, not tickets already created in an external system.

## 2. Milestones and planning ranges

| Milestone | Focused engineering hours | Dependencies | Visible result |
|---|---:|---|---|
| M0: evidence and scope | 12–20 | None | Source register, interviews, chosen dossier, fixtures |
| M1: connected web slice | 55–90 | M0 and publication permissions | Reading UI, race hub, moments, evidence, sharing |
| M2: trustworthy publication | 35–60 | M1 schemas | Review/export workflow, corrections, static deploy |
| M3: useful analysis | 70–120 | Source/data quality | Existing tools connected; curated strategy branches |
| M4: wider editorial beta | 45–75 | Repeatable review | News/upgrades/Legends/search/follows with sufficient content |
| M5: native Android beta | 90–150 | Stable snapshot contract | Offline reader, deep links, first three widgets |
| M6: hardening and distribution | 45–85 | All critical paths | Accessibility, device tests, restore/rollback, release readiness |
| **Scoped beta subtotal** | **352–600** | Rights, learning and tester availability | A small dependable product, not every future feature |

Add 25–35% contingency when estimating calendars: roughly 440–810 engineering hours. At 10 hours/week this is about 44–81 weeks, excluding ongoing editorial work and exams. At 30 hours/week it is about 15–27 weeks. These ranges are coarse planning assumptions, not commitments. The first web slice is 55–90 hours after M0, or 67–110 hours including M0 before contingency; start testing then. A dependable public release also needs the relevant M2 publication and release gates.

The ambitious long-term ecosystem adds unestimated tracks: validated strategy ML, contextual scouting, broad historical coverage, licensed live data, account sync, creator tools and community moderation. Scope each only after its evidence gate. AI assistance may speed implementation but does not remove validation, licensing, design or operational work.

## 3. Release contents

### R0 — private proof

One example journey, local data, no public publishing, no external accounts. Demonstrate beginner/analyst depth and official-versus-inferred separation. Confirm source rights and identify gaps.

### R1 — first public web release, rights permitting

One reviewed historical dossier, Today, ten moments, one strategy explainer, incident pages, evidence drawers, one Legends story, local bookmarks/follows, safe share cards, methodology/corrections/privacy pages. Static snapshots only. All public tools use publishable data or an explicitly synthetic educational example.

### R2 — repeatable companion

More covered events, modest news cadence, upgrades timeline, search, existing telemetry/replay/scout/numeric claim tools integrated through static adapters, editorial workflow and source health. No promise of comprehensive current coverage.

### R3 — Android pilot

Today/Race/Explore/Saved, offline content, first three widgets, safe deep links, best-effort local reminders, export/import. Local device/emulator testing first; external APK distribution only after applicable verification requirements are checked.

### R4 — public Android / sustainable operations

Store or compliant alternative distribution, device coverage, rights/privacy checks, crash monitoring where appropriate, support process and sustainable publishing schedule. Paid capabilities still require separate budget approval.

## 4. Dependency graph

```text
Rights register + selected use case
          ↓
Entities + publication schemas + fixtures
          ↓
Core reading/evidence UI → shareable moment → pilot feedback
          ↓
Review/export + static hosting + correction handling
          ↓
Analysis adapters + content breadth + search
          ↓
Stable snapshot contract → Android reader → widgets → distribution
          ↓
Retention evidence + approved budget → optional hosted services/live/AI
```

Critical path is not “build every agent.” It is source permission, trustworthy content, schema stability, user comprehension and reliable delivery.

## 5. Prioritized implementation backlog

Roles are responsibilities, not new hires: Builder, Editor, Reviewer and Tester may be the same person at different stages. High-risk interpretations benefit from a second informed reviewer; when unavailable, publish less ambitious factual summaries or mark interpretation clearly.

| ID | Work item | Priority / owner | Depends on | Acceptance evidence |
|---|---|---|---|---|
| B01 | Audit current apps and tests | P0 Builder | — | Baseline test log, route/data inventory, limitations recorded |
| B02 | Create source/use register | P0 Editor | — | Permission status for every planned public source/asset |
| B03 | Choose pilot race and stories | P0 Editor | B02 | Enough evidence for complete journey; no invented coverage |
| B04 | Interview/recruit pilot fans | P0 Builder | — | Consented notes and pain examples; no fake demand metrics |
| B05 | Define entity IDs and dates | P0 Builder | B01 | Session/team membership fixtures cover historical changes |
| B06 | Define publication JSON schemas | P0 Builder | B05 | Valid/invalid fixtures and version compatibility tests |
| B07 | Define content and spoiler fields | P0 Editor | B06 | Safe previews and reveal examples for every content type |
| B08 | Write first dossier content | P0 Editor | B02,B03,B07 | Claim-source mappings and original prose reviewed |
| B09 | Create tokens/components | P0 Builder | B07 | States, responsive examples, actual contrast checks |
| B10 | Build moment detail/evidence | P0 Builder | B06,B08,B09 | Beginner and analyst tasks succeed without login |
| B11 | Build race hub and brief | P0 Builder | B10 | Ten linked moments, explicit scope and caught-up state |
| B12 | Add spoiler policy | P0 Builder | B07,B10 | No seeded forbidden fields in safe UI/metadata |
| B13 | Add local saves/follows | P1 Builder | B06,B10 | Persistence, reset and storage-unavailable behavior |
| B14 | Build share cards/links | P0 Builder | B10,B12 | Original source-bearing card, useful recipient page |
| B15 | Add source/correction pages | P0 Builder | B06,B08 | Revision history and withdrawn-content state |
| B16 | Validate publication export | P0 Builder | B06,B08 | Block missing citations, unknown rights and demo leakage |
| B17 | Atomic snapshot manifest | P0 Builder | B16 | Interrupted export cannot replace last-known-good |
| B18 | Static web export | P0 Builder | B11,B17 | All routes work without local API; no runtime server dependency |
| B19 | Review hosting/account limits | P0 Builder | B18 | Zero-spend settings checked; deployment approval separate |
| B20 | Publish approved R1 | P0 Builder | B02,B12,B15,B18,B19 | Live URL smoke test, rollback artifact, no private data |
| B21 | Conduct usability round | P0 Tester | B11 or B20 | Five critical tasks observed, severity-ranked issues |
| B22 | Connect telemetry snapshots | P1 Builder | B06,B16 | Compatible comparisons, coverage, units and chart/table checks |
| B23 | Connect lap replay | P1 Builder | B22 | Honest clock mode, seek/pause/gap states |
| B24 | Connect ScoutGrid | P1 Builder | B22 | Subset denominator and no talent-score claims |
| B25 | Connect numerical ClaimCheck | P1 Builder | B06,B16 | Same tolerance/sign rules as tested backend fixtures |
| B26 | Curate real incident page | P0 Editor | B02,B10 | Official decision separated from interpretation; correct rule issue |
| B27 | Curate strategy challenge | P1 Editor/Builder | B08,B10 | Frozen information set, labelled branches, no future leakage |
| B28 | Add news grouping | P1 Builder | B06,B16 | Duplicates retain distinct/common-origin sources |
| B29 | Build local review interface | P1 Builder | B16 | Draft state, evidence/rights flags, revision-specific approval |
| B30 | Add upgrade timeline | P1 Editor/Builder | B05,B10 | Intent/fitment/effect uncertainty separate |
| B31 | Publish Legends template | P1 Editor/Builder | B10,B16 | Original story, sources, clip unavailable fallback |
| B32 | Add lexical search | P1 Builder | B18 | Typed results, neutral preview, no restricted/draft leakage |
| B33 | Add local export/import | P1 Builder | B13 | Schema/size validation, merge preview and recovery |
| B34 | Define opt-in measurement | P1 Builder | B04,B21 | Event allowlist, consent coverage, no fingerprinting |
| B35 | Run second-weekend pilot | P0 Tester | B21 fixes | Voluntary return + comprehension notes |
| B36 | Create Android project/repository | P1 Builder | B06 stable | Bundled and HTTPS snapshot adapters share fixture behavior |
| B37 | Android reader/navigation | P1 Builder | B36 | Today/Race/Explore/Saved + process recreation |
| B38 | Room/DataStore offline state | P1 Builder | B36 | Interrupted sync retains valid content/preferences |
| B39 | Android deep links/share | P1 Builder | B37 | Event/source/depth route preserved; web fallback |
| B40 | Next-session widget | P1 Builder | B38 | Resize/reboot/timezone/offline tests |
| B41 | Weekend schedule widget | P1 Builder | B40 | TBC/postponement/long labels/multiple instances |
| B42 | Brief widget | P1 Builder | B38,B12 | Neutral titles, staleness, withdrawn-item behavior |
| B43 | Widget configuration/preview | P1 Builder | B40–B42 | Per-instance settings and readable previews |
| B44 | Android signing/test distribution | P0 Builder | B37–B43 | Keys protected, verification rules checked, install/update tested |
| B45 | Accessibility/device round | P0 Tester | Web + Android UI | Keyboard, TalkBack, font scaling, low-end device evidence |
| B46 | Security/rights review | P0 Reviewer | Export + distribution | No critical leak or unsupported publishing permission |
| B47 | Restore/rollback drill | P0 Builder | B17,B20 | Demonstrated recovery with timestamps |
| B48 | Release/support package | P0 Editor/Builder | B45–B47 | Accurate screenshots, privacy, coverage, contact, known limits |
| B49 | Strategy baseline research | P2 Researcher | More valid historical data | Held-out errors, model card, baseline comparison |
| B50 | Text retrieval pilot | P2 Researcher | Approved corpus | Wrong-season/unanswerable tests and citation audit |
| B51 | Paid/live/account proposals | Deferred | Retention + rights + budget | Separate decision record and spending authorization |

P0 means required for the relevant release, not that every row must precede the first prototype. Work-in-progress limit: one engineering slice plus one editorial slice at a time for a solo builder.

## 6. First 30 focused hours

| Hours | Work | Completion artifact |
|---|---|---|
| 0–4 | Confirm current code/data and source constraints | Inventory and selected example |
| 4–8 | Write one complete explanation manually | Reviewed text with sources and uncertainty |
| 8–12 | Define small schemas and spoiler fixtures | Validated sample publication |
| 12–20 | Build moment/evidence UI in two depth modes | Working narrow end-to-end page |
| 20–24 | Add safe share destination and mobile layout | Usable share link and card prototype |
| 24–28 | Observe three to five fans using it | Actual misunderstandings and task outcomes |
| 28–30 | Fix highest-severity issue and rescope | Updated backlog based on evidence |

These blocks are allocation suggestions, not claims that each task certainly fits. If the first explanation cannot be sourced or understood, don't spend the remaining hours on animated dashboards.

## 7. Calendar planning without invented dates

At roughly 10 engineering hours/week: weeks 1–3 deliver the first narrow prototype; weeks 4–10 expand toward R1 if evidence/rights cooperate. Android begins after schemas and web value stabilize, not necessarily in week 11. Exams and content production need separate capacity. Review scope every two weeks and stop low-value branches.

A funded multi-person team could overlap frontend, Android and editorial work after contracts stabilize. Do not divide the total hours by headcount blindly: integration, onboarding and review add work.

## 8. Test matrix

| Layer | Essential tests | Failure consequence |
|---|---|---|
| Domain | IDs, temporal membership, rule applicability, units | Wrong historical attribution/rule |
| Sources | Parser fixtures, quota handling, redirects, rights states | Invalid/unauthorized data published |
| Publication | Citations, approval invalidation, tombstones, atomic manifests | False or partial content |
| Numeric analysis | Delta signs/tolerance, missing data, reproducibility | Incorrect conclusions |
| Scenario analysis | Future leakage, invalid combinations, bounded runtime | Misleading or expensive simulations |
| Retrieval | Wrong season, contradictory evidence, missing answer, injection | Confident false explanation |
| Web | Reading/share/save/search journeys, keyboard, safe metadata | Friction, spoilers, exclusion |
| Android | Process death, offline merge, deep links, signing upgrade | Data loss or broken installs |
| Widgets | Resize, multiple instances, timezone, stale snapshot | Misleading schedule or unreadable widget |
| Security | HTML injection, SSRF, oversized inputs, secrets | Compromise or disclosure |
| Operations | Restore, rollback, expired source, failed deploy | Unrecoverable or stale service |

Use synthetic edge-case fixtures alongside permitted real examples. No automated test should fetch a paid/live source without explicit test configuration. Separate deterministic CI tests from optional network/provider smoke tests.

## 9. Release definition of done

- All P0 requirements for that release have linked evidence.
- No known critical security, data-integrity, spoiler or accessibility blocker.
- All public factual material has inspectable support and publication permission review.
- Demo/generated content cannot be mistaken for a real report.
- Current baseline tests remain passing; new contracts have tests across clients.
- Web works without the producer laptop or local API.
- Cost defaults cannot call paid services; quota exhaustion has a safe fallback.
- Privacy/support/methodology/coverage notices describe actual behavior.
- A previous version can be restored; signing/deployment keys are protected.
- Human signs off on public distribution and any paid account/service separately.

## 10. Budget ledger

| Item | Start | Condition for spending |
|---|---|---|
| Local development/analysis | Existing hardware; no new cash assumed | Don't buy hardware until bottleneck measured |
| Static hosting | Eligible free plan/subdomain | Upgrade only after observed limit and user approval |
| Database | Local SQLite | Hosted sync/editor need proven |
| AI | Templates/human; optional existing local model | Measured time saved with quality; explicit daily cap |
| Live data | Not included | Rights, budget, reliable product need |
| Images/clips | Original assets + authorized links | Written licence when required |
| Domain | Deferred | User chooses name and approves cost |
| Android development | Local tooling/device/emulator | No Play fee needed for local development |
| Public Play distribution | Deferred | Official one-time US$25 fee plus eligibility requirements |
| Advertising | ₹0 | Retention and viable economics demonstrated |
| Email/push/backend | Deferred | Actual need and cost-controlled provider review |

“₹0” means no intended new paid subscriptions, assuming existing hardware/internet. It does not mean zero time/electricity or free public rights. Free-tier availability and policies can change. No account has been created or billing enabled by this plan.

Play's current help page specifies a US$25 registration fee. New personal accounts subject to testing rules need at least 12 testers continuously opted in for 14 days before applying for production access; this is not an approval guarantee. Recheck the actual account and current rules at release. [Registration](https://support.google.com/googleplay/android-developer/answer/6112435), [testing](https://support.google.com/googleplay/android-developer/answer/14151465).

## 11. Risk register

| Risk | Early signal | Mitigation | Owner |
|---|---|---|---|
| No differentiated value | Fans describe it as another feed | Narrow to one explanation journey; observe use | Product |
| Content rights blocked | Unknown or denied redistribution | Link-first original editorial; exclude restricted data | Editor |
| Editorial burnout | Missed updates, rushed fact-checks | Cover fewer events, fixed cadence, no 24/7 claim | Editor |
| Fake analytical certainty | Readers confuse scenario with fact | Strong labels, model cards, evidence audits | Research |
| Spoiler leakage | Result in preview/widget/alt text | Global policy + seeded tests | Design/QA |
| Surprise costs | API calls per visitor, card-backed tiers | Static delivery, zero default model budget | Builder |
| Provider outage | Repeated fetch errors or stale data | Cache, coverage labels, pause affected claims | Builder |
| Rule/version drift | Current article cited for old incident | Temporal filtering and critical fixtures | Research |
| APK distribution friction | Tester cannot install/update | Verify current platform rules; prioritize web | Android |
| Scope explosion | Many unfinished screens | WIP limit, milestone gates, defer list | Product |
| Trust loss | Wrong factual claim spreads | Corrections, source audit, rapid withdrawal | Editor |
| Malicious content/input | Source contains instructions/scripts | Isolation, allowlists, sanitization, no tool authority | Builder |
| Growth overload | Traffic/feedback exceeds capacity | Static core, pause optional features, clear coverage | Operations |

## 12. Operational runbooks

### Incorrect news/analysis

Flag affected revision → stop promotion → verify primary evidence → correct or withdraw → republish canonical page and dependent cards → invalidate relevant cached analysis → document cause → add regression case. Do not silently edit a materially wrong claim. Offline/exported images may remain outside control; linked correction page is the durable record.

### Source revoked or unavailable

Determine whether temporary outage or permission issue → pause ingestion → mark freshness/availability → remove prohibited exported material → regenerate dependent pages → verify residual caches/tombstones → record restoration conditions. Don't solve permission loss by scraping a mirror.

### Traffic spike

Verify core static pages load → inspect current host quotas → disable optional dynamic jobs if present → preserve reading/source links → communicate temporary limits → do not authorize spending automatically. A viral spike that produces incorrect or broken pages is not success.

### Failed release

Keep previous manifest active → inspect failed validation/build → restore last tested deployment if necessary → verify key routes and source links → fix in staging/local → rerun gates. No production editing without a recoverable artifact.

### Lost signing/deployment credential

Revoke compromised credentials where applicable → inspect access → restore from approved secure backup or follow provider recovery → verify app update continuity. Never paste private keys into issue trackers or analytics logs.

## 13. Launch checklist

Private cohort invite → fix severe issues → source/rights approval → static web release → observe two covered weekends → broaden content carefully → native local testing → compliant tester distribution → platform-specific release review → staged rollout.

Marketing assets must show real available features and real data mode. No “live” badge for historical playback, no fake user count, no paid plan that doesn't exist and no borrowed logos implying affiliation. Contacting creators, registering domains, deploying publicly and spending money require the corresponding explicit user instruction at execution time.

## 14. Decision cadence

Weekly: what did users understand, what broke, how many editorial hours, any correction, any cost risk?

Every two covered race weekends: which feature earned voluntary return, which was ignored, which should be cut?

Before each new major module: user problem, source rights, cheapest test, estimated ownership burden, success/stop criterion. A perfect plan is impossible; a disciplined feedback loop is the mechanism that improves it.
