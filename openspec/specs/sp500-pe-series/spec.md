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
3. **Current** — months whose preceding calendar quarter is not yet in the overrides:
   FRED prices with TTM earnings forward-filled from the last confirmed quarter.

Only completed months SHALL be emitted: a FRED month is included only when the fetch
date (US Eastern) is later than that month's last day, because FRED's monthly average of
a month in progress changes daily while Shiller's prices are full-month averages. P/E
for each month SHALL be `price / ttm_eps`. The output `data/sp500_pe.json` SHALL carry
`meta` from `series/sp500_pe.json` and `as_of` with `inputs.price` and
`inputs.earnings`; `as_of.inputs.earnings` SHALL carry `last_observation` (the last
confirmed quarter end), `confirmed_through` (the last confirmed month), and `value`
(the TTM EPS every estimated month reuses).

#### Scenario: Full series assembled

- **WHEN** `fetch_sp500_pe.py` runs with Shiller reachable and overrides present
- **THEN** observations span 1871 to the last completed month, each with `date`
  (`YYYY-MM-01`), `price`, `earnings`, `pe`, and an `estimated` flag

#### Scenario: Month in progress excluded

- **WHEN** the fetcher runs on 2026-09-25 (US Eastern)
- **THEN** the last observation is `2026-08-01`; the September point appears only from
  the first run dated 2026-10-01 or later

### Requirement: Confirmed vs estimated marking

Each observation SHALL carry an `estimated` boolean. A month `M` SHALL be
`estimated=false` when its earnings come from Shiller, or when
`data/earnings_overrides.json` contains the calendar quarter ending strictly before `M`
begins (the entry whose `effective_from` is `quarter_end + 1 month`, which applies to
`M` and the two following months). A month for which that quarter is not yet in the
file SHALL reuse the last entry's TTM EPS and be `estimated=true`. Equivalently,
`estimated` is true exactly when `M >= effective_from(last entry) + 3 months`.
`as_of.inputs.earnings.confirmed_through` SHALL equal the last `estimated=false` month.

#### Scenario: Months covered by the newest quarter are confirmed

- **WHEN** the overrides file ends with the quarter ending 2025-09-30 (`effective_from`
  `2025-10-01`, TTM 234.06)
- **THEN** Oct, Nov and Dec 2025 are `estimated=false` on 234.06, every month from
  Jan 2026 is `estimated=true` on 234.06, and `confirmed_through` is `2025-12-01`

#### Scenario: Estimated periods shown distinctly

- **WHEN** the S&P 500 P/E chart renders
- **THEN** estimated observations are drawn distinctly (dashed line) from the confirmed
  history, starting at the first estimated month

### Requirement: Manually maintained earnings overrides

`data/earnings_overrides.json` SHALL hold quarterly as-reported and TTM EPS regenerated
by `scripts/build_earnings_overrides.py` from the S&P Global workbook
`reference_resources/sp-500-eps-est.xlsx`. The builder SHALL read the workbook's own
as-of cells (`SECTOR EPS!B2` data as of, `B3` historical actuals through, `B4`
estimates from) into the file header as `data_as_of` and `actuals_through`, SHALL
include only quarters ending on or before `actuals_through`, and SHALL derive each
entry's calendar quarter from `effective_from` (the workbook's `quarter_end` values are
last trading days). The source workbook was discontinued by S&P on 2026-01-31; the
descriptor's earnings input SHALL carry `status: discontinued` until a replacement
source is adopted. When the file is absent the fetcher SHALL warn and continue with
Shiller-only data rather than fail.

#### Scenario: Overrides missing

- **WHEN** `fetch_sp500_pe.py` runs and `data/earnings_overrides.json` does not exist
- **THEN** the script prints a warning to stderr and produces output from Shiller
  history alone

#### Scenario: Preliminary quarter excluded

- **WHEN** the workbook's `actuals_through` is 2025-09-30 and its quarterly sheet also
  carries a figure for the quarter ending 2025-12-31
- **THEN** the regenerated file's last entry is the 2025-09-30 quarter

### Requirement: Daily refresh produces full P/E in CI

The daily GitHub Actions workflow SHALL run `scripts/fetch_sp500_pe.py` with
`FRED_API_KEY` present in the step's environment so that the FRED-based price
extension runs in CI. The published `data/sp500_pe.json` SHALL therefore include
the post-Shiller monthly extension (FRED-priced months with overrides-based and
forward-filled TTM earnings) through the last completed month, matching what a local
run with the key produces.

#### Scenario: P/E refresh in CI with the key wired in

- **WHEN** the daily workflow runs the S&P 500 P/E step
- **THEN** the FRED SP500 price fetch succeeds and the published `sp500_pe.json`
  contains observations through the last completed month, including post-Shiller
  months marked `estimated=true` where earnings are forward-filled

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

