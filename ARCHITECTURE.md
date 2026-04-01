# Architecture Planning — Evolution Roadmap

This document tracks anticipated architectural changes as the site grows from a
handful of charts toward the full vision described in
`reference_resources/fixed-income-charts-conversation.md`.

---

## Current Architecture (as of 2026-04-01, 3 tabs)

```
scripts/fetch_<name>.py   →   data/<name>.json   →   site/data/<name>.json
                                                          ↓
                                              site/index.html (single file,
                                              all CSS + JS + HTML inline)
```

- One independent Python script per data source
- One JSON file per data source
- One monolithic `index.html` with all chart/table rendering inline
- GitHub Actions workflow calls each script sequentially, copies JSON, deploys

This works well at the current scale. The notes below describe when and why
each piece will need to evolve.

---

## Planned Charts (from fixed-income-charts-conversation.md)

| # | Chart | Key Data | Status |
|---|-------|----------|--------|
| 1 | Yield curve snapshot with overlays | DGS series (11 tenors) | **Done** |
| 2 | 10y-2y and 10y-3m spreads + recession shading | GS10, GS2, TB3MS, USREC | Planned next |
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

### 5. Frontend: Splitting index.html

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

### 6. Navigation: Section-Based Grouping

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
