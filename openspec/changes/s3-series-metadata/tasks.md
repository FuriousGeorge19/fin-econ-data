## 1. Descriptors and shared modules (S4a)

- [ ] 1.1 Write `series/dgs10.json`, `series/yield_curve.json`, `series/spreads.json`, `series/usrec.json`, `series/sp500_pe.json` per design decision 2, migrating today's header `title`/`units`/`source`/`methodology`/`description` text into `title`, `sources`, `methodology` and `notes`; seed lags DGS 1, SP500 monthly 1, USREC 5, earnings 60; mark the earnings input `status: discontinued` with the 31 Jan 2026 note; `usrec` is `kind: intervals`, `revisions: retroactive`; `yield_curve` is `kind: curve`
- [ ] 1.2 `scripts/staleness.py`: add the US bond-market calendar (federal holidays by rule, Good Friday, `extra_closures`), `is_business_day`, `add_business_days`, `period_end`, `next_period_end`, `compute_due_by(last_observation, cadence, lag)`; replace the `SERIES` table with descriptor-driven `check()` reading `as_of.due_by` and per-input `due_by`, keeping its return shape and the `local`/`live` sources
- [ ] 1.3 `scripts/series_meta.py`: `ids()` (from `series/*.json`), `load(id)`, `period_label(date, cadence)`, `build_as_of(...)` (dataset, per-input, per-series; roll-up over required active inputs), `write_json(path, obj)` (tmp + `os.replace`), and the one-release `last_updated` alias
- [ ] 1.4 `tests/test_series_metadata.py`: descriptor required fields and enums; every `inputs[].source` slug exists in `sources`; pipeline-owned keys of `meta` match the descriptor; `as_of.due_by` and per-input `due_by` recompute; calendar fixtures from design decision 4 (Thanksgiving 2026, Labor Day 2026, Good Friday 2027, extra closure 2025-01-09, earnings 2025-09-30 → 2026-03-30); `period_label` for the three cadences

## 2. Fetchers (S4a)

- [ ] 2.1 `scripts/fetch_treasury.py`: header via `series_meta`; payload unchanged
- [ ] 2.2 `scripts/fetch_yield_curve.py`: header via `series_meta`, `as_of.series` per tenor; `tenors` and `tenor_months` stay top-level; payload unchanged
- [ ] 2.3 `scripts/fetch_spreads.py`: header via `series_meta`, `as_of.series` for `10y2y` and `10y3m` (first observation 1976-06-01 / 1981-09-01); `series[].label` and payload unchanged
- [ ] 2.4 `scripts/fetch_usrec.py`: capture the last monthly observation and its value before `collapse_to_intervals`; write `as_of.last_observation`, `period_label`, `latest_value`; `recessions` unchanged
- [ ] 2.5 `scripts/fetch_sp500_pe.py`: `get_ttm_for_month()` per design decision 10 (`estimated = month >= effective_from(last) + 3 months`, dead line 188 removed); `fetch_fred_prices` drops a month unless the ET fetch date is past its last day; `as_of.inputs.price` and `as_of.inputs.earnings` (`last_observation` = last quarter end, `confirmed_through`, `value`); `last_ttm_earnings` removed
- [ ] 2.6 `scripts/build_earnings_overrides.py`: read `SECTOR EPS!B2/B3/B4` into `data_as_of` / `actuals_through`; cap entries at `actuals_through`; derive the calendar quarter from `effective_from`; regenerate `data/earnings_overrides.json` and confirm the 148 entries and `ttm_eps` values are unchanged — **verification gate**
- [ ] 2.7 Regenerate all five `data/*.json` with `FRED_API_KEY` set; diff payloads against the previous files on the shared date range (identical except new dates and the P/E `estimated` flags for Oct–Dec 2025) — **verification gate**

## 3. Tests (S4a)

- [ ] 3.1 `tests/test_staleness.py`: parametrise over `series_meta.ids()`, read `as_of.due_by` and per-input `due_by`, compare to today's US Eastern date; add the `staleness` marker to `pytest.ini`; keep the live/local source switch
- [ ] 3.2 `tests/test_data_integrity.py`: replace the `xfail` header test with the structural P/E invariants from design decision 10; add "no P/E observation dated in the current or a future month"
- [ ] 3.3 `tests/conftest.py`: fixtures for `series/*.json` and `data/earnings_overrides.json`
- [ ] 3.4 Full local run: `pytest -v` green with `FRED_API_KEY` set (live-site checks included), then `pytest -m "not staleness"` green offline

## 4. Workflow and dev loop (S4a)

- [ ] 4.1 `.github/workflows/update-data.yml`: cron `15 23 * * 1-5`
- [ ] 4.2 Seed step after checkout: `git fetch --depth=1 origin gh-pages`; for each id from `series/*.json`, `git checkout FETCH_HEAD -- data/<id>.json || echo "::warning::…"`; never the `data/` directory
- [ ] 4.3 Each fetch step gets an `id` and `continue-on-error: true`
- [ ] 4.4 Split the test step: `pytest -m "not staleness"` gates; a second step `pytest -m staleness` with `continue-on-error: true` and `STALENESS_SOURCE=local`, writing the per-series table to `$GITHUB_STEP_SUMMARY`
- [ ] 4.5 Copy step derives its file list from `series/*.json` (a one-line Python or shell loop), replacing the five hand-written `cp` lines
- [ ] 4.6 Final `if: always()` step after the deploy: `::warning::` per failed fetch (`steps.<id>.outcome`) and per overdue series; `exit 1` if any fetch step failed
- [ ] 4.7 `scripts/dev.sh`: file list from `series/*.json`; `--live` downloads each `https://joemirza.com/data/<id>.json` into `data/` before serving; staleness warning now prints `due_by`
- [ ] 4.8 Rollback check: `git diff` of the workflow is confined to the steps above and indentation matches siblings
- [ ] 4.9 **Manual CI check (post-merge)**: `workflow_dispatch`; confirm the seed step logs five restores, all fetches succeed, the staleness summary renders, and the site redeploys. Then force one failure (e.g. temporarily bad Shiller URL on a branch run) and confirm: four fresh files, one carried forward, deploy done, job red

## 5. Frontend (S4b)

- [ ] 5.1 Shared `loadSeries(id)` (fetch, error path) and `todayET()` (`toLocaleDateString('en-CA', {timeZone: 'America/New_York'})`); remove the four `data.last_updated` reads
- [ ] 5.2 `asOfAnnotation(meta, as_of)`: bottom-left paper annotation `source_line · data through period_label`, with the P/E's two-input form and the discontinued wording; added to every chart's layout
- [ ] 5.3 `freshnessBadge(as_of)`: no element when on time; `Overdue · expected by <date> · N days late` (calendar days); per-input form for multi-input datasets; discontinued inputs never badge
- [ ] 5.4 Sub-tab strip (`Chart | Table | About`) per chart and an About renderer from `meta`/`as_of` per the `chart-chrome` spec; no hard-coded About text; discontinued status and note shown
- [ ] 5.5 `xaxisToToday(layout)` for `kind: timeseries`; range buttons count back from today; `addRecessionBands` shades an open interval to today
- [ ] 5.6 Shared `valueOnOrBefore(obs, targetISO)` with UTC-only arithmetic; the DGS10 stat tiles, P/E stats, yield-curve table and spreads table all use it and display the resolved comparison date; stat tiles show the date beside "Latest"
- [ ] 5.7 Export buttons per chart: CSV (payload flattened; `date,10y2y,10y3m` for spreads, one column per tenor for the curve), JSON (the file), PNG via `toImageButtonOptions` with `filename: "<id>_<last_observation>"`; `displaylogo: false`
- [ ] 5.8 Regenerate `site/data/` via `scripts/dev.sh` and run the page through `node --check` on the inline script
- [ ] 5.9 **Manual browser check**: each tab renders on local data with no console errors; the source line is visible in a PNG export; the About tab shows sources, inputs, `due_by`, revision sentence; the P/E dashed segment starts at Jan 2026; the badge appears when local data is old and disappears with `dev.sh --live`
- [ ] 5.10 Remove the `last_updated` alias from `series_meta` once 5.1 is deployed

## 6. Docs and close

- [ ] 6.1 `CLAUDE.md`: Key Files rows for `series/` and `scripts/series_meta.py`; Architecture data-flow paragraph (seed from gh-pages, no commit-back, `main`'s `data/` are fixtures); Correctness Tests (metadata test, `staleness` marker); remove the "known failing check" paragraph; changelog entries for S4a and S4b
- [ ] 6.2 `ARCHITECTURE.md`: decision-log entries for the header contract, the freshness rule and the failure policy; fix the chart 2 roadmap row
- [ ] 6.3 Session Plan "Where things stand" and HANDOFF after each S4 half

## 7. Validate

- [ ] 7.1 `openspec validate s3-series-metadata` clean and `openspec status --change s3-series-metadata` all done, before S4 starts (done in S3) and again before archive
