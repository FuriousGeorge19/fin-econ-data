## ADDED Requirements

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

### Requirement: Daily refresh produces Shiller-only P/E in CI

The daily GitHub Actions workflow SHALL run `scripts/fetch_sp500_pe.py` and
publish `data/sp500_pe.json`. As of this baseline, the workflow step does not
pass `FRED_API_KEY` to the script's env, so the FRED-based price extension and
forward-fill paths are inactive in CI — only Shiller's confirmed history is
republished on each run.

**Known gap:** Unlike the Treasury and yield-curve workflow steps (which do
pass `FRED_API_KEY`), the P/E step does not. The post-Shiller price extension
is therefore inactive in CI until the key is wired in. The next change
(`fix-fred-key-on-pe-step`) is planned to close this gap.

#### Scenario: P/E refresh in CI

- **WHEN** the daily workflow runs the S&P 500 P/E step
- **THEN** the script runs to completion, the FRED price fetch warns to stderr
  and returns no prices, and the published `sp500_pe.json` contains observations
  through Shiller's last confirmed month with no post-Shiller extension from
  that run

### Requirement: Tab label for the S&P 500 P/E series

The S&P 500 P/E series SHALL appear in the dashboard under a tab labeled
"S&P 500 P/E".

#### Scenario: P/E tab appears in nav

- **WHEN** the dashboard renders its tab navigation
- **THEN** one of the tabs is labeled "S&P 500 P/E", and selecting it shows the
  P/E chart with the confirmed-vs-estimated distinction visible

