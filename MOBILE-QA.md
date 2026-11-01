# Static demo accessibility and mobile QA

Automated axe/Playwright tooling is not installed in the release environment,
so this is the documented manual gate. Source-level assertions cover the key
landmarks and fallbacks; a browser assistive-technology pass remains an owner
task before public publication.

## Checked in this release

- Semantic headings and labelled controls are present.
- Status changes use `role="status"`.
- Both charts have accessible names and adjacent text alternatives.
- Keyboard focus is visible on selects, links, and disclosure controls.
- Text/background and control-border colours were selected for at least 4.5:1
  contrast in the dark theme; re-check with a browser contrast tool if colours
  change.
- The responsive breakpoint removes outer padding and tightens tables at 420 px;
  the grid collapses naturally to one column at 360 px.
- `prefers-reduced-motion` disables animation, transition, and smooth scrolling.
- Heavy research data is fetched separately after the HTML and contains only
  aggregate fixture results.

## Owner browser pass before publication

1. At 360 × 800, tab from the address bar through every control and link.
2. At 200% zoom, confirm no controls overlap and tables remain horizontally scrollable.
3. With VoiceOver/NVDA, verify the status, race selector, tables, chart names,
   text alternatives, methodology link, and footer build label are announced.
4. Enable reduced motion and confirm there is no animated transition.
5. Run axe or Lighthouse and record any exception with a screenshot and reason.
