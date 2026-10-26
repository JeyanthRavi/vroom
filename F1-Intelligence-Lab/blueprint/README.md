# Paddock Atlas — complete product blueprint

Version 2 · 26 October 2026 · Planning only

**Later scope update:** [implementation status and the two-product split](IMPLEMENTATION-STATUS.md). The user now wants Analysis Lab and News & Stories as separate products; the first local Race Lab slice has been built. The specifications below remain a roadmap, not a list of implemented features.

**Promise:** understand the race, not just the result.

This blueprint supersedes the earlier master plan where they differ. The earlier document is preserved. The name is provisional: no trademark, domain or app-store clearance has been performed. No new product features, accounts, deployments, paid services or marketing campaigns were launched while writing this plan.

## Confirmed constraints

- Serve newcomers and technical fans, with beginner-first onboarding and optional analyst depth.
- Spend approximately ₹0 at the start. Do not require paid AI, live feeds, databases, a domain or advertising.
- Plan one connected website and a native Android companion with widgets.
- Cover news, replacements, upgrades, overtaking/rules, pit strategy, historical stories and authorized clip links.
- Reuse existing local projects; do not claim their narrow demos are production-scale systems.

## Read in this order

1. [Product strategy and detailed requirements](01-PRODUCT.md) — positioning, competition, signature experiences, module PRDs, priorities and scope.
2. [UX, visual system, Android and widgets](02-EXPERIENCE.md) — screen inventory, journeys, wireframes, state behavior and accessibility gates.
3. [Engineering, data and AI](03-ENGINEERING.md) — ₹0 architecture, domain model, API/snapshot contracts, editorial pipeline, research evaluations and security.
4. [Growth, retention and business](04-GROWTH.md) — activation, ethical return loops, distribution, experiments, measurement and monetization gates.
5. [Execution, backlog and release](05-DELIVERY.md) — dependencies, work packages, acceptance criteria, test matrix, schedules, risks and runbooks.
6. [Sources, assumptions and skill decisions](06-EVIDENCE-AND-DECISIONS.md) — dated source register, unresolved choices and how the skills changed the plan.

## Executive decisions

| Decision | Choice | Why |
|---|---|---|
| Launch wedge | A spoiler-safe, evidence-linked race dossier | Useful without live infrastructure or exhaustive news coverage |
| First audience | Curious fans; analyst mode available | One simple entry point without alienating knowledgeable fans |
| Signature interaction | Explain → inspect evidence → explore alternative | Gives existing tools a purpose inside an actual fan journey |
| Initial distribution | Shareable web pages first | No download or signup required to experience value |
| Initial hosting | Static export on an eligible free host | Removes always-on server and database costs |
| Analysis execution | Local Python; publish approved results | Existing machine does the compute; readers receive cached output |
| Android | Native Kotlin/Compose + Glance after web validation | Widgets/offline behavior justify a native client |
| Account strategy | None initially; preferences stay on device | Lower friction, cost and privacy burden |
| AI | Optional editorial assistant, never runtime dependency | A useful product still works with no model subscription |
| Social/community | Sharing first; comments much later | Avoid an unstaffed moderation system |
| Live coverage | Explicitly deferred | Requires rights, reliable data, staffing and potentially money |
| Monetization | No paywall in pilot | Measure value before pricing; commercial rights first |

## Definition of a great first release

A newcomer opens a shared race moment, understands it in under three minutes, can inspect exactly what supports it, and can save or share it without registering. An experienced fan reaches the original evidence and assumptions without digging through simplified text. The website stays usable when the creator's laptop is off. The Android app presents the same content and useful cached widgets. Nothing implies a live service that does not exist.

## What would invalidate this plan

1. Fans do not find the explanation substantially more useful than their existing sources.
2. Publication rights cannot be established for the proposed data/content.
3. Editorial review takes more time than the creator can sustain.
4. The ₹0 stack requires hidden paid usage or becomes unreliable at observed load.
5. Simulations produce authoritative-looking conclusions without credible validation.

Respond by reducing scope or changing the approach, not by increasing notifications or inventing confident content.

## Effort interpretation

All effort figures are planning hypotheses, not estimates derived from a completed engineering breakdown. A focused engineering week means approximately 30 productive hours. At 10 hours/week, multiply engineering-week counts by about three for calendar planning, then allow for exams, learning, editorial work and approvals. The first compelling web slice is much smaller than the eventual ecosystem. There is no guaranteed viral outcome or fixed launch date.

## Immediate next milestone

One reviewed race dossier, two depth modes, ten linked moments, one incident deep dive, one honest strategy case, one original historical story, and one share card format. If permissions for a real example are unresolved, use clearly labelled synthetic data privately and publish only original, rights-cleared editorial material.
