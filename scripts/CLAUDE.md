# scripts/ — fetcher and tool conventions (loads when a script is read)

Every script opens with a docstring saying what it does and writes; read that before the
code. The shared helpers:

- `fred_utils.py` — `fetch_series(series_id, ...)`: the FRED API call with retry, drops the
  `"."` missing-value sentinel, returns `{date, value}` oldest-first. Never re-implement the
  call, and never pass a row cap: the old 6300-row newest-first cap in `fetch_yield_curve.py`
  silently held its history to 2002 until S11b removed it.
- `series_meta.py` — `load(id)` / `ids()` / `is_view()` / `data_id()`;
  `meta_from_descriptor(d)` strips `presentation`/`fetcher` and resolves `sources[]` through
  the catalogue (raises naming the descriptor and slug on a bad reference, so the fetch fails
  rather than shipping an unresolved source); `build_as_of(...)` for the freshness block;
  `period_label`; `write_json` (atomic).
- `staleness.py` — the US bond-market business-day calendar, `compute_due_by`, `check()`.
  Shared by the tests and `dev.sh`; never re-derive lag logic elsewhere.
- `catalog.py` — the catalogue's loader, validator, resolver and report:
  `check [path…]`, `report [--topic T]`. The schema's authority.
- `fetch_all.py` — runs each descriptor's fetcher (`fetcher` key, default `fetch_<id>.py`)
  as a subprocess, catches failures per series into `data/fetch_status.json`, always exits 0.
- `build_site.py` — the generator (stdlib): `series/` + `pages/` → `site/`. Fails naming the
  file on an unknown section, missing chart module, malformed preset, unresolved manifest
  reference, id colliding with a type name, or a bad view. `--include-unpublished`.
- `dev.sh [port]` — build with `--include-unpublished`, warn per stale series, serve on
  `127.0.0.1:8899`. `--live` pulls the published series' data down first. No network otherwise.
- `stock_bond.py` — shared computation for `risk_off_days`, `stock_bond_correlation` and
  `drawdown_curve_shift` (FRED `SP500` + `DGS*`, paired on common dates). Each has its own
  thin `fetch_<id>.py`. The sign convention (correlation of stock returns with yield
  *changes*: positive = the bond hedge works) is printed on the chart and in its docstring.
- `build_earnings_overrides.py` — manual fallback only, not in the pipeline since S9b; its
  trigger (Shiller's earnings column stops updating) is Session Plan Phase 5.

## Writing a fetcher

- Stdlib only (`urllib`, `json`). The one exception is `fetch_sp500_pe.py` (pandas, xlrd,
  openpyxl for Shiller's workbook) and the scripts that reuse its helpers
  (`fetch_gs10_long.py`, `fetch_equity_risk_premium.py`).
- Output `data/<id>.json` = `meta` (from `meta_from_descriptor`) + `as_of` (from
  `build_as_of`) + the payload. Shapes: `observations` `[{date, value}]` for a timeseries;
  `tenors` / `tenor_months` / date-keyed observations for a curve; see
  `openspec/specs/series-metadata/spec.md` and `data-pipeline/spec.md`.
- Derived series (spreads, real short rate, credit spread, ERP) compute in Python at fetch
  time from their legs — never in JS, never from FRED's precomputed spread series. Emit a
  point only where every leg reports. Round each leg before subtracting, so the legs a
  reader sees reconcile to the headline (the ERP fix).
- **Never read a sibling's `data/*.json`.** `fetch_all.py` runs fetchers in no guaranteed
  order, so a series that read another's output would depend on whether that fetch ran.
  Re-read the upstream instead (`fetch_equity_risk_premium.py` re-reads CAPE from Shiller's
  workbook through `fetch_sp500_pe.py`'s helpers).
- Drop an in-progress month. Shiller's file carries a current-month placeholder row
  (`month_is_complete()` in `fetch_sp500_pe.py`); H.15 monthly averages never do.
- Stitched series: every observation carries `source` (a catalogue slug) and `frequency`;
  log, never enforce, a seam-continuity check (`check_seam` in `fetch_gs10_long.py`).
- Write with `series_meta.write_json`. Never write under `site/`.
- Resolve a download link at fetch time when the host changes it
  (`resolve_shiller_xls_url` in `fetch_sp500_pe.py`); never hard-code a `?ver=` tag.
- After running a fetcher locally, the new `data/<id>.json` is a test fixture on `main`;
  the workflow never commits data back, and the live site is fresher.
- `fetch_yields_table.py`: rows and columns are the `ROWS`/`COLUMNS` constants — adding a
  row is one entry plus one descriptor input, which is what gives the row its own as-of clock.
