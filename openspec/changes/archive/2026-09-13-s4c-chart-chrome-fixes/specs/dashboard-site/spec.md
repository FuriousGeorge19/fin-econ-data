## MODIFIED Requirements

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

## ADDED Requirements

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
