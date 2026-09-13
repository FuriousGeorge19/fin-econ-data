# nber-recession-data Specification

## Purpose

The shared NBER recession dataset: `scripts/fetch_usrec.py` fetches the monthly USREC
indicator from FRED and collapses it into recession intervals written to
`data/usrec.json`, a chart-agnostic dataset reused for recession shading across multiple
dashboard charts.
## Requirements
### Requirement: Fetch USREC recession indicator

`scripts/fetch_usrec.py` SHALL fetch the USREC NBER-based recession indicator from FRED
via the shared `fred_utils` module and write `data/usrec.json`. USREC is a monthly 0/1
series; the fetcher SHALL collapse contiguous runs of 1 into recession intervals rather
than emitting every monthly point.

#### Scenario: USREC fetched and collapsed to intervals

- **WHEN** `fetch_usrec.py` runs with a valid `FRED_API_KEY`
- **THEN** `data/usrec.json` is written as a list of recession intervals, each with a
  `start` and `end` date, derived by collapsing consecutive recession months

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

### Requirement: Ongoing recession is open-ended

The final interval SHALL have an open-ended end (e.g. `end: null`) when the most recent
USREC observation indicates an active recession, so consumers can shade through to the
latest available date rather than guessing an end.

#### Scenario: Active recession at latest observation

- **WHEN** the latest USREC value is 1 (in recession)
- **THEN** the final interval in `data/usrec.json` has `end: null` (or an equivalent
  open-ended marker)

