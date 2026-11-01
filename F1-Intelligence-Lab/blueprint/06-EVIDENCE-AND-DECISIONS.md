# Evidence, assumptions and decision record

> **PROPOSED — NOT IMPLEMENTED.** This document is a planning artifact, not a description of current product capabilities.

Planning baseline: 26 October 2026. Sources describe capabilities and constraints, not guaranteed future availability. Recheck them at implementation and release. This is a planning record, not legal advice, a rights clearance, a completed UX audit or a production certification.

## 1. What is confirmed

The user wants a connected F1 web and Android ecosystem: news, replacements, upgrades, incident/rule explanations, strategy, stories, clip links and widgets. Both newer and technical fans are in scope, with beginner-first onboarding. Initial spending should be effectively zero. The existing local tools should become connected experiences rather than disappear in a rewrite.

The user requested a comprehensive plan. This document does not authorize paid services, account creation, public deployment, outreach, collecting personal data or purchasing media rights. Those are execution decisions when requested.

## 2. What remains an assumption

| Assumption | Why used | How to test or resolve |
|---|---|---|
| Solo/student builder | Budget and conversation context | Confirm actual weekly availability before sprint commitments |
| Existing computer can run local builds | Current local Python projects exist | Time a clean build and one analysis job on the machine |
| English-first | Reduces initial editorial and QA scope | Ask pilot users; test terminology comprehension |
| Web is the acquisition entry point | Shared links have lower friction than installing | Observe recipient activation from exact-content links |
| Widgets justify native Android work | Explicit user interest and useful schedule use case | Test a prototype widget before all native screens |
| Fans want explanations connected to evidence | Central differentiation hypothesis | Observe real use over two covered race weekends |
| A small editorial cadence is sustainable | Full-time news operation is unrealistic initially | Track actual time per reviewed item for four weeks |
| Static publication is sufficient initially | No live service is required for the launch wedge | Test whether delayed but accurate dossiers earn return |
| Users value spoiler controls | Likely important for asynchronous viewing | Test reveal behavior, previews and accidental exposure |

No TAM, willingness-to-pay figure, conversion rate, PMF score, viral coefficient or competitor user count has been established. Numerical gates elsewhere are proposed experiment decisions or illustrative arithmetic, not observed business results.

## 3. Primary-source register

### Competitive context

| Source | Finding used | Planning consequence |
|---|---|---|
| [Formula 1 app and website announcement](https://corp.formula1.com/formula-1-launches-newpersonalised-mobile-app-andwebsite/) | Official product describes personalized following, video, race and technical content | Personalization and a news feed alone are not a defensible difference |
| [Box Box](https://boxbox.club/) | Public product describes widgets, schedules, standings, news and alerts | Widgets are useful distribution/retention features, not a unique invention |
| [Motorsport app](https://www.motorsport.com/app/) | Established journalism and race coverage | Do not compete on volume or pretend a solo creator can match a newsroom |
| [Chequered](https://chequered.app/) | Product describes timing, news, widgets, upgrades, FIA documents and history | The broad ecosystem already has substantial overlap; validate explanation quality and connected workflows |

This was desk research of first-party pages, not a hands-on usability benchmark, market-share study or verification of every advertised feature. Feature availability can vary by platform and plan. No competitor weakness should appear in marketing without direct evidence.

### Content, data and rules

| Source | Finding used | Planning consequence |
|---|---|---|
| [OpenF1](https://openf1.org/) and [documentation](https://openf1.org/docs/) | Historical access and live access differ; usage context and access conditions matter | Historical analysis is the candidate starting point; do not budget free live timing or infer redistribution rights from API access |
| [Formula 1 guidelines](https://www.formula1.com/en/information/guidelines.4EOKE9RRqevL4niTK9kWyt) | Branding and content use have restrictions | Independent identity, original diagrams/writing, and a source-by-source permission gate; disclaimer is not permission |
| [FIA regulations index](https://www.fia.com/regulations/category/110) | Regulations are organized by category and version | Store exact document version/effective date, not just a generic regulation link |
| [2026 F1 driving standards guidelines](https://api.fia.com/sites/default/files/2026_f1_driving_standards_guidelines.pdf) | Driving assessment depends on relevant circumstances and guidance | Separate an official decision from educational interpretation; avoid automatic definitive video refereeing |
| [YouTube required minimum functionality](https://developers.google.com/youtube/terms/required-minimum-functionality) | Embedded player integrations have requirements | Use authorized links/embeds where permitted; never download or rehost broadcast clips as a workaround |

An accessible webpage, API response, repository or PDF is not automatically licensed for every reuse. Each source register entry must distinguish fetching, storing, transforming, publishing and commercial use. Permission uncertainty blocks the affected publication, not necessarily the entire original educational product. No permission was obtained during this planning exercise.

### Android and distribution

| Source | Finding used | Planning consequence |
|---|---|---|
| [Jetpack Glance](https://developer.android.com/develop/ui/compose/glance) and [widget management](https://developer.android.com/develop/ui/compose/glance/glance-app-widget) | Native widgets use their own lifecycle and update constraints | Persist cached state; design freshness and error states explicitly |
| [WorkManager work definitions](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work) | Background work depends on constraints and scheduling | Never promise exact minute-by-minute background refresh |
| [Verified App Links](https://developer.android.com/training/app-links/verify-applinks) | Website/app association must be configured and verified | Stable canonical routes, web fallback and explicit verification tests |
| [Alternative distribution](https://developer.android.com/distribute/marketing-tools/alternative-distribution) | Distribution outside Google Play is possible | Start with developer-device testing; assess tester distribution separately |
| [Android developer verification FAQ](https://developer.android.com/developer-verification/guides/faq) | Verification requirements depend on distribution context and rollout; development testing differs | Do not promise unrestricted worldwide free sideloading; check current account, region and device requirements |
| [Play account setup](https://support.google.com/googleplay/android-developer/answer/6112435) | One-time US$25 registration fee | Public Play launch is a later explicit expense, not part of the ₹0 promise |
| [Personal account testing requirements](https://support.google.com/googleplay/android-developer/answer/14151465) | Applicable newer personal accounts require 12 testers continuously opted in for 14 days before applying for production access | Reserve tester coordination time; completing testing does not guarantee approval |
| [Google Play payments policy](https://support.google.com/googleplay/android-developer/answer/9858738) | Digital purchases have billing requirements and exceptions | Revisit packaging and platform obligations before subscriptions |

### Hosting, quality and discoverability

| Source | Finding used | Planning consequence |
|---|---|---|
| [Next.js static exports](https://nextjs.org/docs/app/guides/static-exports) | Static export can run on static hosting, with server-feature limitations | No runtime server actions or database queries in the initial public site |
| [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) | Free-plan build/file limits; functions have separate limits | Keep a quota ledger, small artifacts and a migration path; do not promise unlimited hosting |
| [WCAG](https://www.w3.org/TR/wcag/) | Accessibility has testable success criteria | Target WCAG 2.2 AA with manual and automated checks, not an assumed grade |
| [Google helpful-content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) | Useful people-first content is the appropriate search foundation | Original useful explainers; no mass thin AI pages or guaranteed ranking claims |

Provider offers, account eligibility, platform requirements and source policies can change. Recheck before selecting dependencies, public release, accepting payments and enabling new source use. Record the checked date and actual accepted terms in implementation records.

## 4. Skills used and their concrete effects

The selected skills cover the decisions this plan actually makes. Unrelated skills and implementation-only tools were not loaded merely to increase the count.

| Skill | Effect on this blueprint |
|---|---|
| `before-you-build:before-you-build` | Added falsifiable demand/rights/workload risks and the smallest useful end-to-end release before ecosystem expansion |
| `borghei-c-level-advisor-cpo-advisor` | Separated portfolio investment from maintenance and deferred bets; tied modules to fan problems and decision gates |
| `borghei-business-growth-onboarding-cro` | Put a useful explanation before registration, made onboarding optional, and defined activation as a hypothesis to observe |
| `borghei-business-growth-referral-program` | Designed sharing after value, exact-content recipient landing, and explicit loop arithmetic without assuming virality |
| `borghei-business-growth-pricing-strategy` | Deferred prices until value and willingness to pay are understood; avoided arbitrary tiers and fake social proof |
| `borghei-engineering-design-auditor` | Defined screen/state completeness, visual consistency and future review gates without pretending an unbuilt design has passed an audit |
| `backend-development:architecture-patterns` | Kept domain logic independent of presentation/infrastructure and selected a small modular architecture rather than early distributed services |
| `borghei-engineering-rag-architect` | Required retrieval baselines, date/version-aware citations, abstention and evaluation before open-ended rule answers |
| `borghei-engineering-agent-workflow-designer` | Bounded optional AI assistance, kept human publication approval, and made zero model spending the default |

No skill script was run with fabricated usage, financial or model-evaluation data. Skills supplied methods; they did not establish product-market fit, code correctness, rights clearance or a validated design score. Skill guidance was reconciled against the user's beginner-first and near-zero-spend constraints.

## 5. Architecture and product decision records

### ADR-001 — Static public reader, local production

**Decision:** generate reviewed publication artifacts locally and publish a static website. Keep current Python analysis local initially.

**Alternatives:** always-on application/database; fully client-side raw telemetry processing; paid hosted AI service.

**Tradeoff:** lower operating cost and a useful site while the laptop is off, but no continuous live updates or cross-device account state. Public functionality must work from exported artifacts, not localhost endpoints.

**Revisit:** repeated demand for dynamic features with rights, funding and a sustainable maintenance owner.

### ADR-002 — Beginner-first, shared evidence

**Decision:** a simple explanation is the entry view, with analyst detail one action away on the same canonical item.

**Tradeoff:** more editorial and state testing than a single dense dashboard, but no separate contradictory beginner and expert knowledge bases.

**Revisit:** observed navigation/comprehension problems, not assumed sophistication based on age or identity.

### ADR-003 — Native Android after a useful web release

**Decision:** Kotlin/Compose reader with Glance widgets, local cache and shared publication schema.

**Tradeoff:** a second UI codebase and device testing; justified only if widgets/offline experiences earn use. A website wrapper does not itself solve widget behavior.

**Revisit:** widget tests show weak demand or native workload exceeds available time. The website remains a complete first product.

### ADR-004 — Editorial judgment before autonomous publishing

**Decision:** approved sources and structured records, optional bounded assistance, review tied to an exact content revision.

**Tradeoff:** slower news volume, lower risk of fabricated replacements, misunderstood rules and defamatory-looking conclusions. Agent agreement is not independent evidence.

**Revisit:** automation can expand for deterministic low-risk transformations after measured reliability, not blanket permission to publish.

### ADR-005 — No accounts, payments or community feed at launch

**Decision:** local preferences, saves and reading state; sharing as ordinary links.

**Tradeoff:** no sync, social graph or recurring billing. Much less friction, privacy handling, moderation and infrastructure work.

**Revisit:** users repeatedly request a specific account-backed benefit and retention supports the added burden.

### ADR-006 — Retrieval before generative answers

**Decision:** lexical search and curated source relationships first. Later grounded answers must use season/date filters and explicit uncertainty.

**Tradeoff:** less conversational flexibility, but discoverable evidence without mandatory model costs. Embeddings are optional after a measured retrieval failure, not a default architecture badge.

**Revisit:** evaluation shows a meaningful gain within rights, latency and cost constraints.

### ADR-007 — Rights-aware evidence rather than copied media inventory

**Decision:** original writing/graphics with source links, and permitted embeds only. Public data exports require a separate permission assessment.

**Tradeoff:** less visually spectacular than rehosting footage, but avoids building the core experience around unlicensed assets. Attribution alone does not solve permission.

**Revisit:** explicit licenses or partnerships with documented permitted use.

### ADR-008 — Free pilot, monetization after demonstrated value

**Decision:** no mandatory paid dependency or paywall. Investigate later premium analytical convenience rather than selling copied journalism.

**Tradeoff:** no immediate revenue; bounded scope and costs are essential. Do not fund the project through unproven acquisition spending.

**Revisit:** repeated voluntary use, customer interviews, commercial-use clearance and explicit budget approval.

## 6. Open decision log

| Question | Responsible role | Decision due | Safe default |
|---|---|---|---|
| Final brand and trademark/domain clearance | Founder; qualified advice if needed | Before public branding | Provisional independent project name |
| Exact source/asset publication permissions | Editorial owner | Before each source first publishes | Links and original rights-cleared material only; withhold uncertain assets |
| Available hours during semester/exams | Founder | Before timeboxed delivery | Plan in effort hours; no promised date |
| Which first race/incident/story can be responsibly covered? | Editorial owner | Before first dossier | Choose evidence/permission quality over fame |
| Can someone independently review contentious incidents? | Founder/editor | Before contentious interpretation publishes | Narrow educational scope, cite official outcome and label inference |
| Android minimum version and test devices | Engineering owner | Before native implementation | Select based on actual available devices and pilot audience |
| Current Android verification/distribution eligibility | Release owner | Before external APK distribution | Local emulator/own-device development testing |
| Hosting account eligibility and accepted terms | Founder | Before public deployment | Local preview; no automatic paid upgrade |
| Pilot analytics consent and data retention | Founder/privacy owner | Before event collection | No cross-user tracking; opt-in structured feedback |
| Need for sync or current/live feeds | Product owner | After two covered weekends of use | Defer; show explicit freshness |
| Any future paid service or store purchase | User | Before commitment | ₹0 limit; stop or reduce scope |

One person can fill several roles, but the work and decisions still exist. Unresolved launch-critical items are gates, not TODOs that can be hidden beneath a completed design checklist.

## 7. What was and was not verified in this planning pass

- Inspected the existing local project documentation and ecosystem module to ground the reuse strategy and distinguish narrow MVP behavior from future features.
- Consulted the first-party sources above for current planning constraints.
- Wrote product, experience, engineering, growth and delivery specifications as local Markdown documents.
- Did not implement the proposed frontend, Android app, source pipeline, trained model, authentication or payment system.
- Did not run a production load test, model evaluation, accessibility audit or user study. All their future gates remain work to do.
- Did not acquire rights, obtain legal approval, verify a final brand, contact creators, publish marketing or spend money.

The blueprint is intentionally detailed enough to implement and test, but not called perfect: evidence from users, rights review and real implementation must change it.
