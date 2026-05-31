# treasury-10y-series Specification

## Purpose

The 10-Year Treasury Constant Maturity Rate (DGS10) series: the FRED fetcher that
produces `data/dgs10.json` and the dashboard's "10Y Treasury" tab with its yield
time-series chart and recent-observations table.

## Requirements

### Requirement: Fetch 10-Year Treasury rate

`scripts/fetch_treasury.py` SHALL fetch the DGS10 series (10-Year Treasury Constant
Maturity Rate) from FRED, requesting the most recent ~2520 daily observations
(approximately 10 years of trading days), and write `data/dgs10.json`.

#### Scenario: Successful fetch

- **WHEN** `fetch_treasury.py` runs with a valid `FRED_API_KEY`
- **THEN** `data/dgs10.json` is written with `series_id` `DGS10`, units `Percent`,
  frequency `Daily`, source attributed to FRED, and observations sorted oldest-first,
  each having a `date` and a numeric `value`

#### Scenario: Missing values dropped

- **WHEN** the DGS10 response contains `"."` entries (holidays/gaps)
- **THEN** those entries are excluded and only numeric observations appear in the output

### Requirement: 10-Year Treasury chart and table

The dashboard SHALL present DGS10 on its own tab as a time-series line chart of yield
(percent) over time, plus a "Recent Observations" table of the latest values.

#### Scenario: Treasury tab renders

- **WHEN** the user opens the "10Y Treasury" tab
- **THEN** the page loads `data/dgs10.json`, draws a Plotly line chart of yield over
  time, and populates the recent-observations table from the same data

### Requirement: Tab label for the 10Y Treasury series

The DGS10 series SHALL appear in the dashboard under a tab labeled "10Y Treasury".

#### Scenario: Treasury tab appears in nav

- **WHEN** the dashboard renders its tab navigation
- **THEN** one of the tabs is labeled "10Y Treasury", and selecting it shows the
  DGS10 chart and table
