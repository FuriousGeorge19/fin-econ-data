## ADDED Requirements

### Requirement: Generated multi-page site from descriptors and manifests

`scripts/build_site.py`, using only the Python standard library, SHALL read
`pages/site.json` (site name and the sections `economy`, `markets`, `rates` with labels
and taglines), every `series/*.json`, and every `pages/*.json`, and SHALL write into
`site/`: `charts/<id>/index.html` for every descriptor carrying `presentation`,
`<section>/index.html` for every section (an automatic grid of the section's charts at
`half` size ordered by `presentation.order`), `<section>/<slug>/index.html` for every
manifest with a `section`, and `index.html` from `pages/home.json` when it exists. Each
page SHALL be a shell containing the title, the stylesheet links (`css/site.css` and
every `css/charts/*.css`), the pinned Plotly `<script>`, the static nav, one placeholder
element per block, one inline `<script type="application/json" id="page">` carrying the
page and its blocks (each block's `id`, `title`, `short_title`, `summary`, `href`,
`presentation`, `size`, `preset`), and `<script type="module" src="/js/app.js">`. The
script SHALL also copy each `data/<id>.json` into `site/data/` and SHALL print every
path it writes. It SHALL fail with a message naming the file when a `chart.type` module
does not exist, a section id is unknown, a manifest names a series without
`presentation`, a preset is malformed, or a descriptor id is `timeseries` or `curve`.

#### Scenario: Page per series

- **WHEN** `series/fedfunds.json` with a `presentation` block is added and the generator
  runs
- **THEN** `site/charts/fedfunds/index.html` exists, `site/economy/index.html` lists it
  in `order` position, and no other input file was edited

#### Scenario: Home page only when curated

- **WHEN** `pages/home.json` does not exist
- **THEN** the generator writes every other page and leaves `site/index.html` untouched

### Requirement: URL scheme and static navigation

The site SHALL serve `/` (curated grid), `/<section>/` (automatic grid), `/charts/<id>/`
(single chart, full chrome) and `/<section>/<slug>/` (curated grid or narrative). Every
page SHALL carry a generated two-row nav: the site name linking to `/` and the three
sections; then, on section, chart and composite pages, that section's charts by
`short_title` plus its composite pages, with the current item marked. A chart page's
second row SHALL be its first listed section. All asset and data references SHALL be
root-relative (`/js/…`, `/css/…`, `/data/…`).

#### Scenario: Chart in two sections

- **WHEN** `series/dgs10.json` lists `sections` `["rates", "economy"]`
- **THEN** the 10Y Treasury card appears on `/rates/` and `/economy/`, its page is
  `/charts/dgs10/` with the Rates & Yields row, and it is listed in both sections' rows

#### Scenario: Data resolves from a subdirectory

- **WHEN** `/economy/` mounts the spreads card
- **THEN** it fetches `/data/spreads.json`, not `/economy/data/spreads.json`

### Requirement: Page manifests and block types

A page manifest `pages/<slug>.json` SHALL carry `slug`, `title`, `layout` (`grid` or
`narrative`), optional `section` (absent only for `home`), optional `intro`, and
`blocks[]`, each block one of `{chart, size, preset}` (`size` in `full`, `half`,
`third`; `preset` optional) or `{text: {html}}`. The names `table` and `tile` are
reserved for later block types. Grid layout SHALL place blocks in a responsive grid that
collapses to one column under 640px; narrative layout SHALL place them in one column in
order.

#### Scenario: Composite page

- **WHEN** `pages/state-of-the-us-bond-market.json` lists the yield curve at `full` and
  spreads at `half` with preset `10Y` under section `rates`
- **THEN** `/rates/state-of-the-us-bond-market/` renders both cards at those sizes with
  spreads opening on the last ten years, and the page is listed in the Rates & Yields
  nav row

### Requirement: Generated paths are not committed

`site/index.html`, every `site/**/index.html` and `site/data/` SHALL be gitignored;
`site/css/` and `site/js/` SHALL be committed sources. `scripts/dev.sh` and the workflow
SHALL run the generator before serving or deploying. Until the cutover the tracked
`site/index.html` SHALL NOT be written by the generator.

#### Scenario: Two branches add series

- **WHEN** two branches each add one descriptor and one fetcher and are merged
- **THEN** the merge has no conflict, because no generated page is tracked and no shared
  file was edited on either branch

### Requirement: Adding a series is file-additive

Adding a standard series SHALL require only new files: `series/<id>.json` with
`presentation`, `scripts/fetch_<id>.py` (or the script named by the descriptor's
`fetcher`), `tests/test_<id>.py`, and `data/<id>.json` produced by running the fetcher
once. A new chart type additionally adds `site/js/charts/<type>.js` and optionally
`site/css/charts/<type>.css`. No edit to the workflow, the nav, any page manifest,
`conftest.py`, `site/index.html` or any other shared file SHALL be needed; placing the
series on `/` or a composite page is a separate curation edit.

#### Scenario: Fed Funds added

- **WHEN** an agent adds `series/fedfunds.json`, `scripts/fetch_fedfunds.py`,
  `tests/test_fedfunds.py` and `data/fedfunds.json`
- **THEN** the next generator run and workflow run publish `/charts/fedfunds/` and list
  it on `/economy/` with no other file changed

### Requirement: Fetch runner and fetch status

`scripts/fetch_all.py` SHALL run, for every descriptor id, the script named by its
`fetcher` (default `scripts/fetch_<id>.py`) as a subprocess inside a `::group::<id>`
block with its elapsed seconds, catching every failure, and SHALL write
`data/fetch_status.json` mapping each id to `{ok, returncode, seconds}`. It SHALL always
exit 0. The workflow SHALL run it as one step in place of per-series steps, and the
step-summary and final failure-reporting steps SHALL read `fetch_status.json`.

#### Scenario: One fetcher fails

- **WHEN** `fetch_sp500_pe.py` exits non-zero and the other four succeed
- **THEN** `fetch_status.json` marks `sp500_pe` not ok, the other four ok, the runner
  exits 0, and the workflow's final step later fails the job naming `sp500_pe`

### Requirement: Generator verified by tests

`tests/test_build_site.py` SHALL run the generator into a temporary directory and assert:
a page for every descriptor with `presentation`; section pages list their charts in
`order`; every manifest resolves; the inline `#page` JSON parses; each data file has the
payload shape its type expects (`series` or `observations` for `timeseries`, `tenors`
for `curve`); every `chart.type` module and `fetcher` script exists; no hex or rgb
colour literal under `site/js`; and no `margin`, `rangeslider`, `height` or
`getElementById` outside `site/js/lib/plotly-layout.js` and `site/js/lib/card.js`. It
SHALL run inside the workflow's gating `pytest` step, before the deploy.

#### Scenario: Generator broken before deploy

- **WHEN** a descriptor names a chart type whose module is missing
- **THEN** the gating tests fail and the deploy does not run
