# site/js — runtime rules (loads when a JS file is read)

Native ES modules, no bundler, no npm, Plotly from a CDN `<script>` tag. The contract is
`openspec/specs/chart-components/spec.md` and `chart-chrome/spec.md`; two of the rules are
enforced by `tests/test_build_site.py` (`test_no_colour_literal_in_site_js`,
`test_forbidden_layout_keys_confined_to_layout_and_card`).

## Layout

- `app.js` — parses the inline `#page` JSON, computes `todayET()` once, mounts every block.
- `lib/card.js` — `mount(block, today)`, **the only code that plots into a card**. Builds
  the card DOM scoped to its own container, fetches `/data/<id>.json` (root-relative,
  `lib/data.js`), imports the chart type, renders badge / stats / table / About / exports,
  calls `render` once, wires presets, re-renders on `themechange` (clearing
  `ctx.slots.controls` first). Both failure paths go through `markCardFailed`, so the blast
  radius of a failure is one card.
- `lib/plotly-layout.js` — `baseLayout` / `xaxisToToday` / `PLOT_CONFIG`: **the only file
  allowed to set Plotly `margin`, legend position, a range slider, or a chart height.**
- `lib/theme.js` — `getTheme()` reads `css/tokens.css`'s custom properties at draw time;
  `fmtChange()` is the one up/down formatter (a yield going *up* is coloured `down`: bad
  for a bond holder).
- `lib/asof.js` (in-chart source line, freshness badge, About HTML), `lib/presets.js`
  (HTML preset buttons → `Plotly.relayout`), `lib/dates.js` (UTC-only date math),
  `lib/export.js`.
- `charts/<type>.js` — one module per chart type: `timeseries`, `curve`, `tenors`,
  `sp500_pe`, `yields_table`.

## Rules for a chart type

- Export `render(el, ctx)`; optionally `stats`, `table`, `csv` — all pure except `render`.
  `table()`/`csv()` see the configured options, never live DOM state.
- No module-level mutable state: a type can be mounted twice on one page (two `curve`
  charts sit on `/rates/`). Interactive state lives in `render()`'s closure; redraw with
  `Plotly.react`, not a fresh `newPlot`. Controls mount into `ctx.slots.controls`.
- No `document.getElementById`; use `el` and `ctx.slots`.
- Colours only from `ctx.theme`; no hex/rgb literal anywhere under `site/js`.
- Never set `margin`, legend position, `rangeslider` or `height` (see above).
- Precompute hover text into a `text` array and use a `%{text}` template. Plotly's
  `%{y:<fmt>}` is plain d3-format and rejects this repo's `"+.2f"` (the spreads bug); the
  hover date format derives from `meta.cadence`, not Plotly's zoom-adaptive default.
- Draw only when the container is visible — Plotly sizes a hidden one to 700px and
  remembers it. `card.js` owns first-show and `Plotly.Plots.resize`.
- "All", the mode-bar reset and double-click all mean `[first_observation, today]` via
  `xaxis.autorangeoptions`. No range slider: the in-chart source line owns the bottom band.
- No fetcher emits nulls and `timeseries.js` sets no `connectgaps`, so an omitted month is
  drawn through. Accepted; a null-observation convention would touch every fetcher.
- When an observation carries `source`, `timeseries.js` adds a "Source: <short_name>" hover
  line resolved against `meta.sources[].slug` — a no-op on every unstitched chart.
- The last selectable item in a selector cannot be switched off (an empty chart reads as
  broken, `tenors.js`).
- A new chart type is a new file only, never an edit to a shared file.

## CSS

- `css/site.css` `@import`s `css/tokens.css` and that line must come first. Every colour is
  a token, and the twenty token *names* are frozen (by `s5-chart-components`) — values
  change, names don't; light and dark are separate palettes, each validated with the dataviz skill's
  palette checker, not one inverted from the other.
- Grid: `card--full` / `card--half` / `card--third`, one column under 640px.

## Checking a change

Serve with `scripts/dev.sh` and open `http://127.0.0.1:8899/…`. Read computed values
(`_fullData`, `_fullLayout.width`, `getComputedStyle`), not just a screenshot: the missing
`tokens.css` import once hid behind Plotly's default blue in every screenshot. Zero console
messages is the bar.
