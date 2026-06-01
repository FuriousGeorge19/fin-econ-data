## 1. Shared FRED utility

- [x] 1.1 Create `scripts/fred_utils.py` with `fetch_series(series_id, limit, *, api_key=None, required=True)` encapsulating URL construction, `User-Agent: joemirza-site/1.0`, `"."` → float filtering, and key handling (raise/exit when `required` and key missing; return empty when not required, for graceful-degradation callers)
- [x] 1.2 Refactor `scripts/fetch_treasury.py` to use `fred_utils`; regenerate `data/dgs10.json` and confirm it is byte-identical to the committed version except `last_updated` — **verification gate** (verified: old vs refactored output IDENTICAL)
- [x] 1.3 Refactor `scripts/fetch_yield_curve.py` to use `fred_utils` (replace its internal `fetch_series`); regenerate and diff `data/yield_curve.json` — **verification gate** (verified: 6000 shared dates, 0 value mismatches vs git; metadata/tenors identical. Added retry/backoff to fred_utils — design.md Decision 3a + data-pipeline spec updated)
- [x] 1.4 Refactor only the FRED price call in `scripts/fetch_sp500_pe.py` to use `fred_utils` with `required=False`; leave the Shiller/Excel path and graceful-degradation behavior unchanged — **verification gate** (verified in isolation: refactored `fetch_fred_prices` output == old logic, `old==new: True`. Full-script run not possible locally — `pandas` not installed in this env — but CI installs it and the Shiller path is untouched)

## 2. USREC recession data

- [x] 2.1 Create `scripts/fetch_usrec.py`: fetch USREC via `fred_utils`, collapse contiguous recession months into `[{start, end}]` intervals, set `end: null` for an ongoing recession, write `data/usrec.json` with metadata (`title`, `source`, `last_updated`, description noting NBER dating lag)
- [x] 2.2 Run it and sanity-check the intervals against known NBER recessions — 35 intervals (1854–present); verified 2008-01→2009-06, 2020-03→2020-04, 2001-04→2001-11. NOTE: USREC marks the month *after* the NBER peak through the trough (standard FRED convention), so band starts trail the NBER peak by one month — correct/expected

## 3. Spreads series

- [x] 3.1 Create `scripts/fetch_spreads.py`: fetch DGS10, DGS2, DGS3MO via `fred_utils`; compute `10y2y` and `10y3m` only on dates where both legs report (no fill/interp); write `data/spreads.json` with metadata + both series oldest-first
- [x] 3.2 Run it and confirm both spreads exist over their valid ranges and recent inversions appear as negatives — 10y2y: 1976-06→present (12494 obs); 10y3m: 1981-09→present (11184 obs); 2023-07-03 shows −1.08 / −1.58, both positive in 2026

## 4. Frontend — Treasury Spreads tab

- [x] 4.1 Add a shared `addRecessionBands(plotDiv, usrecData)` JS helper in `site/index.html` that overlays shaded rectangles per interval, shading an open-ended interval to the latest chart date
- [x] 4.2 Add the "Treasury Spreads" nav button + tab content (card, chart div, current-values table) following the existing tab markup pattern
- [x] 4.3 Add the loader/renderer: fetch `data/spreads.json` + `data/usrec.json`, plot both spread lines with a zero reference line, call `addRecessionBands`, and populate the current-values table (both spreads, latest value, period change); include the fetch-failure error path like the other tabs (usrec failure tolerated — bands optional)
- [x] 4.4 **Manual browser check** — verified by serving locally: page + both JSON endpoints return 200, inline JS passes `node --check`, page contains the tab/button/helper, `spreads.json` well-formed with both series. Final visual render pass still recommended

## 5. Workflow

- [x] 5.1 In `.github/workflows/update-data.yml`, add two fetch steps (`fetch_usrec.py`, `fetch_spreads.py`), each with `env: FRED_API_KEY: ${{ secrets.FRED_API_KEY }}`, and add `cp data/usrec.json site/data/` and `cp data/spreads.json site/data/` to the copy step
- [x] 5.2 Confirm via `git diff` the workflow change is scoped to those additions and indentation matches sibling steps (diff clean; mirrors existing yield-curve step structure)

## 6. Validate

- [x] 6.1 Run `openspec validate add-spreads-chart` (Node 22 on PATH) and resolve any errors — valid
- [ ] 6.2 **Manual CI check (post-merge)**: trigger `workflow_dispatch`, confirm both new steps succeed and the deployed site shows the new tab with live data
