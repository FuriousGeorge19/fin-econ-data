## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Treasury Spreads tab
**Reason**: There are no tabs; placement is a descriptor `presentation` value.
**Migration**: "Treasury Spreads chart" above.
