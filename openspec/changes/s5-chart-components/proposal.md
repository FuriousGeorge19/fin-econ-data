## Why

S5 of the cross-session plan (`~/Obsidian/Investing/Finance and Economic Data
Website/Session Plan.md`) is the second of the two design sessions: settle how charts
are built and how pages are assembled before any more charts exist, because every chart
built afterwards is either a config entry on this pattern or another hand-written block
in one file. S6a/S6b build the exemplar, S7 ports the other three charts as three
parallel agents, S11 adds roadmap charts 3–10 the same way, and S12 builds the first
one-pager; all of them depend on the file-additive rule this change defines.

Today the site is one file, `site/index.html` (1562 lines): four flat tabs, four
near-identical loader skeletons, three copies of the same Plotly layout block, ~60 colour
literals in chart code, and a data fetch that is page-relative and so breaks under any
subdirectory. The yield curve is the only chart with DOM controls and module-level
state. Adding a series means ~150 lines of JS in that file plus edits to the workflow in
three places (the fetch step, its `OUTCOME_<id>` env line, and the id list in the summary
step); two parallel agents doing that conflict on the same hunk. `series/<id>.json`
already reserves a `presentation` block and `meta_from_descriptor()` already strips it
from the data file, so nothing the browser loads today can say how a series is drawn.

Decided by the user on 2026-09-13: plain ES modules plus a stdlib Python page generator
(the "no build step" conviction re-stated as "no JavaScript toolchain"); `/` is a curated
grid from `pages/home.json`; the preset row is HTML buttons; `scripts/fetch_all.py`
replaces the per-series workflow steps now, not in S11.

## What Changes

- **Chart components**: one ES module per chart *type* in `site/js/charts/`
  (`timeseries`, `curve`, plus custom modules named after a series) exporting
  `render(el, ctx)` and optional `stats`, `table`, `csv`. Per-series drawing config lives
  in `series/<id>.json` `presentation` (sections, order, summary, chart type and options,
  stats, table). Shared runtime in `site/js/lib/` (card mount, one Plotly layout builder,
  presets, as-of chrome, dates, export, theme, data). No colour literal in `site/js`;
  token names only, so S5b themes by re-valuing tokens.
- **Multi-page generated site**: `scripts/build_site.py` (stdlib only) reads
  `pages/site.json`, `series/*.json` and `pages/*.json`, writes `site/index.html`,
  `site/<section>/index.html`, `site/charts/<id>/index.html` and
  `site/<section>/<slug>/index.html` (page shell + static nav + block placeholders +
  inline block JSON), and copies `data/*.json` into `site/data/`. Generated paths are
  gitignored; `site/css` and `site/js` are committed sources. **BREAKING**: the
  single-file dashboard and its tabs are retired at cutover (end of S7); until then the
  old `/` stays live and the new pages appear under their own URLs.
- **Card chrome and mount lifecycle**: `card.js` builds the whole card in the browser
  (title link, summary, badge, control row, `Chart | Table | About`, exports), fetches
  eagerly at mount, and is the only code that plots — into a container that is visible
  by construction. `Plotly.Plots.resize` on return to the Chart sub-tab; `destroy()` then
  `render()` on `themechange`. The preset row is HTML buttons calling `Plotly.relayout`;
  "All" is `autorange` clipped to `[first, today]`. One layout builder alone sets margins
  and legend position, and never a range slider or a height.
- **Page manifests**: `pages/<slug>.json` (`slug`, `section`, `title`, `layout`
  grid | narrative, `intro`, `blocks[]` of `{chart, size, preset}` or `{text: {html}}`);
  `home.json` is `/`; section pages are automatic grids of their charts.
- **Workflow**: one `python scripts/fetch_all.py` step (each descriptor's `fetcher`,
  default `fetch_<id>.py`, run as a non-fatal subprocess; results in
  `data/fetch_status.json`) replaces the five fetch steps and the `OUTCOME_*` env;
  `python scripts/build_site.py` replaces the copy step; the summary and the final
  fail-after-deploy steps read `fetch_status.json`. Rollback is one file.
- **Tests**: `tests/test_build_site.py` (generator into `tmp_path`: a page per series,
  section order, manifests resolve, payload shape per type, module and fetcher files
  exist, no colour literal in `site/js`, no `margin`/`rangeslider`/`height` outside the
  layout builder) and `presentation` schema checks in `tests/test_series_metadata.py`.

## Capabilities

### New Capabilities
- `chart-components`: the render contract and `ctx`, chart types and their options, the
  `presentation` schema and payload convention, the mount lifecycle, the preset row, the
  source-line band rule, theme tokens, the no-literal and no-module-state rules.
- `site-build`: the generator's inputs and outputs, the URL scheme and nav, page
  manifests, ignored generated paths, the file-additive rule, `fetch_all.py` and
  `fetch_status.json`, the generator tests.

### Modified Capabilities
- `dashboard-site`: single file → generated multi-page site with no JavaScript toolchain;
  tabs → section nav; "fetched on page load" → the mount lifecycle; root-relative data;
  mobile rule by variant class; "Default tab on page load" removed.
- `chart-chrome`: the band is owned by the layout builder and range buttons live outside
  the figure; the sub-tab strip is card chrome; the default CSV is an outer join on trace
  keys.
- `series-metadata`: `presentation` schema (defined by `chart-components`) and `fetcher`;
  absent `presentation` = data-only dataset; the header-contract scenario no longer
  names `site/index.html`.
- `daily-automation`: fetch steps → `fetch_all.py`; copy step → `build_site.py`; the
  secret goes to the one runner step; failure reporting reads `fetch_status.json`.
- `treasury-10y-series`, `sp500-pe-series`, `yield-curve-series`,
  `treasury-spreads-series`: the "tab" requirements become section placement plus chart
  type; spreads records its intended hover-format change and the `changes` table kind.

## Impact

- **Affected (S6a, Python)**: new `pages/site.json`, `scripts/build_site.py`,
  `scripts/fetch_all.py`, `tests/test_build_site.py`; modified `series/dgs10.json`
  (`presentation`, `fetcher`), `tests/test_series_metadata.py`,
  `.github/workflows/update-data.yml`, `scripts/dev.sh`, `.gitignore`.
- **Affected (S6b, JS)**: new `site/css/site.css`, `site/js/app.js`, `site/js/lib/*.js`,
  `site/js/charts/timeseries.js`; `site/index.html` untouched.
- **Affected (S7, workflow)**: `series/{spreads,sp500_pe,yield_curve}.json`; new
  `site/js/charts/sp500_pe.js`, `site/js/charts/curve.js`.
- **Affected (cutover)**: `pages/home.json`; `site/index.html` and `site/data/*.json`
  leave git; `CLAUDE.md`, `ARCHITECTURE.md`, `HOW-IT-WORKS.md`.
- **Not affected**: the fetchers and their payload shapes; `meta`/`as_of`; the freshness
  rule; the Plotly version; S5b's palette values (S5b defines the token values; this
  change fixes only the names).
- **Rollback**: the workflow change is one file and reverts alone. Until cutover the old
  `site/index.html` is untouched and live, so S6a, S6b and S7 can each be reverted
  without touching the deployed site; the generator only adds files at paths that did
  not exist before.
