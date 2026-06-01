## Why

Chart #2 from `ARCHITECTURE.md` — the 10y-2y and 10y-3m Treasury yield spreads with
NBER recession shading — is the headline "where are we in the cycle?" view. Building it
now also trips three of the architecture's planned evolution triggers (shared FRED
utility, recession shading as shared data, Python-side derived series), so this change
both ships a chart and lays reusable groundwork the next several charts depend on.

## What Changes

- Add a **shared `scripts/fred_utils.py`** module (`fetch_series(series_id, limit)` and
  the FRED boilerplate: URL construction, `User-Agent`, `"."` filtering, key handling).
  Conservatively adapt the three existing fetchers to use it — same behavior, less
  duplication.
- Add **`scripts/fetch_spreads.py`**: fetches daily DGS10, DGS2, DGS3MO via `fred_utils`,
  computes the 10y-2y and 10y-3m spreads in Python (date-aligned), writes `data/spreads.json`.
- Add **`scripts/fetch_usrec.py`**: fetches the USREC recession indicator, writes
  `data/usrec.json` as a reusable dataset for this and future charts (charts 3/5/7/8).
- Add a flat **"Treasury Spreads" tab** to `site/index.html`: a dual-line spreads chart
  with a zero line, NBER recession bands via a new shared `addRecessionBands()` helper,
  and a current-values table (both spreads, latest value, period changes).
- **Workflow**: two new fetch steps (USREC, spreads), both with `FRED_API_KEY`, plus the
  two `cp` lines into `site/data/`.

## Capabilities

### New Capabilities
- `treasury-spreads-series`: the spreads fetcher contract, `data/spreads.json` shape, the
  Python-side derived-spread computation, and the dashboard tab (chart + recession-band
  overlay + current-values table).
- `nber-recession-data`: the USREC fetcher contract and `data/usrec.json` shape, framed
  as a shared dataset reusable across multiple charts.

### Modified Capabilities
- `data-pipeline`: clarify that shared **internal** Python utility modules under
  `scripts/` are permitted; the "no shared framework" rule is about external runtime
  dependencies (no `requirements.txt`, build step, or web framework), not internal reuse.
- `daily-automation`: the workflow gains the USREC and spreads fetch steps (each with
  `FRED_API_KEY`) and their copy-to-site lines.

## Impact

- **New code**: `scripts/fred_utils.py`, `scripts/fetch_spreads.py`, `scripts/fetch_usrec.py`,
  `data/spreads.json`, `data/usrec.json`, a new tab + `addRecessionBands()` in `site/index.html`.
- **Modified code**: `scripts/fetch_treasury.py`, `scripts/fetch_sp500_pe.py`,
  `scripts/fetch_yield_curve.py` (adopt `fred_utils`, behavior unchanged);
  `.github/workflows/update-data.yml` (two steps + two copy lines).
- **Not affected**: existing data contracts (`dgs10.json`, `sp500_pe.json`,
  `yield_curve.json`) keep their shapes; the three existing tabs are untouched. The
  `dashboard-site` spec does not change (tab labels are owned by per-series specs).
- **Rollback**: the workflow change is the only CI-touching part — revert the two added
  steps + two copy lines to restore prior behavior. The new scripts/tab are additive;
  removing the tab block and the two scripts fully reverts. The `fred_utils` refactor is
  behavior-preserving, so reverting it is independent of the chart.
