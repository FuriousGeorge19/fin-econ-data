## ADDED Requirements

### Requirement: Section placement and chart type for the yield curve series

`series/yield_curve.json` SHALL carry a `presentation` block placing the series in the
`rates` section with `order` 10 and chart type `curve` with overlays 1w / 1m / 1y / 5y,
a custom date, and `table: true`.

#### Scenario: Yield curve listed under Rates & Yields

- **WHEN** the site is generated
- **THEN** `/charts/yield_curve/` exists, the card is on `/rates/`, and the Rates &
  Yields nav row lists "Yield Curve"

## MODIFIED Requirements

### Requirement: Yield curve snapshot chart and controls

The site SHALL render the curve for a selected date as a line across tenors on a
categorical, evenly spaced x-axis (Bloomberg-style), with toggleable historical overlays
(1 week / 1 month / 1 year / 5 years ago), a custom date picker, and a current-yields
table showing yields and period changes, all drawn by the `curve` chart type with its
controls in the card's control row. Overlay and change-column dates SHALL be resolved
by the `chart-chrome` comparison rule (anchored on the latest curve date, nearest
observation on or before the target) and the table SHALL show each resolved comparison
date.

#### Scenario: Yield curve page renders

- **WHEN** the user opens `/charts/yield_curve/`
- **THEN** the card loads `/data/yield_curve.json`, plots the curve across the 11 tenors
  on a categorical x-axis, and populates the current-yields table

#### Scenario: Overlay a prior date

- **WHEN** the user enables a historical overlay or picks a custom date
- **THEN** an additional curve for that date is drawn over the current curve for comparison

#### Scenario: Resolved dates in the table

- **WHEN** the 1-month comparison target falls on a day with no observation
- **THEN** the table's change column is labelled with the actual date used

## REMOVED Requirements

### Requirement: Tab label for the yield curve series
**Reason**: There are no tabs; placement is a descriptor `presentation` value.
**Migration**: "Section placement and chart type for the yield curve series" above.
