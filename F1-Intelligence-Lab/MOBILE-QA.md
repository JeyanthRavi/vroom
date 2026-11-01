# Hosted replay mobile QA — 28 October 2026

Target: https://vroom-race-replay-jeyanth.quantum-banana.chatgpt.site

Tested in the in-app browser with viewport overrides, not physical Android/iOS devices.

- 390 × 844: race changed to 2026 Monte Carlo, GRU ensemble selected, Car 44 selected.
  UI updated to 36 eligible laps, 63.711 s driver MAE and 65.123 s baseline MAE.
- Evidence disclosure expanded successfully with 36 rows; chart had three traces.
- Page width remained 390 px: no document-level horizontal overflow.
- 360 × 800: page width remained 360 px. Tables are internally horizontally
  scrollable (278 px containers, 475/530 px content). Actual touch scrolling was
  not tested on hardware.
- Controls stack in one column, 308 px wide and 43.5 px high at 390 px viewport.
- Saved narrow-screen screenshot at `.local-data/ml-runs/public-mobile-360.png`.
- Restored the browser's normal viewport after the test.

## Non-blocking usability issues

- SVG axis text shrinks substantially on phones; exact values remain in the table.
- Wide tables need a visible swipe/scroll hint; right-hand columns are initially hidden.
- Select controls are slightly below a 44 px touch-height target.
- Large interruption laps compress ordinary lap variation; this is intentional
  honest scaling but needs a clearly labelled optional zoom view in a future UI pass.

No UI changes were deployed during this verification. No physical-device, offline,
slow-network, screen-reader or complete accessibility certification is claimed.
