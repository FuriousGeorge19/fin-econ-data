# How joemirza.com Works — Complete Technical Explanation

This document explains every piece of the system end-to-end: how data is fetched, how
the site is generated, how it deploys, how the daily automation works, and how DNS
routes your domain to the live site.

*Rewritten 2026-09-14 for the `s5-chart-components` rebuild (S6a→S7c) — the site is no
longer a single HTML file. If you're looking for the version that described the
original March 2026 single-series dashboard, it's in git history before this date.*

---

## Table of Contents

1. [Overview](#overview)
2. [The Data Pipeline](#the-data-pipeline)
3. [The Site Generator](#the-site-generator)
4. [The Frontend Runtime](#the-frontend-runtime)
5. [GitHub Actions — Daily Automation](#github-actions--daily-automation)
6. [GitHub Pages — Hosting](#github-pages--hosting)
7. [DNS and Custom Domain](#dns-and-custom-domain)
8. [HTTPS / SSL Certificate](#https--ssl-certificate)
9. [What Happens When Someone Visits joemirza.com](#what-happens-when-someone-visits-joemirzacom)
10. [What Happens Every Weekday Evening](#what-happens-every-weekday-evening)
11. [Project File Structure](#project-file-structure)
12. [How to Add a New Data Series](#how-to-add-a-new-data-series)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The site is a **static website** — no server, no database, no backend application. It
is a set of generated HTML pages plus JSON data files, served directly by GitHub's
free hosting service (GitHub Pages).

A **GitHub Actions workflow** runs on a schedule (weekday evenings). It fetches fresh
data for five datasets from three different sources, runs the correctness test suite,
**generates the site** from that data plus a set of hand-maintained descriptors, and
deploys the result to GitHub Pages.

The key structural idea, carried over from the original build and sharpened by the
rebuild: **data fetching** (Python, runs in GitHub's cloud) is separate from **how a
chart is drawn** (a JS module in the visitor's browser), which is separate again from
**which pages exist and what's on them** (a Python generator, reading JSON config).
Three layers, each replaceable without touching the other two.

---

## The Data Pipeline

### Five datasets, one shape

| id | Source | Cadence | Fetcher |
|---|---|---|---|
| `dgs10` | FRED (DGS10) | Daily | `scripts/fetch_treasury.py` |
| `sp500_pe` | Shiller/Yale + S&P Global + FRED (SP500) | Monthly | `scripts/fetch_sp500_pe.py` |
| `yield_curve` | FRED (DGS1MO–DGS30, 11 tenors) | Daily | `scripts/fetch_yield_curve.py` |
| `spreads` | FRED (DGS10, DGS2, DGS3MO), computed | Daily | `scripts/fetch_spreads.py` |
| `usrec` | FRED (USREC) | Monthly, collapsed to intervals | `scripts/fetch_usrec.py` |

Each fetcher is a standard Python script — four of the five use only the standard
library; `fetch_sp500_pe.py` also needs `pandas`, `xlrd` and `openpyxl` to read
Shiller's Excel file and the S&P Global earnings workbook. None of the scripts import
each other's business logic directly, but `fetch_spreads.py`, `fetch_yield_curve.py`
and `fetch_treasury.py` all share `scripts/fred_utils.py` for the actual FRED API call
(URL construction, the `FRED_API_KEY` env var, `"."`-as-missing filtering, retry).

### The descriptor: `series/<id>.json`

Every dataset has a hand-maintained descriptor at `series/<id>.json` — this is the
single source of truth for its metadata, and (since the rebuild) for whether and how
it gets a page on the site. A descriptor holds:

- **Identity and metadata**: `id`, `title`, `short_title`, `kind`, `units`, `cadence`,
  `publication_lag_business_days`, `revisions`/`revision_note`, `source_line`,
  `sources` (references into the source catalogue — `{slug, dataset?, url?, note?}`;
  the name and licence come from `catalog/sources/<slug>.json` at fetch time, see
  [The source catalogue](#the-source-catalogue) below), `inputs` (one entry per
  underlying series or input, with its own cadence/lag/status and optionally the
  catalogue `dataset` it draws on), `methodology` (paragraphs), `notes` (paragraphs).
- **`fetcher`** (optional): the script name under `scripts/`, if it doesn't match the
  default `fetch_<id>.py`. Only `dgs10` needs this (`fetch_treasury.py` predates the
  id-based naming convention).
- **`presentation`** (optional): controls whether the dataset gets a page at all, and
  if so, where and how. See [The Site Generator](#the-site-generator) below. `usrec`
  has no `presentation` — it's a data-only dataset, consumed by other charts'
  recession shading but with no page of its own.

`scripts/series_meta.py` provides `ids()` (every descriptor id) and `load(id)` (the
parsed descriptor) to every fetcher and to the test suite, so nothing hand-maintains a
second copy of "which five datasets exist."

### What a fetcher writes: `data/<id>.json`

Every fetcher writes `meta` + `as_of` + a payload, computed by
`scripts/series_meta.py`'s `build_as_of(...)`:

```json
{
  "meta": { "...the descriptor, verbatim, minus presentation and fetcher..." },
  "as_of": {
    "fetched_at": "2026-09-14T23:41:00Z",
    "last_observation": "2026-09-11",
    "period_label": "11 Sep 2026",
    "first_observation": "2017-01-13",
    "observation_count": 2416,
    "due_by": "2026-09-15"
  },
  "observations": [ { "date": "2017-01-13", "value": 2.40 }, "..." ]
}
```

- `meta` is the descriptor embedded at fetch time (so the frontend never hardcodes a
  title, a methodology paragraph, or a source URL — see the About tab below), with
  one transformation: each `sources[]` reference is resolved through the catalogue
  into `{slug, dataset, name, dataset_name, url, licence, terms_status, via, note}`.
  A reference that doesn't resolve makes that fetch fail — the series stays on
  yesterday's live data rather than shipping an unresolved source.
- `as_of` is computed fresh on every fetch: `due_by` is the descriptor's cadence and
  `publication_lag_business_days` applied to `last_observation`, using a hand-rolled
  US bond-market business-day calendar (`scripts/staleness.py`) — federal holidays by
  rule, Good Friday always closed, plus an `extra_closures` list. Freshness is judged
  by comparing `due_by` against `toLocaleDateString('en-CA', {timeZone: 'America/
  New_York'})` in the browser — no business-day arithmetic in JS, so a stale pipeline
  still reports correctly.
- The **payload** shape depends on the dataset: `observations` (a flat array — most
  datasets), `series` (a dict of named sub-series — `spreads`, which has two:
  `10y2y` and `10y3m`), or `tenors` + `observations` keyed by date (`yield_curve`).
  A multi-input dataset (`sp500_pe`, whose price and earnings inputs have separate
  cadences and one is `status: discontinued`) has a per-input breakdown inside
  `as_of.inputs` instead of one flat `as_of`.

### `scripts/fetch_all.py`: one runner, not five workflow steps

Rather than the workflow calling each fetcher as its own step, `scripts/fetch_all.py`
loops over `series_meta.ids()`, runs each one's fetcher (its `fetcher` key, or
`fetch_<id>.py`) as a subprocess inside a GitHub Actions `::group::<id>` block, times
it, and catches failures per series rather than letting one bad fetch kill the run. It
writes `data/fetch_status.json` (`{id: {ok, returncode, seconds}}`) and always exits 0
— the workflow decides what to do with a failure (see below), the runner's only job is
"try each one, report what happened."

### The source catalogue

`catalog/sources/<slug>.json` is the inventory of where data comes from — one file per
rights holder (`fred`, `shiller`, `spglobal`, `nber` so far). Each records how to reach
the source (`access`: method, URL, format, auth, quirks), under what terms (`terms`: a
one-sentence summary for the About tab, a `status` of `verified` / `restricted` /
`unverified` / `unknown`, the terms page and a verbatim quote), and what it offers
(`datasets[]`: ids, what each gives, topics from a small fixed vocabulary, native
cadence, coverage, publication lag, status). Data that reaches us through another
source carries `via` — the S&P 500 index level is a `spglobal` dataset with `via:
fred`, because the terms are S&P's even though the bytes come from FRED. Every fact
block says which page it was read from (`read_from`), and a fact nobody could
establish is the string `"unknown"` rather than a guess.

Nothing under `site/` reads the catalogue. It feeds the site in exactly one place:
`series_meta.meta_from_descriptor()` resolves a descriptor's `sources[]` references
against it when a fetcher runs, and the About tab renders what landed in `meta`. So a
catalogue correction shows up on the site after the next fetch, with no JS change.

`scripts/catalog.py` is the schema's authority. `python3 scripts/catalog.py check`
validates every file and every descriptor reference (exit 1, one line per problem);
`check catalog/sources/x.json` validates one file alone, which is what a research agent
runs; `report [--topic T]` prints what exists, which series use it, and what comes
through FRED. `catalog/README.md` has the rules and field table;
`catalog/research-log.md` records productive searches (including ones that found
nothing) so the next session builds on them.

---

## The Site Generator

### `scripts/build_site.py`

This is the piece that didn't exist before the rebuild, and it's the reason a
descriptor's `presentation` block matters. Given `pages/site.json` (the site name and
three sections), every `series/<id>.json`, and every `pages/<slug>.json` manifest, it
writes:

- `site/charts/<id>/index.html` — one full-chrome page per descriptor that carries a
  `presentation` block.
- `site/<section>/index.html` — one automatic grid per section (`economy`, `markets`,
  `rates`), listing every chart whose `presentation.sections` includes it, sorted by
  `presentation.order`, at `half` size.
- `site/<section>/<slug>/index.html` or `site/index.html` — one page per curated
  manifest (`pages/<slug>.json`); a manifest with no `section` key is the home page
  (`pages/home.json` → `/`).
- `site/data/<id>.json` — a copy of every `data/<id>.json`, since the deploy publishes
  `site/` and nothing outside it.

It **fails the build**, naming the offending file, on: an unknown section in
`presentation.sections`; a `presentation.chart.type` with no module at
`site/js/charts/<type>.js`; a malformed preset (must match `^\d+[MY]$`, `YTD`, or
`All`); a manifest block naming a chart with no `presentation`; an unknown manifest
`section`; or a descriptor id colliding with a built-in type name (`timeseries`,
`curve`). This runs inside the workflow's gating `pytest` step (see
`tests/test_build_site.py`'s `test_real_repo_builds_into_tmp_path`), so a broken
generator is caught before the deploy step, not after.

### The `presentation` block

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

- `sections`: which of the three section pages this chart appears on (a series can be
  on more than one — `dgs10` is on both `rates` and `economy`).
- `order`: sort key within a section.
- `summary`: one line shown under the chart's title.
- `chart.type`: resolves to `site/js/charts/<type>.js`. Built-in: `timeseries`
  (generic time-series traces) and `curve` (the yield-curve snapshot). A custom
  module is named after the series id it serves (`sp500_pe`).
- `stats` / `table`: whether the card shows a stats row and/or a table, and (for
  `table`) which kind.

A descriptor with no `presentation` key gets no page and no nav entry at all — this
is how `usrec` stays a shared, page-less dataset.

### Every page is a thin shell

A generated page is deliberately small: `<title>`, a link to `/css/site.css` (plus any
`/css/charts/<type>.css`), the pinned Plotly `<script>` tag, a static two-row nav
(site name + sections; on a chart/section/composite page, that section's charts and
composite pages, current item marked), one `<div class="card" data-block="<id>">`
placeholder per block, one inline `<script type="application/json" id="page">`
carrying `{page, blocks: [...]}` (each block's id/title/summary/href/presentation/
size/preset), `<script type="module" src="/js/app.js">`, and a footer with the one
sentence the FRED API Terms of Use require on any product that uses the API ("This
product uses the FRED® API but is not endorsed or certified by the Federal Reserve
Bank of St. Louis." — `FRED_API_NOTICE` in `build_site.py`). **Everything inside a
card is built by JavaScript at runtime** — see the next section. All asset references
are root-relative (`/css/...`, `/js/...`, `/data/...`), so a page nested under
`/economy/` or `/charts/dgs10/` resolves the same files a page at `/` does.

### What's committed vs. what's generated

`series/*.json`, `pages/*.json`, `site/css/`, `site/js/` are committed sources. Every
other path under `site/` — every generated `index.html`, and `site/data/` — is
produced fresh by `build_site.py` and is gitignored (`site/**/index.html`,
`site/data/` in `.gitignore`). Run `scripts/build_site.py` (or `scripts/dev.sh`, which
calls it) after editing a descriptor, a manifest, or anything under `site/css`/
`site/js`, before checking the result in a browser.

---

## The Frontend Runtime

### `site/js/app.js` — the entry point

Every generated page loads `/js/app.js` as a native ES module (no bundler — the
browser loads exactly the files that are written). It parses the inline `#page` JSON,
computes `todayET()` (today's date in US Eastern, once per page load), and calls
`mount(block, today)` for every chart block on the page.

### `site/js/lib/card.js` — the only code that plots into a card

For each block, `mount()`:

1. Builds the whole card DOM from the block's JSON (title linking to `/charts/<id>/`,
   summary, badge, a `Chart | Table | About` sub-tab strip, a control row, the chart
   container, stats/table/About panels) — everything starts in a loading state, so
   titles show before any data arrives.
2. Fetches `/data/<id>.json` eagerly (root-relative, so it resolves the same from any
   page depth), plus `/data/usrec.json` — tolerating a 404 — if the chart config asks
   for recession shading.
3. Renders the freshness badge and the About tab (from `meta`/`as_of` alone — no
   chart-type code needed for either).
4. Dynamically imports the chart type module (`import('/js/charts/<type>.js')`), then
   calls its `stats`/`table` (if the config and the module both provide them) and,
   once, its `render(chartEl, ctx)` — the Chart sub-tab is the default and a card is
   never `display:none` at mount, so the container has real width by construction
   (this is what stopped a recurring bug from the single-file era, where a chart
   drawn into a hidden tab got stuck at Plotly's 700px fallback size).
5. Wires the CSV/JSON export buttons and, if the config lists `presets`, the HTML
   range-preset row.
6. On a `themechange` event (there's no toggle wired into generated pages yet — see
   "Known gaps" below — but the listener is live and tested), destroys and
   re-renders the chart with freshly-read theme colours.

Every DOM query inside `card.js` is scoped to that card's own container element, so
two cards — even two mounts of the same chart type — never collide.

### `ctx`: what a chart type receives

`render(el, ctx)`, and the optional pure `stats(ctx)`/`table(ctx)`/`csv(ctx)`, all
receive the same context object: `id`, `data` (the parsed data file), `meta`, `as_of`,
`presentation`, `today`, `theme` (resolved colour *values*, read from CSS custom
properties — never a literal), `variant` (`full`/`half`/`third`), `recessions` (the
interval list or `null`), `initialPreset`, and `slots.controls` (an empty element in
the control row for a type's own DOM controls, like the yield curve's overlay
toggles).

### Chart types: `site/js/charts/`

- **`timeseries.js`** — the generic type `dgs10` and `spreads` both use. Derives one
  trace per key from a `series`-shaped payload, or one trace from an
  `observations`-shaped payload, with no path adapter; supports recession shading,
  a zero line, and two table kinds (`recent`, `changes`).
- **`curve.js`** — the yield-curve type. Categorical, evenly-spaced tenor axis
  (Bloomberg convention); overlay toggle buttons and a custom date picker as
  *closure-scoped* per-mount state (never module-level, so a future second curve
  mount on one page — e.g. nominal and TIPS — stays independent); redraws via
  `Plotly.react` rather than a fresh plot on every toggle.
- **`sp500_pe.js`** — the one chart with logic too bespoke for `timeseries`: a solid
  confirmed-earnings trace and a dashed estimated trace (prepended with the last
  confirmed point so the dash visually connects), a long-term-average stat, and
  dagger-marked table rows for estimated months.

Every type module is subject to the same rules, checked by
`tests/test_build_site.py`: no module-level mutable state, no
`document.getElementById`, no hex/rgb colour literal anywhere under `site/js`, and
`margin`/legend position/`rangeslider`/height may only be set in
`site/js/lib/plotly-layout.js` (its `baseLayout()` is what every type calls for that
shared chrome).

### Theming

`site/css/tokens.css` defines a light and a dark palette under a frozen set of CSS
custom property names (`--series-1`…`--series-6`, `--up`, `--down`,
`--recession-fill`, plus the original six). `site/js/lib/theme.js`'s `getTheme()`
reads them into `ctx.theme` at draw time. **Known gap**: the light/dark toggle and its
anti-FOUC script exist only conceptually — no generated page has a working toggle
control yet (see below); pages currently render whatever `prefers-color-scheme` says
on load and stay that way for the session.

---

## GitHub Actions — Daily Automation

### `.github/workflows/update-data.yml`

#### Triggers

```yaml
on:
  schedule:
    - cron: '15 23 * * 1-5'   # 23:15 UTC Mon–Fri
  workflow_dispatch:
```

23:15 UTC is after FRED's own ~16:15 ET H.15 update, hours before the US Eastern
midnight boundary freshness is judged against, and off the congested top-of-hour cron
slot GitHub Actions itself gets busiest at.

#### Job steps

1. **Checkout + Python 3.12 setup**, then `pip install pandas xlrd openpyxl -r
   requirements-test.txt`.
2. **Seed `data/` from `gh-pages`**: `git fetch --depth=1 origin gh-pages`, then for
   every id in `series/*.json`, `git checkout FETCH_HEAD -- data/<id>.json`. This
   matters because `main`'s `data/*.json` are test fixtures that can lag the live
   site by months — seeding means a fetch failure below carries forward what's
   actually live, not a stale fixture. Named files only, never the directory:
   `data/earnings_overrides.json` is a fetch-time input that doesn't exist on
   `gh-pages` at all, and a directory-level restore would delete it.
3. **`python scripts/fetch_all.py`** (with `FRED_API_KEY` from GitHub Secrets) — every
   series' fetcher, failures caught per-series into `data/fetch_status.json`.
4. **`pytest -m "not staleness"`** (gates the deploy) — the correctness suite,
   including `test_build_site.py`'s real-generator integration test. A *wrong*
   number here blocks the deploy; a *late* one doesn't (see next step).
5. **`pytest -m staleness`** (`continue-on-error: true`, `STALENESS_SOURCE=local`) —
   reports overdue series without blocking.
6. **Write a staleness summary table** to the GitHub Actions job summary.
7. **`python scripts/build_site.py`** — generates the site from whatever data just
   got fetched (or carried forward from the seed step).
8. **Deploy to GitHub Pages** (`peaceiris/actions-gh-pages@v4`, force-pushing `./site`
   to the `gh-pages` branch, `cname: joemirza.com`) — this step always runs; a fetch
   failure never blocks it.
9. **Report fetch failures and overdue series** (`if: always()`): reads
   `data/fetch_status.json` and the staleness check, prints a GitHub Actions
   `::warning::` for each problem, and — only in this final step, *after* the site
   has already shipped — exits 1 if any fetch failed, so the job shows red and GitHub
   notifies without having delayed the site update.

This is a deliberate departure from "one failure blocks everything": the old
all-or-nothing model meant one FRED hiccup froze every series with no badge. The
current policy is seed → fetch what you can → gate only on correctness → always
deploy → fail the job afterward if something needs attention.

### GitHub Secrets

- `FRED_API_KEY` — the only secret this project needs; does not expire.
- `GITHUB_TOKEN` (for the Pages deploy) is provided automatically.

---

## GitHub Pages — Hosting

- **Source branch**: `gh-pages`, entirely managed by the deploy action — never edit
  it directly.
- **Source path**: `/` (root of the branch).
- **Custom domain**: `joemirza.com`, set via the `CNAME` file the deploy action writes.

The `gh-pages` branch holds exactly what `build_site.py` wrote into `site/` that run:
every generated `index.html`, `site/data/*.json`, plus `CNAME` and `.nojekyll`. Your
working code — the sources `build_site.py` reads — lives on `main`.

---

## DNS and Custom Domain

Unchanged since the original build. DNS (Porkbun) points `joemirza.com` at GitHub
Pages:

| Type | Host | Value | Purpose |
|------|------|-------|---------|
| A | *(root)* | 185.199.108.153 | GitHub Pages IP |
| A | *(root)* | 185.199.109.153 | Redundancy |
| A | *(root)* | 185.199.110.153 | Redundancy |
| A | *(root)* | 185.199.111.153 | Redundancy |
| CNAME | www | FuriousGeorge19.github.io | `www.joemirza.com` support |

GitHub matches the `Host` header of an incoming request against the `CNAME` file on
`gh-pages` and serves that branch's content.

---

## HTTPS / SSL Certificate

**Still an open item, unresolved since the initial 2026-03-05 deploy.**
`https://joemirza.com` serves GitHub's `*.github.io` wildcard certificate, not one
issued for `joemirza.com` — `gh api repos/FuriousGeorge19/fin-econ-data/pages` shows
`https_enforced: false`. Only `http://` reliably works. The likely fix is removing and
re-adding the custom domain in **Settings → Pages** to force GitHub to re-request a
Let's Encrypt certificate — a UI action, not something scriptable from here.

---

## What Happens When Someone Visits joemirza.com

1. DNS resolves `joemirza.com` to one of GitHub's four IPs.
2. The browser requests, e.g., `GET /charts/dgs10/`.
3. GitHub matches the `Host` header to the `CNAME` on `gh-pages` and serves
   `charts/dgs10/index.html` — a small generated shell (see "Every page is a thin
   shell" above).
4. The browser parses the HTML, applies `/css/site.css` (which itself pulls in
   `/css/tokens.css` for colour values), and loads Plotly.js from its CDN.
5. `/js/app.js` (a native ES module) runs: parses the inline `#page` JSON, calls
   `mount()` for the one card on this page.
6. `mount()` fetches `/data/dgs10.json`, then dynamically imports
   `/js/charts/timeseries.js` and calls its `render`, `stats`, `table`.
7. Plotly draws the chart into a container that was visible the whole time — no
   hidden-tab sizing bug, since there are no tabs to hide behind.

A section page (`/economy/`) or the home page (`/`) does the same thing once per card
— each card's `mount()` call is independent, so one card's fetch failing doesn't
affect the others on the same page.

---

## What Happens Every Weekday Evening

1. GitHub Actions wakes at 23:15 UTC and provisions a fresh Ubuntu runner.
2. The runner checks out `main`, installs Python 3.12 and the fetch dependencies.
3. `data/` is seeded from the live `gh-pages` copy (see above).
4. `scripts/fetch_all.py` runs every fetcher; each writes its own `data/<id>.json` (or
   leaves the seeded copy in place if it failed).
5. `pytest -m "not staleness"` gates; if it fails, the job stops here — **no
   deploy happens** on a correctness failure.
6. The staleness report runs and gets written to the job summary, without gating.
7. `scripts/build_site.py` regenerates every page from whatever `data/` now
   contains.
8. The deploy action force-pushes `./site` to `gh-pages`; GitHub Pages picks up the
   new commit and serves it within roughly 30 seconds.
9. The final step reports any fetch failure or overdue series and fails the job
   (after the deploy already happened) if there's something to flag.
10. The runner is destroyed. Nothing persists between runs except what got committed
    to `gh-pages`.

---

## Project File Structure

```
fin-econ-data/
├── .github/workflows/update-data.yml   Daily fetch + build + deploy
├── data/                                Raw fetcher output (test fixtures on main;
│   ├── dgs10.json                       gh-pages is the deploy history — see above)
│   ├── sp500_pe.json
│   ├── yield_curve.json
│   ├── spreads.json
│   ├── usrec.json
│   └── earnings_overrides.json          Manually maintained input, not a fetcher output
├── series/                              One hand-maintained descriptor per dataset
│   ├── dgs10.json                       (meta fields + an optional presentation block)
│   ├── sp500_pe.json
│   ├── yield_curve.json
│   ├── spreads.json
│   └── usrec.json                       No presentation — data-only, no page
├── pages/
│   ├── site.json                        Site name + the three sections
│   └── home.json                        Curated manifest for /
├── catalog/                             The source inventory
│   ├── README.md                        Rules + field table (what a research agent reads)
│   ├── sources/                         One file per rights holder
│   │   ├── fred.json, shiller.json, spglobal.json, nber.json
│   └── research-log.md                  Productive searches, newest first
├── scripts/
│   ├── fetch_treasury.py, fetch_sp500_pe.py, fetch_yield_curve.py,
│   │   fetch_spreads.py, fetch_usrec.py    One fetcher per dataset
│   ├── fetch_all.py                     Runs every fetcher, non-fatal per series
│   ├── build_site.py                    The site generator
│   ├── catalog.py                       Catalogue validator / resolver / report
│   ├── series_meta.py, staleness.py,
│   │   build_earnings_overrides.py, fred_utils.py    Shared helpers
│   └── dev.sh                           Local iteration loop
├── site/
│   ├── css/
│   │   ├── site.css                     Committed — nav, card grid, chrome
│   │   └── tokens.css                   Committed — light/dark colour tokens
│   ├── js/
│   │   ├── app.js                       Committed — page entry point
│   │   ├── lib/                         Committed — shared runtime (card.js, etc.)
│   │   └── charts/                      Committed — chart-type modules
│   ├── data/                            GENERATED, gitignored
│   └── **/index.html                    GENERATED, gitignored (every page)
├── tests/                                Pytest correctness suite
├── openspec/                             Design history (specs, changes, archive)
├── .gitignore
├── CLAUDE.md                             Context file for Claude Code sessions
└── HOW-IT-WORKS.md                       This file
```

---

## How to Add a New Data Series

The whole point of the rebuild was making this file-additive for the common case.

### 1. Fits an existing chart type (`timeseries` or `curve`) — most series will

1. **Write `series/<id>.json`**: the metadata fields (title, units, cadence, sources,
   methodology, notes) plus a `presentation` block — `sections`, `order`, `summary`,
   `chart` (`type` + options; see `timeseries.js`'s payload convention above), `stats`,
   `table`.
2. **Write `scripts/fetch_<id>.py`** (or reuse an existing script via a `"fetcher"`
   key, as `dgs10` does).
3. **Write `tests/test_<id>.py`** and run the fetcher once locally to produce a
   `data/<id>.json` fixture.
4. **Run `python3 scripts/build_site.py`.** The chart's page, its entries on every
   section page it's assigned to, and the nav are all derived from the descriptor —
   no workflow edit, no HTML file, no nav edit needed.

Curating the new series onto `/` (or a future composite page) is a separate,
deliberate edit to `pages/*.json` — never automatic.

### 2. Needs a genuinely new chart type

Only necessary when the drawing logic can't be expressed as `timeseries`/`curve`
config — write `site/js/charts/<type>.js` exporting `render(el, ctx)` and optional
pure `stats`/`table`/`csv`. Read `timeseries.js` or `curve.js` first as a worked
example, and follow the same rules every type must: no module-level mutable state, no
`document.getElementById`, no colour literal, and never set Plotly `margin`/legend
position/`rangeslider`/height directly (call `baseLayout()` from
`site/js/lib/plotly-layout.js` instead). `tests/test_build_site.py` greps for
violations of the last three.

### 3. Test locally

```bash
FRED_API_KEY=your_key python3 scripts/fetch_all.py   # or one fetcher at a time
scripts/dev.sh                                        # regenerates + serves
# open http://127.0.0.1:8888/ (use 127.0.0.1, not localhost — see Troubleshooting)
```

---

## Troubleshooting

### The site shows old data

- Check the GitHub Actions tab: did the latest "Update Data" run succeed?
- If it failed at the `pytest` step, the deploy didn't happen at all — the site is
  serving whatever it last successfully deployed.
- If a specific series' fetch failed but the run otherwise succeeded (a red job with
  a green-looking deploy history), that series is serving its last live value — check
  the job's `::warning::` annotations for which one and why.

### The site is completely down

- Check GitHub Pages status: https://www.githubstatus.com/
- Check DNS: `dig joemirza.com` should return GitHub's four IPs.
- Check repo Settings → Pages is still configured with the `gh-pages` source.

### I want to force a data refresh right now

```bash
gh workflow run "Update Data"
gh run watch --exit-status
```

Or: GitHub repo → Actions tab → "Update Data" → "Run workflow".

### I changed the site locally but it's not showing up online

Local changes need to be committed and pushed to `main` — but the live site deploys
from `gh-pages`, generated by the workflow, not from whatever you pushed to `main`
directly. After pushing to `main`, either wait for the next scheduled run or trigger
one manually (above). Editing `site/*.html` directly does nothing lasting — it's
gitignored and gets regenerated (and overwritten) by `scripts/build_site.py` on the
next run.

### `localhost` is showing stale content during local iteration

A recurring gotcha on this machine, across several sessions: `http://localhost:PORT`
has repeatedly served a stale cached response even after restarting `scripts/dev.sh`
and hard-reloading. Use `http://127.0.0.1:PORT/` instead — it has reliably shown the
current file contents every time this has come up.

### DNS isn't resolving / site shows Porkbun's parking page

- Verify the four A records in Porkbun point to GitHub's IPs.
- Confirm no old ALIAS or wildcard CNAME record pointing at Porkbun survived.
- Propagation is usually minutes with Porkbun, but can take up to 48 hours.
- Test with `dig +short joemirza.com A`.
