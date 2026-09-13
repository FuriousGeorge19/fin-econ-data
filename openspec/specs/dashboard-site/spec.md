# dashboard-site Specification

## Purpose

The single-file static dashboard — `site/index.html` with all markup, styles, and
JavaScript inline — providing tabbed navigation across data series, a dark theme,
per-tab data loading, and Plotly.js charts loaded from a CDN, with no build step,
no framework, and no backend.
## Requirements
### Requirement: Single-file static dashboard

The site SHALL be a single static `site/index.html` containing all markup, styles, and
JavaScript inline, served by GitHub Pages with no build step, no framework, and no
backend. Charts SHALL be rendered with Plotly.js.

#### Scenario: Page loads standalone

- **WHEN** `site/index.html` is opened (locally or on GitHub Pages)
- **THEN** it renders the full dashboard using only inline code plus the Plotly.js
  library, with no server-side rendering or API calls beyond fetching the static JSON files

### Requirement: Tabbed navigation across series

The dashboard SHALL present each data series in its own tab in a top nav bar,
with exactly one tab active at a time. Each tab's label and binding to a series
is defined by that series' own spec; the dashboard itself is agnostic to which
series exist. Activating a tab SHALL select that card's `Chart` sub-tab regardless of
which sub-tab was last open, and SHALL refit the card's chart to its container if the
chart was already drawn, so a window resize while the tab was hidden is picked up.

#### Scenario: Switching tabs

- **WHEN** the user clicks a tab in the nav bar
- **THEN** that tab's content becomes visible, the others are hidden, and the
  clicked tab is marked active

#### Scenario: Returning to a card shows the chart

- **WHEN** the user opens a card's Table sub-tab, switches to another tab, and returns
- **THEN** the card shows its Chart sub-tab

#### Scenario: Window resized while hidden

- **WHEN** the browser window is resized while a tab is hidden and the user then
  activates that tab
- **THEN** its chart is refitted to the card width

### Requirement: Dark theme and per-tab data loading

The dashboard SHALL use a dark theme and SHALL load each tab's data by fetching the
corresponding `data/<name>.json` file relative to the page.

#### Scenario: Data fetched per series

- **WHEN** a tab needs its data
- **THEN** the page fetches the matching JSON (`data/dgs10.json`, `data/sp500_pe.json`,
  or `data/yield_curve.json`) and renders its chart and table from that response

### Requirement: Plotly loaded from CDN, not bundled

The dashboard SHALL load Plotly.js from a public CDN (`cdn.plot.ly`) at a version
pinned in the HTML `<script>` tag. The repository SHALL NOT bundle, vendor, or
self-host the Plotly library.

#### Scenario: Plotly available at page load

- **WHEN** `site/index.html` is opened
- **THEN** the page's `<script>` tag references the pinned Plotly version on
  `cdn.plot.ly` and the library is loaded before any chart-rendering code runs

### Requirement: Default tab on page load

The dashboard SHALL render with exactly one tab active by default when the page
first loads, with that tab's chart and table visible and the other tabs hidden.

#### Scenario: Initial render

- **WHEN** a user opens the page
- **THEN** exactly one tab is active and its content is visible; other tabs are
  hidden until the user activates them

### Requirement: Data fetched on page load, not lazily

The dashboard SHALL fetch each series' JSON data file when the page loads, not
on tab activation. All baseline series payloads SHALL be available in memory by
the time the user begins switching tabs. Stats, tables, the freshness badge, the About
tab and the export buttons SHALL be rendered as each fetch resolves. A chart SHALL be
drawn the first time its tab is visible and SHALL NOT be drawn while its container is
hidden, because Plotly sizes a hidden container to a 700px fallback and keeps that size.

#### Scenario: All series loaded upfront

- **WHEN** the page loads
- **THEN** the dashboard issues fetches for each series' `site/data/<name>.json`
  and renders each tab's non-chart content as its corresponding fetch resolves

#### Scenario: Chart drawn on first show

- **WHEN** the user first activates a tab whose data has already loaded
- **THEN** its chart is drawn at that moment and fills the card width (the figure's
  width equals the container's width)

#### Scenario: Tab activated before its data arrives

- **WHEN** the user activates a tab before its fetch resolves
- **THEN** the chart is drawn as soon as the fetch resolves, sized to the visible
  container

### Requirement: Fetch failure surfaces an error message

The dashboard SHALL display a human-readable error message in place of a tab's
chart when that tab's data fetch fails (network error, missing file, malformed
JSON), rather than rendering empty or broken visuals. Other tabs SHALL continue
to function.

#### Scenario: A JSON file is missing

- **WHEN** the page attempts to fetch a series' JSON file and the request fails
- **THEN** that tab's chart area shows an error message identifying the failure,
  and the remaining tabs render normally

### Requirement: Minimal mobile breakpoint

The dashboard SHALL provide a `max-width: 640px` CSS breakpoint that reduces page
padding and the Treasury and S&P 500 P/E chart heights. Cards stack in a single
column by default (block-level layout), so narrow viewports already present one
column without additional rules.

**Known gap:** The yield-curve chart height and wide data tables (notably the
five-column yield-curve "Current Yields" table) are not yet adapted for narrow
viewports and may require horizontal scrolling. Full mobile responsiveness is a
planned follow-up, not part of this baseline.

#### Scenario: Page viewed at mobile width

- **WHEN** the page is rendered at a viewport width ≤ 640px
- **THEN** page padding is reduced, the Treasury and P/E charts shrink to the
  mobile height, and cards remain stacked in a single column
- **AND** the yield-curve table and chart are unchanged from their desktop sizing
  and may still scroll horizontally

### Requirement: Loading placeholder

Each chart container SHALL show "Loading chart…" only while it is empty. The text SHALL
disappear the moment the chart library inserts its elements, without any script removing
it. A failed fetch SHALL replace it with the error message.

#### Scenario: Placeholder gone after render

- **WHEN** a card's chart has been drawn
- **THEN** no "Loading chart…" text is visible anywhere on the page for that card

#### Scenario: Placeholder until the data arrives

- **WHEN** the user activates a tab whose fetch has not yet resolved
- **THEN** the container shows "Loading chart…" until the chart is drawn

