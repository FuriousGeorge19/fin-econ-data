## MODIFIED Requirements

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
`presentation`, `size`, `preset`), `<script type="module" src="/js/app.js">`, and a
footer carrying the attribution notice the FRED API Terms of Use require ("This product
uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St.
Louis."). The script SHALL also copy each `data/<id>.json` into `site/data/` and SHALL
print every path it writes. It SHALL fail with a message naming the file when a
`chart.type` module does not exist, a section id is unknown, a manifest names a series
without `presentation`, a preset is malformed, or a descriptor id is `timeseries` or
`curve`.

#### Scenario: Page per series

- **WHEN** `series/fedfunds.json` with a `presentation` block is added and the generator
  runs
- **THEN** `site/charts/fedfunds/index.html` exists, `site/economy/index.html` lists it
  in `order` position, and no other input file was edited

#### Scenario: Home page only when curated

- **WHEN** `pages/home.json` does not exist
- **THEN** the generator writes every other page and leaves `site/index.html` untouched

#### Scenario: FRED API notice on every page

- **WHEN** the generator writes any page
- **THEN** the page's footer contains "This product uses the FRED® API but is not
  endorsed or certified by the Federal Reserve Bank of St. Louis."
