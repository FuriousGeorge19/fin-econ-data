## Context

This is the second of the two design sessions in the multi-session plan (S5; S3 was
series metadata). Its output is a contract, not a feature: how a chart is built, how a
page is assembled from charts, and what "adding a series" touches. S6a/S6b build the
exemplar, S7 ports the other three charts as three parallel agents, S11 adds roadmap
charts 3–10 the same way, and S12 builds the first one-pager; each depends on being able
to add files without editing shared ones.

The system today: `site/index.html`, 1562 lines, one file. Six colour tokens in `:root`
and ~60 colour literals inside Plotly layouts; four flat tabs whose DOM order differs
from the nav order; four near-identical loader skeletons; a shared region of ~290 JS
lines (tab machinery, UTC date helpers, `loadSeries`, the as-of chrome, the About
renderer, export wiring, Plotly config) and ~160 lines of copy-pasted time-series layout
code. The yield curve is the only chart with DOM controls, module-level state (`ycData`,
`ycDates`) and a full re-plot on interaction. The data fetch is page-relative
(`fetch('data/${id}.json')`), so any page in a subdirectory 404s. Adding a series edits
the workflow in three places — the fetch step, its `OUTCOME_<id>` env line, and the id
list in the summary step — and two parallel agents doing that conflict on the same hunk.

Three facts found while surveying, recorded because they shape the design:

- `series/<id>.json` already reserves `presentation`, and
  `series_meta.meta_from_descriptor()` already strips it from `meta`. The browser cannot
  read drawing config from the data file; something must emit it. That is why a
  generator exists at all.
- The workflow publishes `./site` wholesale and `dev.sh` serves it as a plain directory;
  Python's `http.server` serves `.js` as `text/javascript`. Subdirectories and native ES
  modules need no pipeline change.
- Plotly's CDN carries `plotly-basic-2.35.0.min.js` (1.0 MB) beside the full 4.5 MB
  bundle, so a smaller download needs no bundler.

Inputs handed on by S4c: who may call `render` and when; whether the preset row is a
component; nothing drawn in the source-line band; keep or replace the page-level "drawn
on first show" rule. All four are settled in decision 5.

Decided by the user on 2026-09-13: (1) plain ES modules loaded natively plus a stdlib
Python page generator — "no build step" is recorded as "no JavaScript toolchain"
("moving it from a single page build makes it less fragile"); (2) `/` is a curated grid
from `pages/home.json`; (3) the preset row is HTML buttons in the card's control row,
not Plotly's rangeselector; (4) `scripts/fetch_all.py` replaces the per-series workflow
fetch steps now (S6a), not in S11.

## Goals / Non-Goals

**Goals:**
- Adding a standard time-series chart is a config change: one descriptor with a
  `presentation` block, one fetcher, one test, one fixture; no JS, no page file, no
  workflow edit, no nav edit.
- One chart drawn on many pages at different sizes from the same module and config.
- Three page types expressible in a manifest: single chart, grid one-pager with
  click-through, narrative with text between charts.
- The three-section nav (Economy / Markets / Rates & Yields), generated.
- Every rule S4c inherited by accident is now stated: who plots, when, into what.
- Everything S5b needs to theme is a token name, never a literal.

**Non-Goals (explicitly out of scope):**
- Palette values, light mode, the toggle, a Plotly template per mode (S5b defines them;
  this change fixes only the token names).
- Porting any chart or building the generator (S6a/S6b/S7).
- The narrative page type's authoring format beyond an `html` block (Phase 5).
- A smaller Plotly bundle, lazy fetch, a phone layout (measured at S12).
- The source catalogue (S8); nothing here references `catalog/`.
- Changing any fetcher, payload shape, or the `meta`/`as_of` contract.

If any of these turns out to be required to land S6 cleanly, stop and flag it rather
than expanding scope.

## Decisions

### 1. Native ES modules plus a stdlib Python page generator; "no JavaScript toolchain"

One JS module per chart *type* exporting a render contract; per-series config in
`series/<id>.json` `presentation`; pages stamped by `scripts/build_site.py` from
descriptors and `pages/*.json` into a multi-page static `site/`. No npm, no bundler, no
transpiler, no framework; Plotly stays a CDN global loaded by a `<script>` tag. Browsers
load `<script type="module">` files natively, so the code shipped is the code written.

The generator is the same class of thing as the fetchers — Python producing files for
the site inside the workflow that already runs Python — not a bundler. The repo's "no
build step" conviction was written to keep the Node/npm world out; it is recorded from
here on as "no JavaScript toolchain" (`openspec/config.yaml`, the `dashboard-site` spec).

- *Alternative considered — a JS toolchain (Vite/esbuild):* a tree-shaken Plotly, hot
  reload, TypeScript, a component framework, tooling any collaborator knows. Rejected:
  the reuse requirement is met by a render-function contract plus a manifest, neither
  needs a bundler; the one material win (a smaller Plotly) is available without one
  (`plotly-basic` on the same CDN, an S5b/perf item); it adds Node and a lockfile to a
  Python-only workflow and a second language of build failures for a one-person site;
  and ES modules bundle as-is if a toolchain is ever wanted, so the choice is reversible.
- *Alternative considered — no generator; hand-written page shells and a hand-maintained
  manifest:* `presentation` is stripped from the data files by S3's design, so a manifest
  must be emitted by *something*; and a page per series would be a hand-written file,
  which breaks the file-additive rule S7 and S11 depend on. Emitting shells too is ~50
  lines more and gives clean URLs and a static nav that works before JS runs.
- *Kept thin on purpose:* the generator emits the page shell, the nav, one placeholder
  per block, and the blocks' descriptor fields as inline JSON. **Everything inside a card
  is built by JS** (`card.js`). A Python card template plus a JS filler would make every
  chrome change (S5b's toggle, a new stat tile) a two-language edit that must agree on
  element ids.

### 2. Layout on disk: sources committed under `site/`, generated paths ignored

```
series/<id>.json              descriptor + presentation (+ optional "fetcher")     committed
pages/site.json               site name + the three sections (id, label, tagline)    committed
pages/<slug>.json             curated page manifests; home.json → /                  committed
scripts/build_site.py         generator: pages + data copy → site/                   committed
scripts/fetch_all.py          fetch runner (decision 7)                              committed
site/css/site.css             today's CSS, moved verbatim (S5b adds tokens.css)      committed
site/css/charts/<type>.css    optional per-type CSS, linked on every page            committed
site/js/app.js                reads the page's inline JSON, mounts each block        committed
site/js/lib/*.js              shared runtime (decision 5)                            committed
site/js/charts/<type>.js      chart types and custom modules                         committed
site/index.html               GENERATED at cutover (tracked until then)              ignored
site/<section>/index.html     GENERATED                                              ignored
site/charts/<id>/index.html   GENERATED                                              ignored
site/<section>/<slug>/…       GENERATED                                              ignored
site/data/<id>.json           GENERATED (copied from data/)                          ignored
```

`.gitignore` gains two section-agnostic lines, `site/data/` and `site/**/index.html`
(sources are `.css`/`.js`, never `index.html`), added in S6a; tracked files stay tracked
until `git rm --cached` at cutover. The stray `.envrc.DS_Store` line is removed at the
same time. `build_site.py` also does the data copy the workflow and `dev.sh` do today
(it already iterates `series_meta.ids()`), so there is one "assemble `site/`" step and
the deploy dir stays `site/` — `daily-automation`, `staleness.py`'s `LIVE_BASE` and
CLAUDE.md's data-flow prose stay true. Iteration loop after this: edit `site/js` or
`site/css` → reload; edit a descriptor or a manifest → re-run the generator (`dev.sh`
runs it once at start).

- *Alternative considered — commit the generated pages:* reviewable diffs, but every
  parallel agent's branch regenerates them, producing conflicts on exactly the files the
  file-additive rule exists to avoid. The generator's pytest test is the review.
- *Alternative considered — a separate `web/` source tree copied into an ignored
  `site/`:* the slogan "`site/` is output" costs a rebuild on every CSS/JS edit. Ignoring
  only the generated paths gets the same conflict-safety.
- *Migration:* during S6 and S7 the generator writes the new pages under their own paths
  and does **not** write `site/index.html`; the old dashboard stays at `/` until all four
  charts are ported.

### 3. URLs, page types, nav, section placement

| URL | Page type | Source |
|---|---|---|
| `/` | grid, curated | `pages/home.json` (user decision; initially the four charts) |
| `/economy/`, `/markets/`, `/rates/` | grid, automatic: every series whose `presentation.sections` includes the section, sorted by `presentation.order`, blocks at `half` | descriptors |
| `/charts/<id>/` | single chart, full chrome | one per descriptor with `presentation` |
| `/<section>/<slug>/` | grid or narrative, curated | `pages/<slug>.json` — S12's "State of the US Bond Market" |

- Nav, generated statically: top row = site name → `/`, then the three sections; second
  row (on section, chart and composite pages) = that section's charts by `short_title`
  plus its composite pages; current item highlighted; `/` highlights nothing.
- Chart pages live under `/charts/`, not a section, because a series can belong to
  several (the fixed-income conversation's cross-section note); a chart page's second row
  is its first listed section.
- A grid card has the same chrome as the single page (title links to `/charts/<id>/`,
  summary, badge, control row, `Chart | Table | About`, exports); block
  `size ∈ {full, half, third}` sets the chart height by CSS class (`full` 400 px, 300 on
  mobile; `half` and `third` 300). One column under 640 px.
- Narrative layout = one column with `text` blocks between chart blocks. Defined now so
  manifests can express it; built when Phase 5 needs it. Text content is `{ "html" }`.
- A descriptor without `presentation` (USREC) gets no page and no nav entry.

Default placement, all config values:

| Series | Sections | `order` | Why |
|---|---|---|---|
| `dgs10` | rates, economy | 5 | benchmark rate; also the long-history view |
| `sp500_pe` | markets | 7 | valuation measure |
| `yield_curve` | rates | 10 | "what can I earn" |
| `spreads` | economy | 20 | cycle indicator with recession shading |

`order` = roadmap chart number × 10 from chart 3 onward (Fed Funds = 30).

### 4. `presentation` schema and the payload convention

```json
"presentation": {
  "sections": ["rates", "economy"],
  "order": 5,
  "summary": "Daily 10-year Treasury constant-maturity yield, from FRED.",
  "chart": {
    "type": "timeseries",
    "y": { "suffix": "%", "format": ".2f" },
    "presets": ["1M", "6M", "1Y", "5Y", "All"],
    "recessions": false,
    "zeroline": false
  },
  "stats": true,
  "table": { "kind": "recent", "rows": 30 }
}
```

- `type` resolves to `import('/js/charts/<type>.js')`; the generator fails the build if
  the file is missing. Built-in types: `timeseries`, `curve`. A custom module is named
  after its series id (`sp500_pe`).
- **Payload convention for `timeseries`** (no path adapter): a data file with `series`
  (spreads) gives one trace per key, label from `series[k].label`, trace key = the series
  key; otherwise `observations` with `y` field default `"value"`, trace key = the y
  field, label = `meta.short_title`. An optional `traces: [{key, y, label, color}]`
  overrides this for the day a file needs a subset. Colours default to `series-1..n` by
  trace index; only token names are legal.
- `timeseries` options: `y {suffix, format}`; `presets` (grammar `^\d+[MY]$`, `YTD`,
  `All`; absent → no preset row); `recessions` (true → `card.js` fetches
  `/data/usrec.json`, 404-tolerant, and passes the intervals as `ctx.recessions`, which
  the type puts into the initial `layout.shapes`); `zeroline`. Hover x-format derives
  from `meta.cadence` (daily → full date, monthly → `%b %Y`), so the spreads port changes
  its hover from `%b %Y` to the full date — intended, and recorded in its spec. The
  x-axis start is the minimum x over the traces, never `as_of.first_observation` (which
  spreads lacks).
- `curve` options: `overlays: ["1w","1m","1y","5y"]`, `custom_date: true`, `y {suffix}`;
  tenors from `data.tenors`; no presets; `table: true` gives the tenor × change table
  with each resolved comparison date in the column titles; `csv()` is the wide form.
- `stats`: `true | false`; default true for one trace, false for several (spreads has no
  stat tiles today). `timeseries` stats are latest, 1Y high/low, 1Y change, each with
  its resolved date per the `chart-chrome` comparison rule.
- `table`: `false | true | { kind, … }`. `timeseries` kinds: `recent` (last N rows, one
  column per trace, with change) and `changes` (one row per trace: latest, change over
  each of `windows: ["1M","1Y"]` with the resolved "vs" date — today's spreads table).
- `fetcher` (optional, top-level in the descriptor): script name under `scripts/`,
  default `fetch_<id>.py`; `dgs10` sets `"fetcher": "fetch_treasury.py"`. No rename, so
  the four specs and CLAUDE.md that name that script stay true.
- Recession shading on `dgs10` and `sp500_pe` stays **off** in the port (S4c's "do not
  reopen": don't add it unasked); turning it on is now a one-word config edit.

### 5. Component contract, mount lifecycle, presets, band, tokens

`site/js/charts/<type>.js` exports (no module-level mutable state; no
`document.getElementById`; a type may be mounted N times on one page — nominal and TIPS
curves on the Rates page — so everything is scoped to `el` and `ctx.slots`):

```js
export function render(el, ctx)   // called ONCE by mount with el visible and laid out;
                                  // may redraw itself (Plotly.react on el) from its own
                                  // controls; returns { destroy() }
export function stats(ctx)        // optional, pure → [{ label, value, date? }]
export function table(ctx)        // optional, pure → { columns, rows, note? }
export function csv(ctx)          // optional, pure → string; default = outer join of the
                                  // traces on date, columns `date,<key>…`
```

`ctx = { id, data, meta, as_of, presentation, today, theme, variant, recessions,
initialPreset, slots: { controls } }`: `today` is `todayET()` (US-Eastern `YYYY-MM-DD`)
computed once per page; `theme` is the token → value map read from CSS custom
properties; `variant ∈ {full, half, third}`; `recessions` is the interval list or
`null`; `slots.controls` is the card's control row, where the yield curve's toggles and
date picker sit beside the preset buttons. `table().note` carries the P/E's dagger
legend. The P/E's two-input source line stays in `lib/asof.js`, which is already
generic.

**Who calls `render`, and when (S4c inputs 1 and 4).** `site/js/lib/card.js`'s
`mount(block)`:

1. builds the whole card DOM from the block JSON (title link, summary, badge, control
   row, sub-tab strip, chart container, stats, table, About, exports) with "Loading" in
   every panel, so titles show before data;
2. fetches `/data/<id>.json` eagerly at mount (plus `usrec.json` when asked); mount owns
   the error message, and types never write outside `el`/`slots`, so the CSS
   `:empty::before` placeholder keeps working;
3. renders badge, stats, table, About and exports as the fetch resolves, then imports
   the type and calls `render` once — the Chart sub-tab is the default and cards are
   never `display:none`, so the container has width by construction;
4. on return to the Chart sub-tab, `Plotly.Plots.resize`; on a `themechange` event,
   `destroy()` then `render()` (S5b's hook — no contract change needed);
5. applies `initialPreset` through `presets.js` after render.

`mount` is the only code that plots into a card. If a future layout hides cards
(accordion, tabs), `mount` defers — `IntersectionObserver` is the named mechanism — and
types never observe. Eager fetch is kept deliberately (S4c D1): today's five files are
3.7 MB raw, ~0.7 MB gzipped, and the current dashboard already loads all of them; a
section page will hold ~7 charts. Phone load (Areas of Uncertainty #5) is measured at
S12; lazy fetch would be a `mount`-internal change.

- *Alternative considered — the component observes its own container
  (`IntersectionObserver`/`ResizeObserver`):* page-agnostic, but four charts to twenty
  do not earn two observers, and a component that observes cannot be reasoned about
  from its config alone. Ownership sits in one function instead.

**Preset row (S4c input 2): HTML buttons, owned by the card chrome.** `presets.js`
renders `presentation.chart.presets` in the control row and calls `Plotly.relayout` with
explicit `[today − n, today]` ranges; "All" sets `xaxis.autorange: true`, which
`autorangeoptions` already clips to `[first, today]`, so All, reset and double-click
stay in agreement. Active state is tracked on `plotly_relayout` (nothing active after a
drag-zoom). Gains: ~25 px of plot height (Plotly 2.35 draws the selector 19 px tall
plus a 2% pad in the top margin, ~8% of the 320 px plot area), CSS-themeable under S5b,
any range expressible (YTD, per-series defaults), one control row shared with the yield
curve's toggles. Cost ~40 lines.

- *Alternative considered — keep Plotly's rangeselector:* works today (S4c); colours
  could be set from tokens at render time; loses on placement, custom ranges, and it
  appears in PNG exports.

**Source-line band (S4c input 3).** `site/js/lib/plotly-layout.js` is the only file
that sets `margin`, legend position (top, horizontal), `rangeslider` (never) or `height`
(never — height is CSS per variant); it reserves `margin.b` for the source-line
annotation, sets `xaxisToToday` with `autorangeoptions`, and applies axis chrome from
`ctx.theme`. `tests/test_build_site.py` greps every other file under `site/js` for
those keys.

**Theme tokens (the hook for S5b).** S5b runs before S6b and defines
`site/css/tokens.css`, both palettes, a Plotly template per mode and the toggle. The
minimum token set it must define, because the chart types read exactly these names:
`--series-1` … `--series-6`, `--gridline`, `--axis-line`, `--zero-line`,
`--annotation`, `--up`, `--down`, `--recession-fill`, `--legend-bg`, plus the existing
six (`--bg`, `--surface`, `--border`, `--text`, `--text-muted`, `--accent`). `theme.js`
reads them into `ctx.theme`. Should S6b ever run first, it creates the names with today's
hex values and S5b re-values them; names never change. `site/js` contains no hex/rgb
literal — grepped by the test.

`site/js/lib/` (today's shared region, moved and de-duplicated): `card.js`,
`plotly-layout.js`, `presets.js`, `asof.js` (source line, badge text, About HTML),
`dates.js` (UTC helpers, `nearestOnOrBefore`, `valueOnOrBefore`), `export.js`,
`theme.js`, `data.js` (`loadSeries` with **root-relative** `/data/`). Chart types after
S7: `timeseries` (dgs10, spreads; later Fed Funds, breakeven, real rate, credit
spreads, ERP, ultra-long 10Y), `curve` (yield curve; later TIPS), `sp500_pe` (custom:
imports `baseLayout`/`xaxisToToday` from the layout builder; owns the
confirmed/estimated split with the prepended last-confirmed point, the dagger `note`,
the long-term-average stat, the 24-row table and the
`date,pe,price,earnings,estimated` CSV; "dashed where flag" is promoted into
`timeseries` when a second series needs it).

### 6. Page manifest schema

```json
{ "slug": "state-of-the-us-bond-market", "section": "rates",
  "title": "State of the US Bond Market", "layout": "grid",
  "intro": "optional paragraph",
  "blocks": [ { "chart": "yield_curve", "size": "full" },
              { "chart": "spreads", "size": "half", "preset": "10Y" },
              { "text": { "html": "…" } } ] }
```

`blocks[]` is a tagged union: `chart` and `text` are built by S12; `table` and `tile`
(roadmap item 18's "where today sits in history" stat tile) are reserved names, given a
schema when S11e builds them. `home.json` has no `section`. The generator validates every
`chart` against descriptors that carry `presentation` and every `section` against
`pages/site.json`; a block's `preset` reaches the type as `ctx.initialPreset`.

### 7. The file-additive rule, and fetch discovery

Adding a series creates files and edits none: `series/<id>.json` (with `presentation`),
`scripts/fetch_<id>.py`, `tests/test_<id>.py`, `data/<id>.json` (the fixture — run the
fetcher once; tests parametrize over `series_meta.ids()` and use the `load_data(id)`
fixture, never a new named fixture in `conftest.py`), and — only for a new chart type —
`site/js/charts/<type>.js` with an optional `site/css/charts/<type>.css`. Everything
shared is derived: nav, section pages, the chart page, the data copy, the seed step,
the fetch step. Curating a series onto `/` or a composite page is a separate human edit
to `pages/*.json`. Expected and harmless: `pytest -m staleness` against the live site
404s on a new id until its first deploy.

**`scripts/fetch_all.py`** runs each descriptor's `fetcher` (default `fetch_<id>.py`) as
a subprocess inside a `::group::` with elapsed time, try/except per series, and writes
`data/fetch_status.json` (`{id: {ok, returncode, seconds}}`), always exiting 0. The
step-summary and the final fail-after-deploy step read that file instead of
`steps.<id>.outcome`. One workflow step replaces five plus their two per-series lines;
semantics unchanged: seed → fetch what you can → gate on `pytest -m "not staleness"` →
staleness report → build → deploy → fail afterwards. Secrets masking is runner-level
and unaffected.

- *Alternative considered — leave the per-series YAML:* a three-place edit per series is
  a real merge conflict between parallel agents, and S7 would rehearse every fan-out
  constraint except that one. Cost of the runner: per-step timings in the Actions UI
  become printed elapsed times.
- *Alternative considered — rename `fetch_treasury.py` to `fetch_dgs10.py` instead of a
  `fetcher` key:* touches four specs, CLAUDE.md and the workflow for no behaviour change.

### 8. Tests and done-checks

- `tests/test_build_site.py`: build into `tmp_path`; every descriptor with
  `presentation` → `charts/<id>/index.html`; section pages list their charts in `order`;
  page manifests resolve; the inline page JSON parses; each data file has the payload
  shape its type expects (`series` or `observations`; `tenors` for `curve`); every `type`
  module and `fetcher` script exists; no hex/rgb literal in `site/js`; no
  `margin`/`rangeslider`/`height`/`getElementById` outside `plotly-layout.js` and
  `card.js`.
- `tests/test_series_metadata.py`: `presentation` schema (allowed keys, enums, presets
  grammar, `sections` ⊆ `pages/site.json`, `fetcher` exists when given).
- The browser check (Claude in Chrome) remains the JS verification: each page on
  **first** show, `_fullLayout.width === clientWidth`, zero console errors, All/reset
  ranges, and a screenshot against today's tab for each ported chart.

### 9. Spec decomposition and ownership

- **`chart-components` NEW** — the render contract, `ctx`, chart types and options, the
  `presentation` schema and payload convention, the mount lifecycle, the preset row, the
  band rule, token names, the no-literal and no-module-state rules.
- **`site-build` NEW** — the generator's inputs and outputs, the URL scheme and nav, page
  manifests, ignored generated paths, the file-additive rule, `fetch_all.py`, the tests.
- **`dashboard-site` MODIFIED** — "Single-file static dashboard", "Tabbed navigation
  across series", "Default tab on page load" and "Data fetched on page load, not lazily"
  are REMOVED (the repo's first REMOVED blocks, with Reason and Migration) and replaced
  by ADDED "Generated multi-page static site with no JavaScript toolchain", "Section
  navigation" and "Cards fetch at mount and plot into a visible container"; "Dark theme
  and per-tab data loading", "Fetch failure surfaces an error message" and "Minimal
  mobile breakpoint" are MODIFIED; "Plotly loaded from CDN, not bundled" and "Loading
  placeholder" are unchanged.
- **`chart-chrome` MODIFIED** — "In-chart source line", "About tab", "Time-series x-axis
  ends at today", "Export buttons".
- **`series-metadata` MODIFIED** — "Series descriptor file", "Header contract of meta,
  as_of and payload".
- **`daily-automation` MODIFIED** — all five requirements name per-series steps.
- **The four series specs** — each "Tab label …" (and "Treasury Spreads tab") is REMOVED
  and an ADDED "Section placement and chart type …" takes its place; the chart
  requirements are MODIFIED where they said "tab".
- **`data-freshness`, `data-pipeline`, `nber-recession-data` unchanged.**
- **`openspec/config.yaml`** — hand edit: context line and the conviction wording.

Every MODIFIED block copies the whole requirement under a byte-identical header, because
the validator checks only shape and a partial block is silently truncated at archive.

## Risks / Trade-offs

- **The generator breaks and the daily deploy ships nothing.** → `tests/test_build_site.py`
  runs the generator into a temp dir inside the gating `pytest` step, before the deploy.
- **Seven eager Plotly charts on a section page are slow on a phone.** → Measured at
  S12 (Areas of Uncertainty #5); lazy fetch is a change inside `mount`, not to any type.
- **Two mounts of one type on a page share state by accident.** → The no-module-state
  rule, enforced by the `getElementById` grep and by review of the curve port.
- **`themechange` re-render drops the user's zoom.** → Accepted; the toggle is rare and
  the alternative (relayout every colour) couples `card.js` to every type's internals.
- **A drag-zoom leaves no preset active.** → Intended; documented in `chart-components`.
- **`Plotly.relayout` "All" lands on the padded extent.** → `autorangeoptions` clipping
  was verified in S4c for `step: 'all'`, which sets the same `autorange: true`.
- **Old `site/index.html` and the new `site/js`, `site/css` coexist until cutover.** →
  The old file references neither; the generator never writes `site/index.html` until
  `pages/home.json` exists.
- **`site/**/index.html` also matches the still-tracked `site/index.html`.** → Tracked
  files stay tracked regardless of ignore rules; the cutover `git rm --cached` is the
  only step that changes that.
- **`fetch_all.py` hides which series was slow.** → `::group::` per series with printed
  elapsed seconds, and `fetch_status.json` records them.
- **Custom module name collides with a built-in type.** → The generator rejects a
  descriptor whose id is `timeseries` or `curve`.

## Migration Plan

S5b first (tokens; independent of this change's Python half), then S6a (generator,
runner, tests, workflow — the old `/` untouched and still deployed), then S6b (runtime
and the `timeseries` type; `/charts/dgs10/` and `/rates/` render beside the old
dashboard), then S7 (three agents port spreads, P/E and the yield curve; a verifier
builds, tests and screenshots every page), then one human session for cutover:
`pages/home.json`, `git rm --cached site/index.html site/data/*.json`, verify `/`, and
the docs pass (CLAUDE.md, ARCHITECTURE.md decision log, `HOW-IT-WORKS.md` rewrite).
Rollback at any point before cutover: revert that session's commit; the deployed site is
unaffected because the old file was never touched. Rollback after cutover: restore
`site/index.html` from `a0154df` and delete `pages/home.json`.

## Open Questions (handed on, not blocking)

1. **S5b** — token values for both palettes, the toggle, and whether the Plotly template
   per mode lives in `theme.js` or a JSON the generator inlines.
2. **S12** — phone load time on the first composite page; if slow, lazy fetch inside
   `mount`, and whether grid tiles should be static PNGs with the live chart one click
   away.
3. **Phase 5** — the narrative page's authoring format (markdown needs a Python
   dependency; `html` blocks need none).
4. **S11e** — schemas for the `table` and `tile` block types.
5. **Perf, any session** — swapping the Plotly `<script>` to `plotly-basic-2.35.0` if
   no chart needs a trace type outside it.
