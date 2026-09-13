## MODIFIED Requirements

### Requirement: Yield curve snapshot chart and controls

The dashboard SHALL render the curve for a selected date as a line across tenors on a
categorical, evenly spaced x-axis (Bloomberg-style), with toggleable historical overlays
(e.g. 1 week / 1 month / 1 year / 5 years ago), a custom date picker, and a current-yields
table showing yields and period changes. Overlay and change-column dates SHALL be
resolved by the `chart-chrome` comparison rule (anchored on the latest curve date,
nearest observation on or before the target) and the table SHALL show each resolved
comparison date.

#### Scenario: Yield curve tab renders

- **WHEN** the user opens the "Yield Curve" tab
- **THEN** the page loads `data/yield_curve.json`, plots the curve across the 11 tenors on
  a categorical x-axis, and populates the current-yields table

#### Scenario: Overlay a prior date

- **WHEN** the user enables a historical overlay or picks a custom date
- **THEN** an additional curve for that date is drawn over the current curve for comparison

#### Scenario: Resolved dates in the table

- **WHEN** the 1-month comparison target falls on a day with no observation
- **THEN** the table's change column is labelled with the actual date used
