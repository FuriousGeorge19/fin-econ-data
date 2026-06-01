## ADDED Requirements

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
for reuse across multiple dashboard charts. It SHALL carry the pipeline metadata
conventions (`title`, `source`, UTC `last_updated`) and clearly describe that it reflects
only officially NBER-dated recessions (which lag real time).

#### Scenario: Dataset is chart-agnostic

- **WHEN** any chart needs recession shading
- **THEN** it can consume `data/usrec.json` directly without that file depending on the
  spreads series or any other specific chart

### Requirement: Ongoing recession is open-ended

The final interval SHALL have an open-ended end (e.g. `end: null`) when the most recent
USREC observation indicates an active recession, so consumers can shade through to the
latest available date rather than guessing an end.

#### Scenario: Active recession at latest observation

- **WHEN** the latest USREC value is 1 (in recession)
- **THEN** the final interval in `data/usrec.json` has `end: null` (or an equivalent
  open-ended marker)
