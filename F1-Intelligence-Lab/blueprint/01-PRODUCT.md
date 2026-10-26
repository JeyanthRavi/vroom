# 01 — Product strategy and requirements

Status: proposed. Requirements are written for a near-zero-cash solo/student build. Customer demand, activation and willingness-to-pay are unmeasured.

## 1. Product thesis

The product should turn fragmented F1 information into understanding. A headline is an entry point, not the final product. The unit of value is a **race moment**: a specific event connected to what happened, why it matters, the evidence, the relevant rule or strategy and what changed afterwards.

Positioning statement: for fans who want to understand F1 beyond headlines, Paddock Atlas is an independent race companion that connects concise explanations to inspectable evidence and interactive analysis. It complements official coverage; it does not replace broadcasts or pretend to be an official service.

Candidate landing copy:

> Understand the race. Not just the result.
>
> Catch up on the turning points, unpack the strategy, and see the evidence behind the call.
>
> Primary action: Explore a race. Secondary action: See how it works.

Avoid generic promises such as “the ultimate AI-powered ecosystem,” fabricated social proof, unsupported accuracy claims and “everything live.” Demonstrate an actual explanation immediately.

## 2. Competitive reality

Desk research of first-party descriptions, checked 26 October 2026. This is not a hands-on competitive usability audit, and omitted features should not be treated as absent.

| Alternative | Publicly described strengths | Our implication |
|---|---|---|
| Official F1 app/site | Personalized drivers/teams, news, technical analysis, video and timing integration | Personalization and broad coverage are table stakes, not novel claims |
| Box Box Club | Widgets, schedules, standings, news and driver/team information | A nice countdown widget alone will not differentiate us |
| Motorsport.com app | Journalism, alerts, statistics and live coverage | Do not compete on newsroom breadth or fastest breaking news |
| Chequered | Timing, widgets, news summaries, upgrades, FIA documents and historical exploration | Even the all-in-one combination already overlaps strongly |
| Existing fan workflow | Video creators, official clips, chats, searches and multiple sites | Win one repeat task better before asking users to switch habits |

Evidence: [F1 relaunch](https://corp.formula1.com/formula-1-launches-newpersonalised-mobile-app-andwebsite/), [Box Box](https://boxbox.club/), [Motorsport app](https://www.motorsport.com/app/), [Chequered](https://chequered.app/).

**Differentiation hypothesis, not proven moat:** coherent moment-by-moment explanations, event-date rules, explicit uncertainty, reproducible scenario comparisons and the same underlying evidence in beginner/analyst modes. Long-term defensibility would come from reviewed linked datasets, quality evaluation, trustworthy corrections and an audience relationship—not the number of LLM agents.

## 3. Users and jobs

| Segment | Trigger | Job | Success | Avoid |
|---|---|---|---|---|
| New fan | Confusing pit stop or penalty | Explain this without assuming years of knowledge | Can describe the decision in their own words | Jargon, giant dashboards, forced onboarding |
| Busy fan | Missed a weekend/session | Catch me up without accidental spoilers | Chooses depth and finishes a bounded brief | Infinite scrolling and surprise results |
| Analyst fan | Controversial strategy or pace claim | Show data, assumptions and alternatives | Can reproduce or challenge the conclusion | Opaque scores, fake precision |
| Story fan | Off-week or new favourite driver | Give context and memorable history | Completes a sourced narrative and explores related events | Recycled articles and unauthorized video |
| Creator/club organiser | Needs an explanation to share | Communicate a race moment accurately | Shares a source-bearing card and useful destination | Watermark spam, misleading chart crops |

Launch is beginner-first, not beginner-only. A single depth control changes presentation; it must not change evidence status, verdict, cited article or measured value.

## 4. Signature experiences

### S1. Catch Me Up

Inputs: event/session, “avoid results” or “show all,” optional followed teams and reading depth. Output: five to ten reviewed moments, ordered chronologically or by selected editorial importance, with a visible end.

Modes: one-minute overview; three-minute explanation; analyst dossier. These are approximate reading targets, not generated text-length promises. Unknown coverage is displayed. “Since last visit” compares known published revisions, not inferred unseen real-world events.

Acceptance: first useful moment is reachable with no login; changing spoiler mode cannot leak results in title, image, accessible name or share preview; related links preserve event/depth context; a “caught up” screen offers save/close/next topic without pressure.

### S2. Why Did That Happen?

Reusable explanation format: what happened → decision context → official finding if applicable → evidence → uncertainty → consequences. Entry from a news card, timeline marker, widget or shared link. “Explain this term” opens a concise glossary overlay without losing position.

Acceptance: every material factual statement maps to evidence or is explicitly attributed/inferred; “unknown” is a valid result; sources open at the relevant page/section where supported; corrections are visible.

### S3. You’re on the Pit Wall

A historical decision challenge stops just before a pit call. It shows only information available then, asks the user to select a plausible action, and reveals the actual decision and trade-offs afterwards. No cash prizes, wagers or fabricated superiority score.

First version: three curated branches, precomputed locally. Later: bounded client-side simulation for approved scenarios. The educational takeaway is why the decision was difficult, not shaming a user or driver.

Acceptance: no future weather/incident leakage in inputs; unknown tyre condition is disclosed; replay reveals the actual outcome separately from simulated alternatives; model assumptions are inspectable.

### S4. Evidence Cards

Share a single useful finding with event context, source badge, observed/inferred/simulated label and canonical link. Recipient sees the actual insight before any install prompt. A screenshot is not silently updated after correction; the linked page is, and contains revision history.

### S5. My Race Companion

Useful schedules, calm briefings and small widgets that reflect followed teams and spoiler preferences. No artificially urgent alert for trivial updates. The product remains valuable without notifications enabled.

## 5. Detailed module PRDs

### P01 — Today and Paddock Wire

- Goal: understand the important developments without reading duplicate stories.
- Categories: confirmed driver replacement; contract/seat report; component replacement; aero upgrade; race/session update; rule change; strategy explainer; historical feature.
- Each brief: original headline, short original summary, what changed, why it matters, source links, publication/update/event times, status and connected entities.
- Labels: official announcement, attributed report, unverified report, analysis, correction. A team claim remains a team claim even when officially published.
- Group duplicate coverage by event/claim, retain sources, and identify a common original source. Three derivative articles are not three confirmations.
- Initial operations: manually authored or reviewed batches; no 24/7 breaking-news promise.
- Acceptance: sorting uses publication time consistently; correction time does not masquerade as a brand-new scoop; missing dates are explicit; a stale feed shows “last published” time.
- Failure: source unavailable → retain permitted metadata and disclose unavailable link; insufficient evidence → draft remains unpublished.

### P02 — Race Centre

- Canonical hub for season/event/session; tabs Overview, Moments, Strategy, Incidents, Upgrades, Data, Sources.
- Before event: schedule, circuit-specific educational notes and coverage plan.
- During event in zero-cost mode: cached schedule and clearly labelled editorial updates when available, not a fake live ticker.
- After event: reviewed results if rights permit, key moments, debrief and corrections.
- Separate race laps from driver lap number, elapsed session time and UTC timestamps. Sprint and qualifying formats are explicit.
- Acceptance: timezone change updates schedules; postponed/cancelled/unknown states exist; missing session is not mistaken for “no incidents.”

### P03 — Upgrade Garage

- Filter by team, event, component and status; follow deployment across weekends.
- Card fields: component family, first reported/declared event, car/driver fitment if documented, stated objective, source, confidence basis and withdrawn/retained status.
- Use original simplified diagrams or licensed images. Diagram should never imply engineering dimensions or geometry not supported by evidence.
- Distinguish aerodynamic development, track-specific configuration, repair and regulated component replacement.
- Analyst view: controlled comparison assumptions, confounders and sample coverage. “Performance effect unknown” is preferable to invented tenths.
- Acceptance: no causal benefit inferred solely from qualifying position; version history allows later reinterpretation; penalties link to actual decisions.

### P04 — StewardLens and Incident Desk

- Real cases show official state: pending, decision issued, no further action, no document found, or unknown.
- Dossier includes event/turn/lap, involved drivers, evidence inventory, applicable regulation version, decision document and independent explanation.
- Rule relevance is not proof of breach. Guidance is distinguished from binding regulation. Appeals/reviews update disposition without erasing original decisions.
- “Mistake” taxonomy: documented rule breach; execution error supported by evidence; strategy outcome; disputed interpretation. Avoid intent/motive attribution without evidence.
- Optional original diagrams show positions with uncertainty; no invented video frame measurements.
- Acceptance: event-date rules resolve deterministically; historical cases never default to current rules; absent footage is marked; synthetic demos cannot appear in real news feeds.

### P05 — Strategy Lab

- Show stint timelines, pit-loss assumptions, traffic, tyre age, weather, safety-car conditions and relevant team statements.
- Separate observed decision, inferred motivation, model prediction, actual outcome and counterfactual result.
- V1: authored explanation plus precomputed branches. V2: explainable degradation/traffic baseline. V3: calibrated simulation and held-out evaluation.
- Controls: stop lap, available compound, pit-loss range; disable impossible/unsupported choices and explain why.
- Rule constraints must come from event-specific configuration, not a universally hardcoded tyre rule.
- Acceptance: same inputs/seed/model version reproduce output; unsupported scenarios fail visibly; model cannot use future events unless user explicitly selects retrospective scenario mode.

### P06 — Pitwall Replay

- Preserve current lap-relative replay as a named mode; do not call it simultaneous race reconstruction.
- Later race replay aligns real event timestamps, pit-lane states, lapped cars and gaps. Missing intervals remain gaps.
- Timeline markers deep-link to incident and strategy explanations. User can pause, scrub, change speed and reset.
- Do not interpolate a path through unknown GPS coverage or invent overtakes from position samples alone.
- Acceptance: clocks are labelled; seek updates all linked panels; background tabs pause rendering; accessibility has a textual event list.

### P07 — Telemetry Pit Crew

- Select compatible session/laps, compare speed/throttle/brake/gear where available, inspect derived deltas and export a reproducibility manifest.
- Show sampling frequency/coverage, normalization method and units. Gear/throttle are observed signals, not direct evidence of driver intent.
- Browser-friendly downsampled charts preserve important extrema; full source references remain available where permitted.
- Acceptance: no cross-session comparison without explicit warning/context; gaps not bridged silently; chart summary and table work without colour discrimination.

### P08 — ScoutGrid

- Initial product: performance explorer for available laps, not “AI driver talent ranking.”
- Longer-term: within-team/context-adjusted comparisons, qualifying/race consistency, sample size and uncertainty.
- Research controls: era/car/circuit/conditions, selection effects, changing teammates, retirements and incomplete records.
- Acceptance: filters always expose coverage denominator; two stored laps never produce a complete-grid claim; rankings describe the measured metric only.

### P09 — ClaimCheck and Evidence Library

- Keep deterministic numeric checks: lap time, signed delta, documented penalty seconds.
- Broader claim evaluation begins as editor-assisted retrieval: supported, contradicted, mixed, insufficient evidence, out of scope.
- Confidence is a calibrated system property where measured, not an LLM's self-reported percentage.
- Evidence library supports season/date/article/document type and canonical entity filters.
- Acceptance: citations actually support the claim; unavailable source does not become “false”; corrected/deprecated source invalidates derived output.

### P10 — Legends

- Formats: five-minute race story, rivalry timeline, engineering turning point, comeback dossier, “what changed after this?” feature.
- Story structure: context, stakes, turning points, outcome, long-term consequences, sources and disputed interpretations.
- Candidate editorial subjects for later verification: 1976 title fight, 1989/1990 Suzuka controversies, 2008 Brazil finish, 2011 Canada comeback, 2012 season, 2020 Sakhir, 2021 Abu Dhabi, and major technical rule eras. This list is an editorial queue, not completed fact-checking or clip clearance.
- Keep contentious histories multi-perspective and document-based; do not use suffering/injuries as engagement bait.
- Acceptance: original writing, image/clip permissions recorded, chapter navigation, last-reviewed date, no fabricated quotations.

### P11 — My Paddock, search and learning

- Device-local follows/bookmarks/depth/spoiler preferences first; export/import for portability.
- Search across published titles, concepts, drivers, teams, races, incidents and article references.
- Learning paths: tyres and stints; race control; overtaking; car development; reading telemetry. Optional quizzes explain answers without streak loss or penalties.
- Empty state teaches how to save one useful moment rather than pushing account creation.
- Later account sync is additive and requires a privacy/security design; not a prerequisite to reading.

## 6. Portfolio priorities

| Posture | Modules | Investment rule |
|---|---|---|
| Invest first | Race Centre, Moments/Catch Me Up, evidence, editorial UI, sharing | Deliver the central value loop |
| Maintain and connect | Existing telemetry, replay, numerical ClaimCheck, FIA archive | Preserve useful behavior and improve provenance |
| Curate before automate | News, Legends, upgrades, incident explanations | Validate editorial demand and effort |
| Research separately | Strategy simulation, contextual scouting, text ClaimCheck | Promote only after evaluation |
| Defer | Licensed live timing, accounts, push infrastructure, comments, creator marketplace | Requires demand, budget or staffing |

Prioritization uses impact/confidence/effort qualitatively until actual reach data exists. Do not fabricate RICE numbers or market-share scores to make preferences look scientific.

## 7. Explicit non-goals

No broadcast rehosting, unofficial affiliation claims, gambling, outrage ranking, mandatory contact uploads, fake urgency, infinite-content generation, automated accusations, arbitrary model confidence meters or paid services enabled by default. No iOS/watch app, trackside travel portal, ticket marketplace or open social network in the first release.

## 8. Product validation protocol

Recruit 12–20 consenting fans across beginner/analyst levels, primarily through existing contacts or communities that permit research. Do not present this as a representative market sample.

Five tasks: find when the next session starts; explain a pit decision; identify official versus inferred incident reasoning; find supporting evidence; share a moment without spoiling the result.

Record task success, misunderstandings, time to first useful explanation, evidence use and willingness to revisit. Ask what they currently use and what the prototype replaces. Follow up across two race weekends, plus an off-week.

Initial decision gate: most tested users can explain the chosen moment accurately; no repeated confusion between official and model judgments; at least five independently return and several use a second connected feature. These are practical pilot gates, not statistical proof of PMF. If weak, improve the core journey before expanding modules.
