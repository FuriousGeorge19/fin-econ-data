## Why

After S4b shipped on 2026-09-13 the live site shows five chart-chrome defects that the
S4b browser check missed: every chart keeps its "Loading chart..." placeholder, three of
the four charts render at Plotly's 700px fallback width, the range slider hides the
in-chart source line, "All" shows one month, and a card reopens on whichever sub-tab was
last used. All five live in `site/index.html`; none touch data or Python. They need
fixing before S5 designs the chart component around the current behaviour, because two of
them are contract questions S5 must answer explicitly (when `render` may run, and whether
the preset row stays Plotly's).

## What Changes

- The "Loading chart…" text is produced by CSS on an empty chart container; the
  placeholder `<div>`s are removed. Plotly does not clear its container (it inserts its
  own `div` as the first child), so the old placeholder survived every render.
- A chart is drawn the first time its tab is visible; data is still fetched at page load.
  Later tab switches refit the chart, so a window resize while the tab was hidden is
  picked up. Plotly sizes a hidden container to 700px and remembers that on the chart's
  config context.
- **BREAKING (visual)**: the range slider is removed from the 10Y, P/E and spreads
  charts. The source line then sits unobstructed in the bottom margin.
- "All", the mode bar's reset-axes button and double-click all set the x-axis to
  `[first_observation, today]` via `xaxis.autorangeoptions`. The previous "All" passed
  `method`/`args` (updatemenus attributes), so Plotly treated it as a default
  one-month-backward button.
- Switching top-level tabs resets the destination card to its Chart sub-tab.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `dashboard-site`: "Tabbed navigation across series" (activation resets the card to its
  Chart sub-tab and refits the chart); "Data fetched on page load, not lazily" (fetch at
  load stays; the chart is drawn on first show, never while hidden); a new "Loading
  placeholder" requirement.
- `chart-chrome`: "In-chart source line" (no chart control may overlap it; no range
  slider on time-series charts); "Time-series x-axis ends at today" ("All", reset and
  double-click all return to `[first_observation, today]`).

## Impact

- `site/index.html` only (CSS and JS). No fetcher, data file, test or workflow change.
  Ships through the normal `update-data.yml` deploy (a manual `workflow_dispatch` today,
  since the cron is weekday-only). Rollback is a revert of the one commit.
- `openspec/specs/dashboard-site` and `openspec/specs/chart-chrome` gain the merged
  deltas at archive time.
- S5 design inputs recorded in `design.md` (render-when-visible contract, preset row as a
  component question, source-line band rule) and in the Obsidian handoff.
