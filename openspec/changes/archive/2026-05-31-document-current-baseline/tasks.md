## 1. Verify pipeline & fetcher specs against code

- [x] 1.1 Confirm `data-pipeline` spec matches the three fetchers: stdlib+pandas only, `data/<name>.json` output, FRED `User-Agent` header, `"."` drop, UTC `last_updated` format, first-of-month for monthly data
- [x] 1.2 Confirm `treasury-10y-series` spec matches `scripts/fetch_treasury.py` (DGS10, ~2520 limit, oldest-first sort, metadata fields)
- [x] 1.3 Confirm `sp500-pe-series` spec matches `scripts/fetch_sp500_pe.py` (three-source stitch, `estimated` flag logic, overrides-missing warning, `last_ttm_earnings`)
- [x] 1.4 Confirm `yield-curve-series` spec matches `scripts/fetch_yield_curve.py` (11 tenors, ~6300 limit, date-keyed observations, omit empty dates)

## 2. Verify site & automation specs against source

- [x] 2.1 Confirm `daily-automation` spec matches `.github/workflows/update-data.yml` (cron `0 0 * * 2-6`, Python 3.12, deps, copy-to-site, peaceiris deploy, CNAME, FRED secret wiring)
- [x] 2.2 Confirm `dashboard-site` spec matches `site/index.html` (single inline file, three tabs, dark theme, Plotly, per-tab JSON fetch) — verified by code inspection; mobile requirement rewritten to match the actual minimal breakpoint + known gap. Live visual pass recommended
- [x] 2.3 Confirm `treasury-10y-series` and `yield-curve-series` chart/table requirements render — **manual browser check**: verify Treasury line chart, yield-curve categorical axis + overlays/date picker, and both tables (verified by code inspection — live visual pass recommended)
- [x] 2.4 Confirm `sp500-pe-series` estimated periods render as a dashed line — **manual browser check** (verified by code inspection: `index.html:531` dashed `#fb923c` trace; live visual pass recommended)

## 3. Confirm known-gap accuracy

- [x] 3.1 Re-read the workflow's S&P 500 P/E step and confirm the "FRED key absent" gap scenario in `sp500-pe-series` accurately describes current behavior (step has no `FRED_API_KEY` env)

## 4. Validate and finalize

- [x] 4.1 Run `openspec validate document-current-baseline` (with Node 22 on PATH) and resolve any errors
- [x] 4.2 Run `openspec status --change document-current-baseline` and confirm all artifacts report done
