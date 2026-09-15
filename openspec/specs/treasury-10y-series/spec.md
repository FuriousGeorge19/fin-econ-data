# treasury-10y-series Specification

## Purpose

The 10-Year Treasury Constant Maturity Rate (DGS10) series: the FRED fetcher that
produces `data/dgs10.json` and the dashboard's "10Y Treasury" tab with its yield
time-series chart and recent-observations table.
## Requirements
### Requirement: Fetch 10-Year Treasury rate

`scripts/fetch_treasury.py` SHALL fetch the DGS10 series (10-Year Treasury Constant
Maturity Rate) from FRED, requesting the most recent ~2520 daily observations
(approximately 10 years of trading days), and write `data/dgs10.json` under the
`series-metadata` header contract.

#### Scenario: Successful fetch

- **WHEN** `fetch_treasury.py` runs with a valid `FRED_API_KEY`
- **THEN** `data/dgs10.json` is written with `meta` from `series/dgs10.json` (input
  `series_id` `DGS10`, units `Percent`, cadence `daily`, source FRED), `as_of` with the
  last observation and `due_by`, and observations sorted oldest-first, each having a
  `date` and a numeric `value`

#### Scenario: Missing values dropped

- **WHEN** the DGS10 response contains `"."` entries (holidays/gaps)
- **THEN** those entries are excluded and only numeric observations appear in the output

### Requirement: 10-Year Treasury chart and table

The site SHALL present DGS10 on its own page (`/charts/dgs10/`) and on any grid that
lists it as a time-series line chart of yield (percent) over time drawn by the
`timeseries` chart type from its `presentation` block, plus a "Recent Observations"
table of the latest values.

#### Scenario: Treasury page renders

- **WHEN** the user opens `/charts/dgs10/`
- **THEN** the card loads `/data/dgs10.json`, draws a Plotly line chart of yield over
  time, and populates the recent-observations table from the same data

### Requirement: Section placement and chart type for the 10Y Treasury series

`series/dgs10.json` SHALL carry a `presentation` block placing the series in the
`rates` and `economy` sections with `order` 5, chart type `timeseries` (percent axis,
presets 1M / 6M / 1Y / 5Y / All, no recession shading by default), stats on, and a
`recent` table of 30 rows, and SHALL set `"fetcher": "fetch_treasury.py"`.

#### Scenario: Treasury appears in two sections

- **WHEN** the site is generated
- **THEN** `/charts/dgs10/` exists, the 10Y Treasury card is on `/rates/` and
  `/economy/`, and both section nav rows list "10Y Treasury"

