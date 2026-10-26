# 02 — UX, visual design, Android and widgets

This is a design specification, not a completed design audit. Proposed tokens and thresholds require rendered testing before they become approved defaults.

## 1. Experience principles

1. Explain the value before asking for setup, an account, permission or money.
2. Keep race context visible: event, session, time, data status and current depth.
3. Show conclusions with their evidence and limitations, not buried footnotes.
4. Reduce navigation choices without removing expert depth.
5. A short successful visit is success; do not optimize for wasted time.
6. Respect platform conventions: native Android navigation/widgets, accessible web links and browser history.
7. Do not suggest a result is live, official or complete unless it is.

## 2. Information architecture

```text
Today
├── Catch Me Up
├── News / Updates
└── Followed teams and drivers
Race Centre
├── Calendar → Event → Session
├── Moments / Strategy / Incidents / Upgrades
└── Data / Sources
Explore
├── Telemetry / Replay / ScoutGrid
├── Rules / ClaimCheck / Evidence
└── Learn
Stories
└── Legends / Rivalries / Innovations / Collections
My Paddock
├── Saved / Following / Reading progress
└── Preferences / Offline / Privacy
```

Web desktop: five labelled primary links, search, spoiler control, theme control. Android: Today, Race, Explore, Saved bottom destinations; Stories is prominent in Explore and Today. Keep these four Android items stable between race and off-week states.

Planned canonical routes: `/`, `/news/`, `/news/{slug}/`, `/races/{season}/{event}/`, `/moments/{id}/`, `/incidents/{id}/`, `/strategy/{id}/`, `/upgrades/`, `/teams/{id}/`, `/drivers/{id}/`, `/stories/{slug}/`, `/learn/{slug}/`, `/explore/`, `/saved/`, `/sources/{id}/`, `/methodology/`, `/corrections/`, `/privacy/`, `/about/`.

Retain or redirect existing `/telemetry/`, `/stewardlens/`, `/pitwall/`, `/scoutgrid/`, `/claimcheck/`, `/archive/`. Redirects preserve shared URLs. Every indexable public route has meaningful static HTML; unsupported jobs never resolve to a blank shell.

## 3. First-run experience

### Website from a shared link

1. Open the requested moment directly, with neutral preview metadata.
2. Default to a spoiler-safe reveal gate if the URL contains results and the user's preference is unknown.
3. Show a concise explanation and one clear next action: “See why” or “Inspect evidence.”
4. Offer depth switching inline, not in a modal tutorial.
5. After useful interaction, offer “Follow this team” or “Save this moment.” No account required.
6. Offer the Android app only as optional widget/offline value, not a full-screen gate.

### Android first launch

1. One-sentence promise and a real published example; do not ask for notification permission immediately.
2. Optional picks: beginner/analyst depth, followed teams/drivers, spoilers hidden/shown. Skip is equally visible.
3. Land on a prepared brief, not an empty personalized feed.
4. After viewing value, offer a preview of the next-session widget.
5. Ask notification permission only if the user chooses a concrete reminder. A denial does not trigger nagging.

Design goal: a meaningful explanation within three minutes; a visible first action within 30 seconds. These are usability targets to test, not measured performance.

## 4. Representative layouts

### Desktop Today

```text
Brand     Today  Race Centre  Explore  Stories  My Paddock   Search
─────────────────────────────────────────────────────────────────
NEXT SESSION · time zone · schedule status       [Spoilers hidden]
─────────────────────────────────────────────────────────────────
WHAT CHANGED?                         YOUR PADDOCK
Lead reviewed moment                 Followed-team updates
[Read 60-second brief]                Next-session schedule
Source · published time               Data freshness
─────────────────────────────────────────────────────────────────
3 turning points                     One strategy question
─────────────────────────────────────────────────────────────────
Latest verified updates              Story of the week
─────────────────────────────────────────────────────────────────
You're caught up · Explore a race / Close
```

### Incident detail

```text
Event / Session / Lap / Turn                 [Beginner | Analyst]
WHAT HAPPENED?
Short neutral summary
[Authorized clip link] [Original explanatory diagram]

OFFICIAL OUTCOME       | OUR EXPLANATION
Decision and document | Evidence-based interpretation
Status + revision     | What remains uncertain

APPLICABLE RULE → article + season + issue + page
EVIDENCE DRAWER → specific statements and sources
RELATED → race consequence / comparable case / terminology
```

### Android Today

```text
Paddock Atlas                Search  Spoilers
Next session · local start time
Catch Me Up             [1 min / 3 min / Deep]
One lead moment, not a carousel of ten promotions
What changed for your team
One strategy explainer
One story
Today       Race       Explore       Saved
```

## 5. Screen-by-screen interaction contract

| Screen | Primary action | Supporting content | Required failure/empty behavior |
|---|---|---|---|
| Today | Open brief | Next session, followed entities, bounded updates | Last published time; do not fill gaps with generated news |
| Brief | Next reviewed moment | Progress, depth, sources | Incomplete coverage message and an end state |
| News list | Filter/open story | Status, source, timestamp | No matches plus clear filters; never change filters silently |
| News detail | Understand change | Evidence, related event, corrections | Unavailable source notice; withdrawn content explanation |
| Calendar | Open event | Timezone, session status | Postponed/cancelled/TBC states, stale schedule warning |
| Race overview | Explore key moments | Sessions, scope, coverage | Archived/read-only state when analysis absent |
| Moment | Explain/inspect | Clip link, rule/strategy context | Evidence missing is explicit |
| Strategy | Compare a scenario | Stints, assumptions, model version | Unsupported inputs blocked with reason; calculations cancellable |
| Incident | Read official decision | Separate analysis and rule references | Pending/unknown does not show invented verdict |
| Upgrade | Inspect change | Intent, fitment, sources, confounders | Effect unknown; no stock “performance gain” number |
| Telemetry | Compare laps | Coverage and units | Empty/incompatible lap selection recovery |
| Replay | Play/seek | Clock, timeline, data panels | Gap indicator; reset and pause always available |
| ScoutGrid | Compare measured metrics | Sample size, filters | No global ranking when only subset available |
| ClaimCheck | Check supported claim type | Observed value and source | Out-of-scope/refusal/insufficient-evidence states |
| Story | Read chapter | Timeline, sources, related clips | Missing clip does not prevent reading |
| Team/driver | Follow/explore | Season membership, updates | Historical membership differs from current affiliation |
| Learn | Understand concept | Original diagram and example | Unknown term can be reported; no invented definition |
| Search | Open result | Type, context, evidence status | Suggestions; spelling correction clearly indicated |
| Saved | Resume item | Local storage status, export | “Save a moment to find it here”; browse example |
| Settings | Change preference | Clear scope, reset/export | Failed sync retains old state and explains it |
| Editor inbox | Review next draft | Rights, evidence, duplicate group | Parser failures quarantined, never auto-published |
| Corrections | Read changed claim | Prior/current version and reason | Removed item remains referenced without forbidden material |

## 6. Spoiler policy as a system feature

Preference modes: show all; hide results until explicitly revealed; event-specific reveal. Store event reveal state locally. Never infer “watched the race” from elapsed time or opening a page.

Spoiler-bearing fields include winner names, finishing positions, standings deltas, incident outcomes, victory photos, thumbnails, alt text, captions, chart labels, push text, widget content, search snippets and social preview images.

Public share previews default to neutral event/moment titles. A specific shared route opens a reveal gate for unknown recipients. An explicitly spoiler-bearing card can be shared only after previewing it. Do not rely on client-side CSS hiding for search engines or link-preview scrapers: static public metadata itself must be safe.

Android notifications use safe wording by default; a preference change does not erase already-delivered system notifications. Explain this limitation. The ₹0 version avoids push, reducing this risk.

QA: create a seeded forbidden-word/field fixture and inspect HTML metadata, accessibility text, widget snapshots, notifications and share previews. Test per-event reveal independently from global preference.

## 7. Visual system

### Proposed tokens

| Token | Initial proposal | Usage |
|---|---|---|
| Canvas dark | `#0B0D10` | Main background |
| Surface dark | `#151A21` | Panels |
| Elevated dark | `#1E2630` | Menus and highlighted surfaces |
| Text primary | `#F5F7FA` | Body/headings |
| Text secondary | `#B8C2CF` | Metadata, still readable |
| Accent | `#FF5A52` | Actions and selected states; pairings must be checked |
| Focus | `#7CC8FF` | High-visibility keyboard focus |
| Border | `#344150` | Delimiters, not sole state indicator |
| Light canvas | `#F6F7F9` | Light mode |
| Light text | `#17212D` | Light mode body |

These are proposals, not contrast-certified colours. Check each real foreground/background pair and active/disabled state. Prefer dark text on a light red action surface if it tests better than white. Use semantic severity tokens separately from team colours.

Typography: licensed open-source condensed display face for short headings, highly readable sans-serif body face and optional mono face for timing. Verify font files/licences before bundling. No official F1 font. Body 16–18 CSS px with comfortable line height; article width about 65–75 characters; avoid uppercase paragraphs.

Spacing scale: 4/8/12/16/24/32/48/64. Cards mostly 8–12 px radius, not a wall of giant pills. Use restrained borders and depth, not heavy glass effects. Motion 120–200 ms for small state changes, reduced-motion alternative; no compulsory racing intro, sound or autoplay.

Breakpoints to test: 360/390/768/1024/1440 CSS px, plus 200% text sizing and narrow landscape. Use flexible content widths, not device-name assumptions. Desktop charts may be dense; mobile defaults to one selected metric and a full-width details sheet.

## 8. Component contracts

- `SourceBadge`: source class plus accessible text; opens evidence, not just a decorative tooltip.
- `EvidenceDrawer`: claim, source revision, relevant excerpt where permitted, page/section, external link and limitations.
- `FreshnessLabel`: source observation time versus publication time; stale styling plus plain text.
- `MomentCard`: event/time, neutral title, short explanation, content kind, status, depth link and safe share action.
- `SessionStrip`: local start time, timezone, status, countdown without fake precision.
- `StintChart`: compound/age, start/end laps, pit markers, tabular alternative and unknown segments.
- `DecisionPanel`: official outcome visually distinct from interpretation and simulation.
- `ClipCard`: uploader/source, outbound destination, optional timestamp, availability, rights state internally; no misleading play overlay if only an outbound link exists.
- `ScenarioControls`: valid inputs, reset, assumptions, result version and disabled reasons.
- `CorrectionNotice`: changed claim, date, editor rationale and effect on downstream analyses.

Each component requires loading, populated, empty, partial, stale, error, focus and disabled states where applicable. Create component examples with long names, missing images, mixed units and many sources before building entire pages.

## 9. Accessibility and performance gates

Target WCAG 2.2 AA on web; test rather than claim conformance from colours alone. Include semantic headings, visible focus, skip links, keyboard charts, label-associated inputs, status announcements, text resizing and alternatives for images/charts. Use 44 CSS px as a comfortable web interaction design target and 48 dp Android touch targets where practical; these are product choices, not claims that WCAG requires exactly those sizes. [WCAG 2.2](https://www.w3.org/TR/wcag/).

No chart depends only on red/green or team colour. Use labels, line styles and patterns. Respect reduced motion and system font scaling. Run VoiceOver/TalkBack and keyboard task tests before release. Captions/transcripts require rights/availability checks; don't silently manufacture transcripts of inaccessible footage.

Proposed engineering budgets, to validate on representative devices: reading-route compressed initial JS under 180 KB; avoid loading chart packages until needed; user-visible interactions respond immediately; define LCP/INP/CLS field targets during implementation; no background replay loop when hidden. Media is lazy-loaded, dimensions reserved and external embeds load only after intent/appropriate consent.

## 10. Native Android architecture and UX

Kotlin + Compose app, Room local content cache, DataStore preferences, WorkManager best-effort sync, Glance widgets. An installable website is a useful early distribution surface but not a substitute for native widget behavior. Sharing content/contracts does not mean Compose and React share UI code.

Use a repository interface that reads a bundled starter dataset or validated static HTTPS snapshots in the first version. Add a live API adapter later without changing screen state models. Offline work does not require a public database.

Screen states use immutable models. Navigation preserves event, depth, scroll and spoiler context. External clip links open the authorized provider or browser; do not create a disguised video downloader. Support back behavior and process recreation.

Minimum Android version is a decision to validate against tester devices and library support, not hardcoded in this plan. Test at least one low/mid-range physical device and a current emulator; emulator success alone is insufficient.

## 11. Widget specifications

Grid sizes below are design intents: launcher cell sizes vary. Implement responsive size modes rather than assuming universal pixel dimensions.

| Widget | Approximate size | Data | Tap | Refresh |
|---|---|---|---|---|
| Next session | 2×1 / 2×2 | Event, session, local time, countdown | Event schedule | Cached schedule plus app/manual/best-effort sync |
| Weekend agenda | 4×2 | Remaining sessions and status | Race hub | Same shared schedule refresh |
| Paddock brief | 4×2 | Three approved neutral headlines | Specific article | Snapshot sync, freshness visible |
| Favourite team | 2×2 / 4×2 | Selected team, latest reviewed update | Team profile | Independent per-widget configuration |
| Standings | 4×2 | Last verified standings where permitted | Standings detail | Spoilers hidden by default |
| Race status, later | 4×2 | Coarse licensed status, last observation | In-app race view | Best effort; never promised live-per-second |

Widget configuration: select type/entity, theme, density, spoiler mode inherited or stricter, and save. Preview before pin request. User can remove widgets normally. Multiple widgets have independent instance IDs and settings.

Rendering reads persisted cache, not a network request per card. Display last successful data refresh; distinguish checking from data arrival. If source is stale, do not replace it with an empty widget. If event postponed, display that state instead of a misleading countdown. In no-data state, provide “Open app to load schedule.”

Android documentation describes periodic widget refresh via `updatePeriodMillis` up to every 30 minutes and WorkManager for more frequent schedules such as 15 minutes; neither is a promise of exact delivery. Avoid minute-by-minute background refresh. Use a static local start time or platform-supported countdown presentation, with graceful fallback. [Widget update guidance](https://developer.android.com/develop/ui/compose/glance/glance-app-widget).

Test process death, reboot, timezone/date change, Doze, no connectivity, resizing, removing/re-adding, denied permissions, expired snapshots, app upgrade and two widgets with different teams. Widgets must not crash when their referenced article was corrected or removed.

## 12. Notifications and installation

₹0 launch: no server push. Optional local schedule reminders are best-effort and explain timing limits; don't request special exact-alarm privileges just for marketing. RSS and visiting the site are valid update channels.

Later categories: session reminders, chosen-team confirmed updates, post-race brief and corrections. All opt-in; no results in default notification previews. Marketing category off by default. Per-user quiet hours in their timezone.

Start Android testing on the developer's own device/emulator. Signed APK distribution to consenting testers is a separate release step; don't promise unrestricted worldwide sideloading. Android developer verification requirements are evolving and regional, so verify eligibility before external distribution. ADB development testing remains supported. [Android verification FAQ](https://developer.android.com/developer-verification/guides/faq).

Before Play release: verify account-specific testing, current target API, privacy/Data Safety disclosures, content rating, signing and identity requirements. Play registration is not ₹0; budget separately. See source register and delivery gates.

## 13. Design review protocol

Passes: inventory → page hierarchy → component/state consistency → complete journeys → accessibility → performance → distinctive visual polish. Record findings as observation, user impact, severity, recommended fix and evidence.

Do not assign an A/B grade before inspecting rendered screens. The release gate is successful tasks and no critical barriers, not a decorative score. Compare before/after on identical viewport/data fixtures. Review screenshots at mobile and desktop alongside actual keyboard/TalkBack use.
