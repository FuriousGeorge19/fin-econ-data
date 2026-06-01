# sp500-pe-series Specification

## Purpose

The S&P 500 trailing-twelve-month as-reported P/E series, built by stitching three
sources in time order (Shiller history, manually maintained S&P Global earnings
overrides, and FRED prices), with confirmed-vs-estimated marking, plus the dashboard's
"S&P 500 P/E" tab.

## Requirements

### Requirement: Trailing P/E from three stitched sources

`scripts/fetch_sp500_pe.py` SHALL build a monthly S&P 500 trailing-twelve-month
as-reported (GAAP) P/E series by stitching three sources in time order:
1. **Historical** — Robert Shiller / Yale `ie_data.xls`: confirmed monthly price `P`
   and TTM earnings `E`, kept only where `E` is present and positive.
2. **Recent** — months after the last confirmed Shiller month: FRED `SP500` monthly
   average prices combined with TTM earnings from `data/earnings_overrides.json`.
3. **Current** — months past the last confirmed quarter in the overrides: FRED prices
   with forward-filled TTM earnings from the most recent confirmed quarter.

P/E for each month SHALL be `price / ttm_eps`, and the output `data/sp500_pe.json` SHALL
carry `title`, `units` `Ratio`, frequency `Monthly`, a `methodology` description, and
`last_ttm_earnings` (the last confirmed TTM EPS).

#### Scenario: Full series assembled

- **WHEN** `fetch_sp500_pe.py` runs with Shiller reachable and overrides present
- **THEN** observations span 1871 to the current month, each with `date` (`YYYY-MM-01`),
  `price`, `earnings`, `pe`, and an `estimated` flag

### Requirement: Confirmed vs estimated marking

Each observation SHALL carry an `estimated` boolean. Months backed by confirmed Shiller
earnings or by a non-latest confirmed quarterly override SHALL be `estimated=false`.
Months whose earnings are forward-filled from the latest available quarter (the quarter
not yet superseded) SHALL be `estimated=true`.

#### Scenario: Forward-filled month flagged estimated

- **WHEN** a month falls after the most recent confirmed quarter in `earnings_overrides.json`
- **THEN** its TTM earnings are forward-filled from that quarter and the observation is `estimated=true`

#### Scenario: Estimated periods shown distinctly

- **WHEN** the S&P 500 P/E chart renders
- **THEN** estimated observations are drawn distinctly (dashed line) from the confirmed history

### Requirement: Manually maintained earnings overrides

`data/earnings_overrides.json` SHALL hold quarterly as-reported and TTM EPS sourced from
the S&P Global quarterly scorecard, and is maintained manually (~4x/year). When the file
is absent the fetcher SHALL warn and continue with Shiller-only data rather than fail.

#### Scenario: Overrides missing

- **WHEN** `fetch_sp500_pe.py` runs and `data/earnings_overrides.json` does not exist
- **THEN** the script prints a warning to stderr and produces output from Shiller history alone

### Requirement: Daily refresh produces full P/E in CI

The daily GitHub Actions workflow SHALL run `scripts/fetch_sp500_pe.py` with
`FRED_API_KEY` present in the step's environment so that the FRED-based price
extension runs in CI. The published `data/sp500_pe.json` SHALL therefore include
the post-Shiller monthly extension (FRED-priced months with overrides-based and
forward-filled TTM earnings), matching what a local run with the key produces.

#### Scenario: P/E refresh in CI with the key wired in

- **WHEN** the daily workflow runs the S&P 500 P/E step
- **THEN** the FRED SP500 price fetch succeeds and the published `sp500_pe.json`
  contains observations through the current month, including post-Shiller months
  marked `estimated=true` where earnings are forward-filled

#### Scenario: Secret absent falls back safely

- **WHEN** the S&P 500 P/E step runs but `FRED_API_KEY` is missing or invalid
- **THEN** the script warns to stderr, returns no FRED prices, and still completes
  with Shiller-only output rather than failing the build

### Requirement: Tab label for the S&P 500 P/E series

The S&P 500 P/E series SHALL appear in the dashboard under a tab labeled
"S&P 500 P/E".

#### Scenario: P/E tab appears in nav

- **WHEN** the dashboard renders its tab navigation
- **THEN** one of the tabs is labeled "S&P 500 P/E", and selecting it shows the
  P/E chart with the confirmed-vs-estimated distinction visible
