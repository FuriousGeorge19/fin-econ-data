## MODIFIED Requirements

### Requirement: Shared, reusable recession dataset

`data/usrec.json` SHALL be a standalone dataset not coupled to any single chart, intended
for reuse across multiple dashboard charts. It SHALL follow the `series-metadata` header
contract: `meta` from `series/usrec.json` (with `kind: intervals`, `revisions:
retroactive`, and a note that it reflects only officially NBER-dated recessions, which
lag real time) and `as_of` whose `last_observation` is the last month USREC reported
(captured before the monthly series is collapsed to intervals) and whose
`latest_value` is that month's 0/1, so consumers can state "no recession declared
through Aug 2026".

#### Scenario: Dataset is chart-agnostic

- **WHEN** any chart needs recession shading
- **THEN** it can consume `data/usrec.json` directly without that file depending on the
  spreads series or any other specific chart

#### Scenario: Last observed month recorded

- **WHEN** `fetch_usrec.py` runs and FRED's latest USREC observation is `2026-08-01`
  with value 0
- **THEN** `as_of.last_observation` is `2026-08-01`, `as_of.period_label` is `Aug 2026`,
  `as_of.latest_value` is 0, and `recessions` is unchanged in shape
