# series/ — descriptor rules (loads when a descriptor is read)

One JSON file per dataset. This directory is the single source of the site's file list:
`scripts/fetch_all.py`, `scripts/build_site.py`, `scripts/staleness.py`, `scripts/dev.sh` and
the workflow's seed step all derive from it. Schema authority is `tests/test_series_metadata.py`
(`REQUIRED_FIELDS`, `ALLOWED_PRESENTATION_KEYS`, `ALLOWED_CHART_KEYS`, `ALLOWED_TABLE_KEYS`) and
`openspec/specs/series-metadata/spec.md`. Exemplars: `fedfunds.json` (plain FRED timeseries),
`gs10_long.json` (stitched, two inputs), `tenor_history.json` (a view), `yields_table.json`
(custom chart type, `size: "full"`), `usrec.json` (data only, no page).

## Fields

- Required: `id`, `title`, `short_title`, `kind` (timeseries | curve | intervals), `units`,
  `cadence` (daily | monthly | quarterly), `publication_lag_business_days`, `revisions`,
  `revision_note`, `source_line`, `sources`, `inputs`, `methodology`, `notes`.
  Optional: `fetcher`, `presentation`.
- `sources[]` are references into the catalogue, `{slug, dataset?, url?, note?}` — never
  `name`/`licence` (the tests reject them). The slug must exist under `catalog/sources/` and
  `dataset` must be an id in that file. Each `inputs[]` entry names its `source` and may name
  its `dataset`. Resolution happens at fetch time (`series_meta.meta_from_descriptor`), so
  **descriptor prose reaches the site only when the fetcher next runs** — rerun it locally
  after editing `methodology`/`notes` if you want to see the change.
- `methodology` is About-tab prose about how the numbers are made. Decisions and caveats go
  in `notes` (chart 8's rescope off ICE BofA; `real_short_rate`'s missing October 2025 CPI).
  Decision minutes in `methodology` was an S11b verifier finding.
- An input with `required: false` never gates `due_by` (`gs10_long`'s fixed pre-1953 leg).
- `fetcher`: the script name when it is not `fetch_<id>.py` (`dgs10` → `fetch_treasury.py`;
  the three `sp500_*` → `fetch_sp500_pe.py`). Point at an existing script rather than
  writing a second one that downloads the same file.
- No `presentation` means a data-only dataset with no page (`usrec`, used for shading).

## The `presentation` block

- Required: `sections` (subset of `pages/site.json`: economy, markets, rates), `order`,
  `summary`, `chart`. Optional: `stats`, `table` (`{kind: recent | changes, rows, windows}`),
  `publish`, `data`, `size`.
- `chart.type` names a module in `site/js/charts/` (`timeseries`, `curve`, `tenors`,
  `sp500_pe`, `yields_table`, `duration_calc`, `decomposition`, `risk_off_table`,
  `drawdown_shift`). Options: `y {suffix, format}`, `presets` (`1M 6M 1Y 5Y All`
  grammar), `recessions`, `zeroline`, `overlays` (`1w`/`1m`/`5y` grammar, plus `ytd`), `custom_date`, `traces`, and for `tenors`
  `tenors`/`default_tenors`/`stat_tenors`. The payload shapes `timeseries` accepts are in
  `site/js/charts/timeseries.js`'s header comment.
- **`publish: false`** keeps a series off the public site. `build_site.py` derives chart
  pages, section grids, nav, curated-manifest blocks and the `site/data/` copy from the
  published set; a manifest that still names the series is skipped, not failed. Only
  `build_site.py --include-unpublished` (what `scripts/dev.sh` passes) builds it. Use it for
  terms, not for work in progress — unfinished work has no `presentation` yet. The ids in
  `tests/test_build_site.py`'s `LICENCE_RESTRICTED` may not be flipped without a terms decision
  recorded in the Session Plan.
- **`data: "<id>"`** makes a **view**: a page drawn from another series' data file, with no
  fetcher and no `data/<id>.json` of its own (`tenor_history` over `yield_curve`).
  `build_site.py` rejects a view naming a missing series, itself, another view, or publishing
  while its source is unpublished. The About tab shows the source's sources, licence and
  freshness but the view's own title, methodology and notes (carried through the page
  JSON as `meta_overrides`). `series_meta.is_view()` /
  `data_id()` are the predicates; `fetch_all.py` and `staleness.py` skip views.
- **`size: "full"`** overrides whatever width a grid or manifest asked for (`yields_table`,
  13 columns, was unreadable at half width).
- Curating a series onto `/` (`pages/home.json`) is a deliberate editorial edit, never
  automatic. Section pages are automatic.

## What a chart shows (editorial conventions)

- Recession shading on a time-series chart, `recessions: true` (data from `usrec`), is the
  convention; `dgs10`, `gs10_long` and the `sp500_*` charts predate it and lack it.
- Never upsample monthly to daily; monthly observations sit on the first of the month.
  A series stitched from more than one source carries `source` and `frequency` on every
  observation, and the hover shows "Source: <short_name>" (`gs10_long`).
- Make data gaps visible; never interpolate across them. The real example: DGS20 has no
  values from 1987-01 to 1993-09 (last 1986-12-31, next 1993-10-01) while Treasury issued no
  20-year bond, and it is the only tenor with a gap over six months — pinned by
  `tests/test_tenor_history.py`. (DGS30's 2002–2006 suspension is not a gap in this data.)
  A single omitted month (`real_short_rate`, Oct 2025) is left out of the data and, for now,
  drawn through — say so in `notes`.
- FRED's `"."` is missing, never zero.
- Where zero is meaningful (spreads, real rates, ERP): `zeroline: true`; diverging colours.
  Sequential scale for heatmaps.
- Price levels that compound over decades plot on a log axis, labelled as such. Not yields,
  ratios or spreads.
- No dual y-axes — held lightly, no chart has needed one. Prefer a derived series, a scatter,
  or stacked panels on one time axis.
- Curve snapshots use a categorical, evenly spaced tenor axis and label the current curve
  with its values.
- Title a derived series for what it measures, not its inputs ("Corporate Credit Spread
  Across Investment Grade", not "Baa − Aaa").
- The in-chart source line, the freshness badge, "All" = `[first_observation, today]` and
  the absence of a range slider are the runtime's job (`site/js/CLAUDE.md`); a descriptor
  supplies only `source_line`.
