# chart-components Specification

## Purpose
TBD - created by archiving change s5-chart-components. Update Purpose after archive.
## Requirements
### Requirement: Chart type modules and the render contract

Every chart SHALL be drawn by a chart type module at `site/js/charts/<type>.js`, a native
ES module with no build step. A type module SHALL export `render(el, ctx)`, which draws
into `el` and returns an object with `destroy()`, and MAY export pure functions
`stats(ctx)` (returning `[{label, value, date}]`), `table(ctx)` (returning `{columns,
rows, note}`) and `csv(ctx)` (returning a string). `render` SHALL be called at most once
per mount by the card chrome, with `el` visible and laid out; a type MAY redraw itself
into the same `el` (for example `Plotly.react` after its own controls change). Built-in
types are `timeseries` and `curve`; a custom module SHALL be named after the series id
it serves. A type module SHALL NOT hold module-level mutable state, SHALL NOT call
`document.getElementById`, SHALL NOT write outside `el` and `ctx.slots`, and SHALL be
mountable more than once on one page.

#### Scenario: Two curves on one page

- **WHEN** a page mounts the `curve` type for the nominal yield curve and again for a
  TIPS curve
- **THEN** each mount has its own data, controls and state, and toggling an overlay on
  one does not redraw the other

#### Scenario: Custom module for a series

- **WHEN** `series/sp500_pe.json` sets `presentation.chart.type` to `sp500_pe`
- **THEN** the card imports `/js/charts/sp500_pe.js` and calls its `render`, and the
  generator fails the build if that file does not exist

### Requirement: Render context

The card chrome SHALL pass every type a `ctx` object with `id`, `data` (the parsed
`data/<id>.json`), `meta`, `as_of`, `presentation`, `today` (the US Eastern calendar
date `YYYY-MM-DD`, computed once per page), `theme` (the token → value map read from
CSS custom properties), `variant` (`full`, `half` or `third`), `recessions` (the
interval list from `data/usrec.json`, or `null`), `initialPreset` (a preset label or
`null`) and `slots.controls` (an element in the card's control row for type-owned
controls). `stats`, `table` and `csv` SHALL depend only on `ctx`.

#### Scenario: Controls in the control row

- **WHEN** the `curve` type renders
- **THEN** its overlay toggles and custom date input are children of `ctx.slots.controls`
  and nothing else in the card is modified by the type

### Requirement: Presentation block

A descriptor's `presentation` object SHALL carry `sections` (a non-empty list of section
ids from `pages/site.json`), `order` (integer sort key within a section), `summary` (one
line shown under the title), `chart` (`type` plus type options), `stats` (`true` or
`false`; default `true` for a single-trace `timeseries`, `false` otherwise) and `table`
(`false`, `true`, or an object with `kind` and options). A descriptor without
`presentation` SHALL be a data-only dataset with no page and no nav entry. Colours in
`presentation` SHALL be token names (`series-1` … `series-6`), never colour literals.

#### Scenario: Data-only dataset

- **WHEN** `series/usrec.json` has no `presentation`
- **THEN** no `/charts/usrec/` page is generated and USREC appears in no nav row

#### Scenario: Presentation validated

- **WHEN** `pytest` runs `tests/test_series_metadata.py`
- **THEN** every `presentation` uses only the allowed keys, every `sections` entry
  exists in `pages/site.json`, every preset matches `^\d+[MY]$`, `YTD` or `All`, and the
  `chart.type` module file exists

### Requirement: Timeseries type payload convention and options

The `timeseries` type SHALL derive its traces from the payload without a path adapter:
a data file with `series` gives one trace per key, labelled from `series[key].label`
with the key as trace key; otherwise `observations` gives one trace whose y field is
`presentation.chart.y.field` (default `value`), keyed by that field name and labelled
`meta.short_title`. An optional `traces: [{key, y, label, color}]` list SHALL override
this. Options SHALL be `y {suffix, format}`, `presets` (absent means no preset row),
`recessions` (`true` makes the card fetch `/data/usrec.json`, tolerating a 404, and the
type draws the intervals as shapes in its initial layout), and `zeroline`. Hover
x-format SHALL derive from `meta.cadence` (daily: full date; monthly: `%b %Y`). The
x-axis start SHALL be the earliest x over the traces. Stats SHALL be latest, 1Y high,
1Y low and 1Y change, each with its resolved date. Table kinds SHALL be `recent` (last
`rows` observations, one column per trace, with change) and `changes` (one row per
trace: latest, and the change over each of `windows` with its resolved date). The
default `csv` SHALL be an outer join of the traces on date with columns `date,<key>…`.

#### Scenario: Spreads by config

- **WHEN** `series/spreads.json` sets `chart.type` `timeseries`, `zeroline` true,
  `recessions` true and `table {kind: changes, windows: [1M, 1Y]}`
- **THEN** the chart draws the `10y2y` and `10y3m` traces with a zero line and recession
  bands, the table has one row per spread with 1-month and 1-year changes and their
  resolved dates, and the CSV has columns `date,10y2y,10y3m`

#### Scenario: Single-series default

- **WHEN** `series/dgs10.json` sets `chart.type` `timeseries` with no `traces`
- **THEN** one trace keyed `value` labelled `10Y Treasury` is drawn and the CSV has
  columns `date,value`

### Requirement: Curve type options

The `curve` type SHALL draw the latest date's values across `data.tenors` on a
categorical, evenly spaced x-axis, with dashed overlays for each enabled entry of
`overlays` (`1w`, `1m`, `1y`, `5y`) and a dotted overlay for a custom date when
`custom_date` is true, each overlay date resolved by the `chart-chrome` comparison rule.
It SHALL NOT show a preset row. Its `table` SHALL list each tenor with the latest yield
and the change against each overlay, with the resolved comparison date in the column
title, and its `csv` SHALL be the wide form (`date` then one column per tenor).

#### Scenario: Overlay toggled

- **WHEN** the user enables the 1-year overlay
- **THEN** the type redraws into the same container with the additional dashed curve
  and no other card on the page changes

### Requirement: Card mount lifecycle

`site/js/lib/card.js` SHALL be the only code that plots into a card. For each block it
SHALL: build the whole card DOM (title linking to `/charts/<id>/`, summary, badge,
control row, `Chart | Table | About` sub-tab strip, chart container, stats, table, About,
export buttons) with a loading state in every panel; fetch `/data/<id>.json` eagerly at
mount (and `/data/usrec.json` when the chart asks for recessions); own the error message
when a fetch fails; render badge, stats, table, About and exports as the fetch resolves;
import the type module and call `render` once with the Chart sub-tab visible; call
`Plotly.Plots.resize` when the Chart sub-tab is shown again; call `destroy()` then
`render()` on a `themechange` event; and apply `initialPreset` after render. Cards SHALL
never be `display:none` at mount; if a future layout hides cards, the deferral SHALL be
implemented inside `mount`, never in a type.

#### Scenario: Chart drawn into a visible container

- **WHEN** any page mounts a card
- **THEN** the chart's `_fullLayout.width` equals the container's `clientWidth` on first
  draw, with no 700px fallback

#### Scenario: Return from the Table sub-tab after a resize

- **WHEN** the user opens the Table sub-tab, resizes the window, and returns to Chart
- **THEN** the chart is refitted to the container width

#### Scenario: Fetch fails

- **WHEN** `/data/<id>.json` returns 404
- **THEN** the card's chart panel shows an error message naming the failure and every
  other card on the page renders normally

### Requirement: Preset row as HTML buttons

Time-series charts SHALL present their range presets as HTML buttons in the card's
control row, outside the Plotly figure, rendered from `presentation.chart.presets`. Each
preset SHALL call `Plotly.relayout` with an explicit range ending at today: `nM`/`nY`
count back from today, `YTD` starts at 1 January of today's year, and `All` sets
`xaxis.autorange` true so that `autorangeoptions` yields `[first observation, today]`.
The active button SHALL follow `plotly_relayout` events, with no button active after a
drag-zoom. Plotly's `rangeselector` SHALL NOT be used.

#### Scenario: All agrees with reset

- **WHEN** the user clicks "All", then double-clicks the plot, then clicks the mode bar's
  reset-axes button
- **THEN** all three leave the x-axis range at `[first observation, today]`

#### Scenario: Preset from a page manifest

- **WHEN** a composite page block sets `"preset": "10Y"`
- **THEN** the chart renders and is immediately relayouted to the last ten years with
  the 10Y button active

### Requirement: One layout builder owns margins, legends and the band

`site/js/lib/plotly-layout.js` SHALL be the only file under `site/js` that sets Plotly
`margin`, legend position, `rangeslider` or `height`. It SHALL reserve the bottom margin
for the source-line annotation, place legends at the top of the plot area, never set a
range slider, and never set a height (chart height is CSS per variant). It SHALL apply
axis, grid, font and annotation colours from `ctx.theme`.

#### Scenario: Band enforced by test

- **WHEN** a chart type module sets `margin` or `rangeslider`
- **THEN** `tests/test_build_site.py` fails naming the file and key

### Requirement: Theme tokens and no colour literals

`site/js` SHALL contain no hex or rgb colour literal. Chart code SHALL read colours from
`ctx.theme`, populated from the CSS custom properties `--bg`, `--surface`, `--border`,
`--text`, `--text-muted`, `--accent`, `--series-1` … `--series-6`, `--gridline`,
`--axis-line`, `--zero-line`, `--annotation`, `--up`, `--down`, `--recession-fill` and
`--legend-bg`. Token names SHALL NOT change; S5b re-values them per mode.

#### Scenario: Literal rejected

- **WHEN** a module under `site/js` contains `#38bdf8`
- **THEN** `tests/test_build_site.py` fails naming the file

#### Scenario: Re-theme without a contract change

- **WHEN** the page dispatches `themechange` after the tokens are re-valued
- **THEN** every card destroys and re-renders its chart and the new colours appear

