## ADDED Requirements

### Requirement: Section placement and chart type for the 10Y Treasury series

`series/dgs10.json` SHALL carry a `presentation` block placing the series in the
`rates` and `economy` sections with `order` 5, chart type `timeseries` (percent axis,
presets 1M / 6M / 1Y / 5Y / All, no recession shading by default), stats on, and a
`recent` table of 30 rows, and SHALL set `"fetcher": "fetch_treasury.py"`.

#### Scenario: Treasury appears in two sections

- **WHEN** the site is generated
- **THEN** `/charts/dgs10/` exists, the 10Y Treasury card is on `/rates/` and
  `/economy/`, and both section nav rows list "10Y Treasury"

## MODIFIED Requirements

### Requirement: 10-Year Treasury chart and table

The site SHALL present DGS10 on its own page (`/charts/dgs10/`) and on any grid that
lists it as a time-series line chart of yield (percent) over time drawn by the
`timeseries` chart type from its `presentation` block, plus a "Recent Observations"
table of the latest values.

#### Scenario: Treasury page renders

- **WHEN** the user opens `/charts/dgs10/`
- **THEN** the card loads `/data/dgs10.json`, draws a Plotly line chart of yield over
  time, and populates the recent-observations table from the same data

## REMOVED Requirements

### Requirement: Tab label for the 10Y Treasury series
**Reason**: There are no tabs; placement is a descriptor `presentation` value.
**Migration**: "Section placement and chart type for the 10Y Treasury series" above.
