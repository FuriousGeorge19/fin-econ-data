## Why

`openspec/changes/s5-chart-components/` (approved 2026-09-13, nothing built) designs
the future multi-page chart-component contract but explicitly excludes palette values,
the light/dark toggle, and a Plotly template per mode from its own scope — its
design.md names this session "S5b" and says it must land before S6a/S6b, because S6b's
own task list depends on the token contract this session produces
(`site/js/lib/theme.js`, "reads the tokens into `ctx.theme`"). Today's site is
dark-theme-only: six colour tokens in `:root`, and roughly 60 hard-coded colour
literals scattered across `site/index.html`'s Plotly configs and a few CSS rules.
Nothing in the file supports a second theme.

## What Changes

- `site/css/tokens.css` (new): the full token set `s5-chart-components` requires
  (`--series-1`…`--series-6`, `--gridline`, `--axis-line`, `--zero-line`,
  `--annotation`, `--up`, `--down`, `--recession-fill`, `--legend-bg`, plus the
  existing six), defined for both a light and a dark palette. Dark values are a
  verbatim extraction of today's literals — not a redesign. Light values and two new
  series slots (`--series-5`/`--series-6`, unused today) are new, sourced from the
  "dataviz" skill's validated, contrast/CVD-checked default palette.
- A light/dark toggle button in the nav bar: defaults to `prefers-color-scheme` with no
  stored preference; an explicit choice sets `data-theme` on `<html>`, persists via
  `localStorage`, and overrides the OS setting either way.
- `getTheme()` (new function inside `site/index.html`'s existing script): reads the
  tokens via `getComputedStyle`. Every chart-drawing function and every up/down
  stat/table function is retoned to call it instead of a literal. On a new
  `themechange` event, all four charts and their tables redraw — visible ones
  immediately, hidden ones deferred to first show through the existing
  `renderWhenVisible` mechanism (S4c), so the 700px-fallback bug that fix addressed is
  not reintroduced.
- A latent bug fixed in passing: today's tab-click handler binds to every `nav button`
  with no filter (`document.querySelectorAll('nav button')`); adding the toggle as a
  nav child would make it fire tab-switch logic. Narrowed to `nav button[data-tab]`.
- **BREAKING (visual)**: none in dark mode — verified pixel-identical before/after.
  Light mode is new, so there is nothing prior for it to break.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `dashboard-site`: "Dark theme and per-tab data loading" is REMOVED (its per-tab-fetch
  half is already superseded by the later "Data fetched on page load, not lazily"
  requirement; its dark-theme-only half is no longer true) and replaced by an ADDED
  "Light and dark theme, toggle defaults to system preference".
- `chart-chrome`: an ADDED "Chart and table colors follow the active theme".

## Impact

- `site/index.html` (CSS and JS) and one new file, `site/css/tokens.css`. No fetcher,
  data file, test or workflow change. Ships through the normal `update-data.yml`
  deploy. Rollback is a revert of the one commit.
- `openspec/specs/dashboard-site` and `openspec/specs/chart-chrome` gain the merged
  deltas at archive time.
- Unblocks S6a/S6b: `site/css/tokens.css` is the file `s5-chart-components` task 4.1
  reads from once landed; `getTheme()` is provisional scaffolding S6b's
  `site/js/lib/theme.js` is expected to absorb near-verbatim.
