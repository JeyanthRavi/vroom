# Data rights review — 28 October 2026

Status: **permission for this public redistribution is not established**.
This is a source review, not legal advice or a finding that the project violates law.

## Primary sources

- [OpenF1 website and FAQ](https://openf1.org/): describes educational, personal,
  research and non-commercial fan uses. It disclaims ownership of underlying data
  and directs other uses to its contact channel. This is not an explicit grant
  covering Vroom's public bulk timing export and trained models.
- [OpenF1 software licence](https://github.com/br-g/openf1/blob/main/LICENSE):
  software licensing must not be conflated with rights in upstream timing data.
- [Formula 1 rights guidelines](https://www.formula1.com/en/information/guidelines.4EOKE9RRqevL4niTK9kWyt):
  claim rights over timing/statistics; restrict substantial reproduction; distinguish
  private education from public postings; reserve AI/data-mining uses to express
  licensing. Their applicability and enforceability require qualified advice.

## Exposure and recommendation

The public JSON contains observed lap durations, race/session and driver identifiers,
derived race states and predictions for 36 races. This is not just aggregate metrics.
No broadcast media or FIA PDFs are included in this static release. The broader
local portal's FIA documents and any future clips need a separate rights review.

Recommend temporarily making the replay owner-private pending written clarification.
Do not assume that attribution, a non-commercial label, or removing a download button
resolves rights: the browser still retrieves the complete JSON. No visibility change
or external message was made during this review. No permission has been obtained.

## Unsent clarification request

Use OpenF1's official contact channel; Formula 1 lists brandprotection@f1.com
for rights questions. Ask which rights holder can authorize this specific use.

> I am building a non-commercial student research project, Vroom. It trains
> gradient-boosted and GRU next-lap regressors on historical OpenF1 timing and
> race-control data. A public static demo currently contains observed lap durations,
> identifiers and precomputed predictions for 36 races, with no live feed or media.
> Does your permission cover model training and public redistribution of these
> records and predictions? What attribution, limits or upstream permissions are
> required? If bulk records are not permitted, what aggregate evaluation display
> may be published? Please identify any separate rights-holder approval needed.

Do not send this draft without the user's authorization. Retain any response and
its exact scope before describing the data as licensed or cleared.
