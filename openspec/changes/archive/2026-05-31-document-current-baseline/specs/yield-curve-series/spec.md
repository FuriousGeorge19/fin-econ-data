## ADDED Requirements

### Requirement: Fetch all Treasury tenors

`scripts/fetch_yield_curve.py` SHALL fetch all 11 standard Treasury constant-maturity
tenors from FRED — DGS1MO, DGS3MO, DGS6MO, DGS1, DGS2, DGS3, DGS5, DGS7, DGS10, DGS20,
DGS30 — each requesting ~6300 daily observations (~25 years), and write
`data/yield_curve.json`.

#### Scenario: All tenors fetched

- **WHEN** `fetch_yield_curve.py` runs with a valid `FRED_API_KEY`
- **THEN** the output includes a `tenors` list of the 11 labels (`1mo`…`30yr`) and a
  `tenor_months` map giving each tenor's maturity in months

### Requirement: Date-keyed observations across tenors

Observations SHALL be keyed by date, where each date maps to the subset of tenor yields
available that day. Dates with no tenor data at all SHALL be omitted. Tenors missing on
a given day (sentinel `"."`) SHALL simply be absent from that day's entry rather than
zero-filled.

#### Scenario: Partial day

- **WHEN** a date has yields for some but not all tenors
- **THEN** that date's entry contains only the tenors that reported, and absent tenors are not present

### Requirement: Yield curve snapshot chart and controls

The dashboard SHALL render the curve for a selected date as a line across tenors on a
categorical, evenly spaced x-axis (Bloomberg-style), with toggleable historical overlays
(e.g. 1 week / 1 month / 1 year / 5 years ago), a custom date picker, and a current-yields
table showing yields and period changes.

#### Scenario: Yield curve tab renders

- **WHEN** the user opens the "Yield Curve" tab
- **THEN** the page loads `data/yield_curve.json`, plots the curve across the 11 tenors on
  a categorical x-axis, and populates the current-yields table

#### Scenario: Overlay a prior date

- **WHEN** the user enables a historical overlay or picks a custom date
- **THEN** an additional curve for that date is drawn over the current curve for comparison

### Requirement: Tab label for the yield curve series

The Treasury yield curve series SHALL appear in the dashboard under a tab labeled
"Yield Curve".

#### Scenario: Yield curve tab appears in nav

- **WHEN** the dashboard renders its tab navigation
- **THEN** one of the tabs is labeled "Yield Curve", and selecting it shows the
  curve snapshot chart and current-yields table