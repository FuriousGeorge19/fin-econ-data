# Architecture Planning — Evolution Roadmap

This document tracks anticipated architectural changes as the site grows from a
handful of charts toward the full vision described in
`reference_resources/fixed-income-charts-conversation.md`.

---

## Current Architecture

**See `CLAUDE.md`'s Architecture section for the up-to-date description** — this
document tracks the *evolution*, not the current state, and the diagram that used to
live here (a single `site/index.html`, one tab per series) was retired by the
`s5-chart-components` rebuild (S6a→S7c, 2026-09-13–14; see the Decision Log). In
short, as of 2026-09-14: `series/<id>.json` descriptors carry a `presentation` block,
`scripts/build_site.py` generates a multi-page site from them plus `pages/*.json`
manifests, and `site/js/charts/<type>.js` modules do the actual drawing — Sections 5
and 6 below, "Frontend: Splitting index.html" and "Navigation: Section-Based
Grouping," are both marked done rather than rewritten in place, so the reasoning
that led there stays intact.

The notes below describe when and why each remaining piece will need to evolve.

---

## Planned Charts (from fixed-income-charts-conversation.md)

| # | Chart | Key Data | Status |
|---|-------|----------|--------|
| 1 | Yield curve snapshot with overlays | DGS series (11 tenors) | **Done** |
| 2 | 10y-2y and 10y-3m spreads + recession shading | GS10, GS2, TB3MS, USREC | **Done** |
| 3 | Fed Funds rate, long history | FEDFUNDS, USREC | Planned |
| 4 | 10-year nominal yield, ultra-long (1871+) | GS10 + Shiller long bond | Planned |
| 5 | Ex-post real short rate (3mo − CPI) | TB3MS, CPIAUCSL, USREC | Planned |
| 6 | Breakeven inflation (10yr) | T10YIE | Planned |
| 7 | Equity risk premium | S&P earnings yield, DFII10, USREC | Planned |
| 8 | Credit spreads (IG + HY OAS) | BAMLC0A0CM, BAMLH0A0HYM2, USREC | Planned |
| 9 | Multi-tenor time series (selectable) | DGS series (already fetched) | Planned |
| 10 | TIPS real yield curve snapshot | DFII5/7/10/20/30 | Planned |

---

## Evolution Triggers and Plans

### 1. Shared FRED Fetch Utility

**When:** Charts 2–3 (next up). Multiple scripts will need FRED API calls with
identical boilerplate (URL construction, error handling, "." filtering, rate
limiting).

**What to do:** Extract a `scripts/fred_utils.py` module with a `fetch_series(series_id, limit)` function. Each fetch script imports it. The yield curve script already has this pattern internally — generalize it.

**Also consider:** A single `scripts/fetch_fred_series.py` that takes a config
dict of series IDs and outputs them all to one JSON file. Many of the planned
charts pull from overlapping FRED series (USREC is needed by 5+ charts, GS10
appears in multiple contexts). A unified fetch could:
- Reduce API calls (fetch each series once even if used by multiple charts)
- Produce a single `data/fred_series.json` keyed by series ID
- Simplify the workflow (one fetch step instead of many)

Trade-off: a monolithic fetch is less modular. A middle ground is one fetch
script per *chart group* (e.g., `fetch_rates_history.py` fetches FEDFUNDS +
GS10 + TB3MS + USREC together since they're all used in the rates/economy
charts).

### 2. Recession Shading as Shared Data

**When:** Chart 2 (spreads). USREC is used on charts 2, 3, 5, 7, 8.

**What to do:** Fetch USREC once (in whatever script runs first, or in a
dedicated shared-data fetch), output to `data/usrec.json`. Build a shared
JavaScript function `addRecessionBands(plotDiv, usrecData)` that overlays
shaded rectangles on any Plotly chart. This avoids duplicating recession
shading logic across 5+ chart renderers.

### 3. Derived / Computed Series

**When:** Chart 2 (spreads), chart 5 (real rate), chart 7 (ERP).

**What to do:** Compute derived series in Python at fetch time, not in
JavaScript at render time. Reasons:
- Date alignment across series with different frequencies/gaps is easier in
  pandas than in vanilla JS
- Keeps the frontend simple (just plot what's in the JSON)
- Computed series can be inspected and debugged in the JSON files

Pattern: a fetch script pulls its input series, computes the derived series,
and outputs a single JSON file with the result. For example,
`fetch_spreads.py` fetches GS10, GS2, TB3MS, computes 10y-2y and 10y-3m
spreads, and writes `data/spreads.json`.

### 4. Historical Stitching (Pre-1953 Data)

**When:** Chart 4 (ultra-long 10yr) and chart 5 (real short rate back to 1930s).

**What to do:** These charts need Shiller's historical data stitched with FRED
monthly series stitched with FRED daily series. The JSON output should carry
per-observation metadata:
```json
{
  "date": "1925-01-01",
  "value": 3.86,
  "source": "shiller",
  "frequency": "monthly"
}
```
This lets the frontend optionally display source transitions or show a tooltip
note like "Monthly observation (Shiller)". The conversation doc recommends
assigning monthly data to the 1st of the month and letting visual gaps
communicate frequency — no upsampling.

Shiller's data can be fetched from his Excel file at Yale (similar to how
`fetch_sp500_pe.py` already does it — that script already pulls Shiller data).
Factor out Shiller fetching into a shared utility if multiple charts need it.

### 5. Frontend: Splitting index.html — **Done 2026-09-14** (`s5-chart-components`)

Landed as a full generated-multi-page-site rebuild rather than the lighter options
below — see the Decision Log entry for why the design went further than "split into
files." `site/index.html` no longer exists; each chart is `site/js/charts/<type>.js`
plus a `presentation` block in `series/<id>.json`, assembled by `scripts/build_site.py`
into `site/charts/<id>/index.html` and the section pages.

**When:** Around 5–6 tabs (charts 2–4 timeframe).

**What to do:** The current `index.html` is ~600 lines. Each new chart adds
~100–150 lines of JS. At 8+ charts it will be 1500+ lines — manageable but
increasingly hard to navigate.

Options (in order of simplicity):
1. **Split JS into separate files** — one `<script src="js/yieldcurve.js">`
   per chart. HTML stays as one file. No build step needed. Easiest migration.
2. **Split into separate HTML pages** — one page per section (Economy, Markets,
   Rates). Shared CSS via a linked stylesheet. More modular but loses the SPA
   feel.
3. **Introduce a minimal build step** — e.g., a simple concatenation script or
   esbuild for JS modules. Only if complexity justifies it.

Recommendation: option 1 first. It's a 30-minute refactor and buys a lot of
headroom.

### 6. Navigation: Section-Based Grouping — **Done 2026-09-14** (`s5-chart-components`)

The three sections below are exactly what shipped: `pages/site.json` names them
(`economy`, `markets`, `rates`), each descriptor's `presentation.sections` places it
on one or more, and `scripts/build_site.py` generates `/economy/`, `/markets/`,
`/rates/` automatically, sorted by `presentation.order`. `dgs10` is the one series on
two sections (rates and economy) — the cross-section case this section anticipated.

**When:** Around 6–8 charts, when flat tabs become unwieldy.

**What to do:** The planning conversation outlines three sections organized by
analytical question, not asset class:

- **Economy** — spreads, Fed Funds, real rates, recession indicators. "Where
  are we in the cycle?"
- **Markets** — equity risk premium, credit spreads, cross-asset valuation.
  "How is risk priced?"
- **Rates & Yields** — yield curve snapshot, TIPS curve, current rates. "What
  can I earn?"

Implementation: section headers in the nav with sub-tabs, or a two-level nav
(top = section, second row = charts within section). Some series appear in
multiple sections with different presentations — this is intentional (same data,
different analytical context).

### 7. Data Size and Performance

**When:** Ongoing concern as series accumulate.

**Current state:** `yield_curve.json` is 1.4 MB (11 tenors × 6000 days). Adding
10+ more FRED series at similar depth could push total data load to 5–10 MB.

**Mitigation options:**
- **Lazy loading** — only fetch data for the active tab. Currently all three
  JSON files load on page open. Switch to loading on tab click.
- **Compression** — GitHub Pages serves gzip. JSON compresses well (~80%
  reduction). Already happening transparently.
- **Truncation** — some charts don't need 25 years of daily data on first load.
  Could serve a "recent" slice and load full history on demand.
- **Data format** — if JSON size becomes a real problem, switch to CSV (much
  more compact for tabular data) or a columnar JSON format (`{dates: [...],
  values: [...]}` instead of `[{date, value}, ...]`).

Not a problem yet. Monitor as we add charts.

### 8. Workflow Execution Time

**When:** 8+ fetch scripts.

**Current state:** The workflow runs scripts sequentially. Each FRED API call
takes 1–3 seconds. With 11 series in the yield curve script, that's ~15–30
seconds for that step alone.

**Mitigation:** Run independent fetch scripts in parallel in the workflow using
`&` and `wait`, or use a single Python script that fetches all FRED series
concurrently with `concurrent.futures`. GitHub Actions has a 6-hour timeout so
this isn't urgent, but faster runs mean faster deploys after manual triggers.

### 9. The 100+ Series Regime (Scale Tipping Point)

**When:** If the catalog ever grows from a handful of charts toward ~100–200
series. This is a different regime from everything above — Sections 1–8 are
tuned for the ~10-chart roadmap, where each trigger is a modest convenience.
Past ~50 series, three of those conveniences become *mandatory* and one new
constraint appears that doesn't exist at small scale.

Importantly, **update latency is not the bottleneck here.** The daily run is
dominated by fixed costs (runner spin-up, Python setup, Pages rebuild — ~1 min
total) that don't scale with series count. Going from 3 to 200 series moves the
total run from ~1–2 min to maybe ~3–6 min. The 6-hour Actions limit is never in
sight. The real walls are correctness (rate limits) and authoring effort
(hand-written code), not speed.

**What changes, and why:**

1. **Config-driven becomes mandatory, not optional.** Section 1 frames a
   config-dict fetcher as something to "also consider," and leans toward
   per-chart-group scripts instead. That trade-off flips past ~50 series:
   maintaining 150 near-identical `fetch_*.py` files is untenable. The series
   list becomes pure data —
   ```python
   SERIES = [
       {"id": "DGS10",    "title": "10-Year Treasury", "limit": 2520},
       {"id": "UNRATE",   "title": "Unemployment Rate", "limit": 900},
       # ...one row per series...
   ]
   ```
   — and a single generic fetcher loops over it. Adding series #150 is a
   one-line edit, not a new file. (Series with bespoke logic — e.g.
   `fetch_sp500_pe.py` with its Excel earnings overrides — stay separate; the
   config-driven path is only for series fetched the *same* way.)

2. **Rate-limit-awareness becomes a real requirement.** At small scale this is
   irrelevant — the current ~13 calls are far under any ceiling, which is why
   Section 1 only mentions "rate limiting" in passing. But FRED caps requests at
   roughly **120 per minute**. A "series" is not one call: the yield curve tab
   alone is 11 tenors, so 150–200 series can mean **300–500+ API calls**. Fired
   naively in parallel, FRED starts returning `429 Too Many Requests` and
   fetches fail. The fetcher must:
   - pace requests to stay under ~120/min (a throttle / token bucket), and
   - on a `429`, **back off and retry** rather than crash.

3. **Parallel and rate-limiting are in tension — balance them.** Section 8
   treats parallelism as a pure speed win, which it is at small scale. At 100+
   series it collides with the rate limit: parallelism wants maximum
   concurrency, rate-limiting says "but not faster than 120/min." The target is
   not max parallelism — it's "several requests in flight at once, *throttled*
   to stay under the ceiling." These two are a single design problem, not two
   independent optimizations.

4. **The frontend must become generated, not hand-authored.** Sections 5–6
   assume each chart is hand-written and the work is *organizing* that code.
   Past ~50 tabs that assumption breaks: nobody hand-writes 150 tabs. The
   frontend would instead **generate** tabs and charts from a manifest (the same
   config that drives fetching, or a sibling of it), rendering a standard
   chart/table per series and only special-casing the genuinely custom ones.
   This is the step from "split the hand-written code into files" to "stop
   hand-writing each chart." Lazy-loading per tab (Section 7) is a hard
   requirement in this regime — never fetch 150 JSON files on page open.

**Net:** if this scale ever arrives, the first thing to change is the *fetch
layer* — move to a config-driven, rate-limit-aware, throttled-parallel fetcher —
for reasons of FRED's limits and authoring effort, not latency. The frontend
follows by becoming manifest-driven. None of this is worth doing below a few
dozen series; the current "one script each, run in a row" approach is correct
until the numbers force the change.

---

## Decision Log

Decisions made during implementation that future work should be aware of:

- **Categorical x-axis for yield curve** (2026-04-01): Yield curve snapshot uses
  evenly spaced tenor labels (Bloomberg convention) rather than linear or log
  maturity scale. This is the industry standard because the curve represents
  discrete instruments, not a continuous function, and gives equal visual weight
  to the information-dense short end.

- **All data on a daily timeline** (2026-04-01): Per the planning conversation,
  monthly historical data is assigned to its original date (1st of month).
  Gaps communicate frequency changes naturally. No upsampling.

- **Python for computation, JS for display** (2026-04-01): Derived series
  (spreads, real rates) should be computed in Python fetch scripts, not in
  browser JavaScript. Keeps the frontend simple and makes the JSON files
  self-contained and debuggable.

- **Header contract: one descriptor per dataset, `meta` + `as_of` + payload**
  (2026-09-13, `s3-series-metadata`): every `data/<id>.json` embeds its
  hand-maintained `series/<id>.json` descriptor verbatim under `meta` and a
  runtime `as_of` block (`fetched_at`, `last_observation`, `period_label`,
  `due_by`, and per-input/per-series breakdowns for multi-input or
  multi-series datasets) computed by `scripts/series_meta.py`. Retired the
  single top-level `last_updated` string once the frontend (S4b) stopped
  reading it. Payload shapes (`observations`, `series`, `recessions`,
  `tenors`) are unchanged. This is also now the single source of the site's
  file list: `scripts/dev.sh`, the workflow's seed/copy steps and
  `scripts/staleness.py` all derive their file lists from `series/*.json`
  rather than each hand-copying it.

- **Freshness judged by a business-day `due_by`, computed in Python, compared
  in the US Eastern date** (2026-09-13, `s3-series-metadata`): replaced the
  old five-integer staleness table with a calendar-aware rule —
  `due_by = period_end(last_observation)` advanced one cadence step plus the
  descriptor's `publication_lag_business_days`, using a hand-rolled US
  bond-market business-day calendar (federal holidays by rule, Good Friday
  always treated as closed, plus an `extra_closures` list). Python computes
  `due_by` at fetch time; the browser only compares it against
  `toLocaleDateString('en-CA', {timeZone: 'America/New_York'})` — no
  business-day arithmetic in JS, so freshness stays correct even if the
  pipeline stops running entirely. A dataset's `due_by` rolls up to the
  earliest `due_by` among its `required`, `active` inputs; an input marked
  `status: discontinued` (the P/E's earnings input, as of 31 Jan 2026) is
  excluded from the roll-up and is stated in the UI rather than alarmed.

- **Workflow failure policy: seed from `gh-pages`, deploy what succeeded, fail
  the job after the fact** (2026-09-13, `s3-series-metadata`): rejected both
  the prior all-or-nothing model (one FRED hiccup froze every series with no
  badge) and committing fetched data back to `main` (the strongest case —
  fresh local data via `git pull` — didn't justify ~250 bot commits/year and a
  rebase step, since `gh-pages` already holds the daily history and
  `scripts/dev.sh --live` covers local freshness). Instead: seed each
  `data/<id>.json` from the live `gh-pages` copy before fetching, run each
  fetch with `continue-on-error`, gate the deploy only on
  `pytest -m "not staleness"` (a *wrong* number still blocks; a *late* one
  doesn't), always deploy, then fail the job afterward if any fetch failed so
  GitHub still notifies without delaying the site update. `main`'s
  `data/*.json` are now explicitly test fixtures, not the deploy history.

- **Charts draw on first show; All/reset = first observation → today; no range
  slider** (2026-09-13, `s4c-chart-chrome-fixes`): three of the four charts had
  been drawn while their tab was `display:none`, and Plotly sizes a hidden
  container to a 700px fallback that it remembers on the chart's config context
  (`_hasZeroWidth`, OR'd, sticky). `site/index.html` now defers each Plotly draw
  until its tab is first shown (`renderWhenVisible`/`onTabShown`) and refits with
  `Plotly.Plots.resize` on later shows; the data fetch and the non-chart chrome
  stay eager. Plotly's rangeselector buttons cannot express a custom range
  (`method`/`args` are updatemenus attributes and are ignored), so "All" is
  `step: 'all'` and `xaxis.autorangeoptions {clipmin, clipmax, include}` pins
  autorange to `[first_observation, today]`; the mode-bar reset and double-click
  land there too. The range slider was removed rather than moving the source line
  under it: the line was already placed correctly without it, the plot area grows
  ~60px, and the slider's own padded extent (to 2035 on the P/E, from the marker
  trace's 5% autorange pad) was how the axis could wander past today. Inputs for
  S5: the component contract must say when `render` may run; the preset row is a
  component question (Plotly's button colours are layout literals, which collides
  with S5b's tokens); the source line owns the bottom-margin band.

- **Theme token set frozen; dark values are an extraction, light is new**
  (2026-09-13, `s5b-theme-tokens`): `site/css/tokens.css` defines all 20 tokens
  `s5-chart-components` names (the existing six plus `--series-1..6`,
  `--gridline`, `--axis-line`, `--zero-line`, `--annotation`, `--up`, `--down`,
  `--recession-fill`, `--legend-bg`) for both a light and a dark palette. Dark
  values are copied verbatim from `site/index.html`'s pre-existing literals — a
  deliberate non-redesign, confirmed pixel-identical by screenshot — because
  `s5-chart-components` design.md commits to that: whichever of S5b/S6b lands
  first, dark keeps today's hex and the other session only adds what's missing.
  Light values and two new series slots (`--series-5`/`--series-6`, unused until
  now) are genuinely new, sourced from the "dataviz" skill's validated palette and
  checked with its `validate_palette.js` against this site's own surfaces rather
  than picked by eye; the skill's stock "yellow" categorical slot was tried first
  and discarded when it failed the normal-vision-separation check against the
  frozen orange (`--series-3`), a red passed instead. `getTheme()` — reading the
  tokens via `getComputedStyle` — is explicitly provisional scaffolding for
  `site/js/lib/theme.js`, an S6b deliverable that doesn't exist yet; building it
  now would sit on module structure S6a/S6b haven't created. A `themechange`
  redraw goes through the existing `renderWhenVisible`, not a direct
  `Plotly.newPlot`, so a chart hidden during a toggle can't reproduce S4c's 700px
  fallback. Also fixed: `nav button` (no filter) would have wired the new toggle
  button into tab-switching; narrowed to `nav button[data-tab]`.

- **Generated multi-page site replaces the single-file dashboard; component
  contract for chart types** (2026-09-13–14, `s5-chart-components`, five sessions:
  S5 design, S6a Python half, S6b JS half, S7 the other three charts, S7c cutover):
  Section 5's "split index.html into files" and Section 6's "section-based nav"
  were both subsumed into a larger rebuild rather than done as the smaller steps
  either section originally described, because `series/<id>.json` already reserved
  a `presentation` block (S3) that nothing read — a generator had to exist regardless,
  and once it does, per-page files and per-section nav come for free rather than as
  separate migrations. `scripts/build_site.py` (stdlib Python, no templating
  library) reads every descriptor's `presentation` and every `pages/*.json`
  manifest and writes `site/charts/<id>/`, `site/<section>/` (automatic grids sorted
  by `order`), and curated pages (`pages/home.json` → `/`); it fails the build,
  naming the file, on a malformed `presentation`, a missing chart-type module, or an
  unresolved manifest reference — this runs inside the gating `pytest` step, so a
  broken generator cannot ship an empty deploy. `site/css/` and `site/js/` are
  committed sources; every other path under `site/` is generated and gitignored.
  Chart types are ES modules in `site/js/charts/` exporting `render(el, ctx)` plus
  optional pure `stats`/`table`/`csv`; `site/js/lib/card.js`'s `mount(block, today)`
  is the only code that plots into a card, and `site/js/lib/plotly-layout.js` is the
  only file allowed to set Plotly `margin`, legend position, a range slider, or a
  chart height — both enforced by greps in `tests/test_build_site.py`, not just
  convention. `scripts/fetch_all.py` replaced five per-series workflow steps (and
  their three-place-edit conflict risk for parallel agents) with one runner that
  catches failures into `data/fetch_status.json`. Adding a series with an existing
  chart type is now genuinely file-additive: a descriptor, a fetcher, a test fixture
  — no shared file touched, verified in practice by S7's three-agent parallel port
  (spreads by config only; `sp500_pe` and `curve` as new modules) hitting zero
  merge conflicts. One deviation from the general design surfaced during S7's
  verification and was fixed in the same session, not deferred: `timeseries.js`'s
  hover text had been built through Plotly's own `%{y:<format>}`/`%{x}` templating,
  which doesn't accept the repo's `"+.2f"` forced-sign convention and defaults to a
  zoom-adaptive date format rather than a fixed one — both replaced with
  precomputed per-point hover text once a second chart (`spreads`) exercised a code
  path `dgs10` alone never had. Cutover (S7c): `pages/home.json` curates the
  original four charts onto `/`; `git rm --cached site/index.html site/data/*.json`
  stopped tracking the now-generated files (both were already gitignored going
  forward, per S6a's `.gitignore` change — untracking is what actually stops
  git from following them). Rollback before cutover was one commit's revert at any
  point, because the old `site/index.html` was never touched until this step;
  rollback after cutover is restoring that file from its last commit before the
  `git rm --cached` and deleting `pages/home.json`.

- **Source catalogue: one file per rights holder, resolved into `meta` at fetch
  time** (2026-09-14, `s8-source-catalog`): `catalog/sources/<slug>.json` records
  each source's access, terms (status + verbatim quote + page URL) and datasets
  (topics, native cadence, coverage, lag, status), with `via: fred` for data whose
  bytes come from FRED but whose terms belong to someone else (S&P's index level;
  ICE BofA later). The boundary rule — a dataset gets its own file only when its
  terms differ from its host's or the publisher serves it directly — keeps
  `fred.json` from becoming a shared file every provider-terms task edits, so a
  workflow agent adding a source adds one file and runs
  `python3 scripts/catalog.py check <path>` on it alone. Descriptors' `sources[]`
  became references (`{slug, dataset?, url?, note?}`); `series_meta.
  meta_from_descriptor()` resolves them when a fetcher runs, so the About tab
  shows the catalogue's licence sentence, hosting note and terms status without
  the browser ever fetching the catalogue — a correction ships on the next fetch.
  Chosen over the browser fetching `/data/catalog/` (a second fetch per card and
  the join logic in JS) and over a `catalog/datasets/` directory (file-additive but
  a join for every read). The validator is a stdlib script, the schema's authority,
  not a JSON-Schema dependency; it checks shape, while the research workflow's
  verifier checks evidence (`read_from` on every fact block). The catalogue is not
  published on the site — not now rather than never.
