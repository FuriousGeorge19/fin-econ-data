# treasury-spreads-series Specification

## Purpose

The Treasury yield-spread series (10y-2y and 10y-3m), computed in Python at fetch time
from the daily constant-maturity component series, plus the dashboard's "Treasury
Spreads" tab — a dual-line chart with a zero reference line, NBER recession-band overlay,
and a current-values table.
## Requirements
### Requirement: Fetch components and compute spreads in Python

`scripts/fetch_spreads.py` SHALL fetch the daily constant-maturity series DGS10, DGS2,
and DGS3MO from FRED via the shared `fred_utils` module, and SHALL compute two derived
spread series in Python at fetch time: `10y2y = DGS10 − DGS2` and `10y3m = DGS10 − DGS3MO`.
It SHALL write a single `data/spreads.json`. The script SHALL NOT use FRED's precomputed
`T10Y2Y`/`T10Y3M` series, and SHALL NOT compute spreads in the browser.

#### Scenario: Spreads computed at fetch time

- **WHEN** `fetch_spreads.py` runs with a valid `FRED_API_KEY`
- **THEN** `data/spreads.json` is written containing both the `10y2y` and `10y3m` spread
  series, each value rounded and expressed in percentage points, with no spread arithmetic
  left for the frontend

### Requirement: Spread date alignment

A spread observation for a given date SHALL be emitted only when both component legs
report a value on that date. Dates where either leg is missing SHALL be omitted; values
SHALL NOT be forward-filled or interpolated. Each spread series therefore spans its own
valid date range (the 10y-2y series begins only once both DGS10 and DGS2 exist).

#### Scenario: Partial-leg date omitted

- **WHEN** DGS10 reports on a date but DGS2 does not
- **THEN** no `10y2y` value is emitted for that date, and the gap is left as-is

### Requirement: spreads.json output shape

`data/spreads.json` SHALL follow the `series-metadata` header contract (`meta` from
`series/spreads.json`, `as_of` with per-series as-of for `10y2y` and `10y3m`) and SHALL
present the two spreads keyed so the frontend can plot each as its own line over a date
axis without re-sorting.

#### Scenario: Output carries both series and metadata

- **WHEN** the fetcher writes `data/spreads.json`
- **THEN** the file contains `meta`, `as_of` (including `as_of.series["10y2y"]` and
  `as_of.series["10y3m"]`, each with its own first and last observation and `due_by`),
  plus the `10y2y` and `10y3m` spread series, each as date/value observations ordered
  oldest-first

### Requirement: NBER recession shading on the spreads chart

The spreads chart SHALL display NBER recession periods as shaded overlay bands behind the
spread lines, sourced from the shared recession dataset, requested by
`presentation.chart.recessions: true` and drawn by the `timeseries` type from
`ctx.recessions`. An ongoing (open-ended) recession SHALL be shaded through to today,
the chart's x-axis end under the `chart-chrome` rule.

#### Scenario: Recession bands present

- **WHEN** the spreads chart renders
- **THEN** each NBER recession interval from the recession dataset appears as a shaded band
  behind the spread lines, aligned to the chart's date axis

### Requirement: Current values table

The card SHALL include a current-values table listing both spreads with their latest
value and period changes, anchored on the last observation and showing each resolved
comparison date (the `chart-chrome` comparison rule), produced by the `timeseries`
type's `changes` table kind.

#### Scenario: Table shows latest spreads and changes

- **WHEN** the spreads card renders its table
- **THEN** it shows a row per spread (10y-2y and 10y-3m) with the latest value and its
  date, and its change over each comparison period with that period's resolved date

### Requirement: Treasury Spreads chart

`series/spreads.json` SHALL carry a `presentation` block placing the series in the
`economy` section with `order` 20 and chart type `timeseries` with no custom module:
the `series` payload gives the two traces, `y.format` is `+.2f`, `zeroline` is true,
`recessions` is true, presets are 1Y / 5Y / 10Y / 25Y / All, stats are off, and the
table kind is `changes` with windows 1M and 1Y. The chart SHALL plot both the 10y-2y
and 10y-3m spreads as distinct lines over time with a zero reference line (so
inversions below zero are visually obvious). Because the type derives the hover date
format from the daily cadence, the hover SHALL show the full date (the pre-S5 chart
showed month and year; this change is intended).

#### Scenario: Spreads page renders

- **WHEN** the user opens `/charts/spreads/` or `/economy/`
- **THEN** the card loads `/data/spreads.json` and draws two labeled spread lines with a
  visible zero baseline, and the Economy nav row lists "Treasury Spreads"

