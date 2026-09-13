## MODIFIED Requirements

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
spread lines, sourced from the shared recession dataset. An ongoing (open-ended) recession
SHALL be shaded through to today, the chart's x-axis end under the `chart-chrome` rule.

#### Scenario: Recession bands present

- **WHEN** the spreads chart renders
- **THEN** each NBER recession interval from the recession dataset appears as a shaded band
  behind the spread lines, aligned to the chart's date axis

### Requirement: Current values table

The tab SHALL include a current-values table listing both spreads with their latest value
and period changes, anchored on the last observation and showing each resolved
comparison date (the `chart-chrome` comparison rule), consistent with the other tabs.

#### Scenario: Table shows latest spreads and changes

- **WHEN** the Treasury Spreads tab renders its table
- **THEN** it shows a row per spread (10y-2y and 10y-3m) with the latest value and its
  date, and its change over each comparison period with that period's resolved date
