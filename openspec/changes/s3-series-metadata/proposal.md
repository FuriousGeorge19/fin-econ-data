## Why

S3 of the cross-session plan (`~/Obsidian/Investing/Finance and Economic Data
Website/Session Plan.md`) is the first of two design sessions: settle series metadata,
staleness and as-of semantics before more charts are built, because every chart built
afterwards inherits them. S4 builds this change; S5's chart components, S8's source
catalogue and S11d's yields table (per-row as-of stamps) all read the header contract
defined here.

Today nothing on the site can say what date its data is actually through. Every
`data/*.json` header carries `last_updated`, the pipeline run time, and that is the only
header field `site/index.html` reads: the live 10Y Treasury tab says "updated 12 Sep"
while its last observation is 10 Sep. No file records its last observation, and
`usrec.json` cannot derive one. `scripts/staleness.py` fuses cadence, publication lag
and slack into one integer per series with no holiday calendar, and the staleness test
gates the whole deploy, so one stale series would block fresh data for the other four.
When a fetch fails the run stops and the whole site freezes silently; deploying what did
succeed is impossible today because a failed series' only fallback is `main`'s copy,
which is from March. The S1 `xfail` (`sp500_pe.json` header 222.53 vs 234.06 in every
recent observation) is a definitional bug in the same area: which months count as
confirmed.

## What Changes

- **Series descriptor per dataset**: `series/<id>.json` (`dgs10`, `sp500_pe`,
  `yield_curve`, `spreads`, `usrec`) holds title, sources and licence, inputs with
  cadence and publication lag, revision policy, methodology and notes. Each fetcher
  embeds it verbatim under `meta` and writes a runtime `as_of` block (`fetched_at`,
  first/last observation, `period_label`, `due_by`, per-input and per-series as-of).
  The list of site data files, the staleness check, `dev.sh` and the workflow all
  derive from `series/*.json`. **BREAKING** for the JSON header: `title`, `units`,
  `frequency`, `source`, `methodology`, `description`, `series_id` and
  `last_ttm_earnings` move under `meta`/`as_of`; `last_updated` survives one release as
  an alias of `as_of.fetched_at`. Payload keys (`observations`, `series`, `recessions`,
  `tenors`, `tenor_months`) are unchanged.
- **Overdue rule**: `due_by` = next period end + publication lag in business days
  (Mon–Fri less US bond-market holidays), computed in Python at fetch time; the browser
  only compares it to the US Eastern calendar date. An overdue chart gets a badge
  (`Overdue · expected by 14 Sep 2026 · 3 days late`, calendar days); a `discontinued`
  input is stated, not alarmed.
- **Chart chrome**: a source line with the data-through date drawn inside every Plotly
  figure; an About sub-tab rendered from `meta`/`as_of`; time-series x-axes end at
  today; comparison windows anchor on the last observation, snap on-or-before, and show
  the resolved date; CSV/JSON/PNG export buttons with as-of-dated filenames.
- **Workflow**: seed `data/` from the `gh-pages` branch by named file before fetching;
  fetch steps become non-fatal so a failed series carries yesterday's live file forward;
  the staleness check reports to the job summary instead of gating; a final step fails
  the job after deploy if any fetch failed; the cron moves from `0 0 * * 2-6` to
  `15 23 * * 1-5`. No commit-back of data to `main`.
- **S&P 500 P/E**: a month is confirmed iff the earnings file holds the calendar quarter
  ending before it begins (so Oct–Dec 2025 are confirmed, Jan 2026 onward estimated, and
  the header bug disappears by definition); the unfinished current month is dropped;
  `build_earnings_overrides.py` reads the workbook's own as-of cells; the discontinued
  S&P file is recorded as such.
- **USREC**: the fetcher records the last observed month and its value before collapsing
  to intervals.

## Capabilities

### New Capabilities
- `series-metadata`: the descriptor file, the `meta` + `as_of` header contract, period
  labels, atomic writes, the transitional alias, and the metadata tests.
- `data-freshness`: the business-day calendar, the `due_by` rule with worked fixtures,
  the roll-up over inputs, the US-Eastern "today", the overdue badge, discontinued
  inputs, and the staleness check reading `as_of`.
- `chart-chrome`: everything drawn around a chart — the in-chart source line, the About
  tab, the x-axis end rule, comparison as-of, and export buttons.

### Modified Capabilities
- `daily-automation`: cron slot; seed-from-live, non-fatal fetches, staleness summary,
  deploy-always, failure reported after deploy.
- `data-pipeline`: "JSON output schema conventions" now defers to the header contract.
- `sp500-pe-series`: stitched-source wording and header fields; the confirmed/estimated
  rule; overrides as-of and discontinuation; "through the last completed month".
- `nber-recession-data`: dataset carries `meta`/`as_of` including the last observed month.
- `treasury-10y-series`: the fetch scenario names the new header location.
- `treasury-spreads-series`: output shape; recession band shaded to today; table shows
  resolved comparison dates.
- `yield-curve-series`: table shows resolved comparison dates.

## Impact

- **Affected (S4a, Python and workflow)**: new `series/*.json`,
  `scripts/series_meta.py`, `tests/test_series_metadata.py`; modified
  `scripts/staleness.py`, the five fetchers, `scripts/build_earnings_overrides.py`,
  `scripts/dev.sh`, `tests/test_staleness.py`, `tests/test_data_integrity.py`,
  `.github/workflows/update-data.yml`; regenerated `data/*.json` fixtures.
- **Affected (S4b, JS)**: `site/index.html` — shared loader, in-chart annotation, badge,
  About sub-tab, x-axis rule, comparison helper, export buttons.
- **Not affected**: payload shapes; the tab set and labels; `dashboard-site`; the Plotly
  version; the S8 catalogue (only a `sources[].slug` seam is reserved).
- **Rollback**: the workflow edits (seed step, `continue-on-error`, summary step, final
  step, cron) are one file and revert independently. The header change is the only
  coupling between S4a and S4b: the `last_updated` alias keeps the old page working on
  new data for one release, so either half can be reverted alone.
