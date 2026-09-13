## 1. Descriptors and shared modules (S4a)

- [x] 1.1 Write `series/dgs10.json`, `series/yield_curve.json`, `series/spreads.json`, `series/usrec.json`, `series/sp500_pe.json` per design decision 2, migrating today's header `title`/`units`/`source`/`methodology`/`description` text into `title`, `sources`, `methodology` and `notes`; seed lags DGS 1, SP500 monthly 1, USREC 5, earnings 60; mark the earnings input `status: discontinued` with the 31 Jan 2026 note; `usrec` is `kind: intervals`, `revisions: retroactive`; `yield_curve` is `kind: curve`
- [x] 1.2 `scripts/staleness.py`: add the US bond-market calendar (federal holidays by rule, Good Friday, `extra_closures`), `is_business_day`, `add_business_days`, `period_end`, `next_period_end`, `compute_due_by(last_observation, cadence, lag)`; replace the `SERIES` table with descriptor-driven `check()` reading `as_of.due_by` and per-input `due_by`, keeping its return shape and the `local`/`live` sources
- [x] 1.3 `scripts/series_meta.py`: `ids()` (from `series/*.json`), `load(id)`, `period_label(date, cadence)`, `build_as_of(...)` (dataset, per-input, per-series; roll-up over required active inputs), `write_json(path, obj)` (tmp + `os.replace`), and the one-release `last_updated` alias
- [x] 1.4 `tests/test_series_metadata.py`: descriptor required fields and enums; every `inputs[].source` slug exists in `sources`; pipeline-owned keys of `meta` match the descriptor; `as_of.due_by` and per-input `due_by` recompute; calendar fixtures from design decision 4 (Thanksgiving 2026, Labor Day 2026, Good Friday 2027, extra closure 2025-01-09, earnings 2025-09-30 → 2026-03-30); `period_label` for the three cadences

## 2. Fetchers (S4a)

- [x] 2.1 `scripts/fetch_treasury.py`: header via `series_meta`; payload unchanged
- [x] 2.2 `scripts/fetch_yield_curve.py`: header via `series_meta`, `as_of.series` per tenor; `tenors` and `tenor_months` stay top-level; payload unchanged
- [x] 2.3 `scripts/fetch_spreads.py`: header via `series_meta`, `as_of.series` for `10y2y` and `10y3m` (first observation 1976-06-01 / 1981-09-01); `series[].label` and payload unchanged
- [x] 2.4 `scripts/fetch_usrec.py`: capture the last monthly observation and its value before `collapse_to_intervals`; write `as_of.last_observation`, `period_label`, `latest_value`; `recessions` unchanged
- [x] 2.5 `scripts/fetch_sp500_pe.py`: `get_ttm_for_month()` per design decision 10 (`estimated = month >= effective_from(last) + 3 months`, dead line 188 removed); `fetch_fred_prices` drops a month unless the ET fetch date is past its last day; `as_of.inputs.price` and `as_of.inputs.earnings` (`last_observation` = last quarter end, `confirmed_through`, `value`); `last_ttm_earnings` removed
- [x] 2.6 `scripts/build_earnings_overrides.py`: read `SECTOR EPS!B2/B3/B4` into `data_as_of` / `actuals_through`; cap entries at `actuals_through`; derive the calendar quarter from `effective_from`; regenerate `data/earnings_overrides.json` and confirm the 148 entries and `ttm_eps` values are unchanged — **verification gate**
- [x] 2.7 Regenerate all five `data/*.json` with `FRED_API_KEY` set; diff payloads against the previous files on the shared date range (identical except new dates and the P/E `estimated` flags for Oct–Dec 2025) — **verification gate**

## 3. Tests (S4a)

- [x] 3.1 `tests/test_staleness.py`: parametrise over `series_meta.ids()`, read `as_of.due_by` and per-input `due_by`, compare to today's US Eastern date; add the `staleness` marker to `pytest.ini`; keep the live/local source switch
- [x] 3.2 `tests/test_data_integrity.py`: replace the `xfail` header test with the structural P/E invariants from design decision 10; add "no P/E observation dated in the current or a future month"
- [x] 3.3 `tests/conftest.py`: fixtures for `series/*.json` and `data/earnings_overrides.json`
- [x] 3.4 Full local run: `pytest -v` green with `FRED_API_KEY` set (live-site checks included), then `pytest -m "not staleness"` green offline

## 4. Workflow and dev loop (S4a)

- [x] 4.1 `.github/workflows/update-data.yml`: cron `15 23 * * 1-5`
- [x] 4.2 Seed step after checkout: `git fetch --depth=1 origin gh-pages`; for each id from `series/*.json`, `git checkout FETCH_HEAD -- data/<id>.json || echo "::warning::…"`; never the `data/` directory
- [x] 4.3 Each fetch step gets an `id` and `continue-on-error: true`
- [x] 4.4 Split the test step: `pytest -m "not staleness"` gates; a second step `pytest -m staleness` with `continue-on-error: true` and `STALENESS_SOURCE=local`, writing the per-series table to `$GITHUB_STEP_SUMMARY`
- [x] 4.5 Copy step derives its file list from `series/*.json` (a one-line Python or shell loop), replacing the five hand-written `cp` lines
- [x] 4.6 Final `if: always()` step after the deploy: `::warning::` per failed fetch (`steps.<id>.outcome`) and per overdue series; `exit 1` if any fetch step failed
- [x] 4.7 `scripts/dev.sh`: file list from `series/*.json`; `--live` downloads each `https://joemirza.com/data/<id>.json` into `data/` before serving; staleness warning now prints `due_by`
- [x] 4.8 Rollback check: `git diff` of the workflow is confined to the steps above and indentation matches siblings
- [x] 4.9 **Manual CI check (post-merge)**: `workflow_dispatch`; confirm the seed step logs five restores, all fetches succeed, the staleness summary renders, and the site redeploys. Then force one failure (e.g. temporarily bad Shiller URL on a branch run) and confirm: four fresh files, one carried forward, deploy done, job red — verified 2026-09-13: normal run (`main`, #142) restored 5/5 and showed all series "on time"; forced-failure run on throwaway branch `test/s4a-forced-fetch-failure` (broke `fetch_usrec.py`'s `SERIES_ID`, not `fetch_sp500_pe.py`'s `SHILLER_URL` — the latter is also imported by `tests/test_sp500_pe.py` and would fail the gating tests instead of exercising this path) confirmed 4 fresh + 1 carried-forward, deploy ran, final step warned and exited 1. Branch deleted, never merged

## 5. Frontend (S4b)

- [x] 5.1 Shared `loadSeries(id)` (fetch, error path) and `todayET()` (`toLocaleDateString('en-CA', {timeZone: 'America/New_York'})`); remove the four `data.last_updated` reads
- [x] 5.2 `asOfAnnotation(meta, as_of)`: bottom-left paper annotation `source_line · data through period_label`, with the P/E's two-input form and the discontinued wording; added to every chart's layout
- [x] 5.3 `freshnessBadge(as_of)`: no element when on time; `Overdue · expected by <date> · N days late` (calendar days); per-input form for multi-input datasets; discontinued inputs never badge
- [x] 5.4 Sub-tab strip (`Chart | Table | About`) per chart and an About renderer from `meta`/`as_of` per the `chart-chrome` spec; no hard-coded About text; discontinued status and note shown
- [x] 5.5 `xaxisToToday(layout)` for `kind: timeseries`; range buttons count back from today; `addRecessionBands` shades an open interval to today
- [x] 5.6 Shared `valueOnOrBefore(obs, targetISO)` with UTC-only arithmetic; the DGS10 stat tiles, P/E stats, yield-curve table and spreads table all use it and display the resolved comparison date; stat tiles show the date beside "Latest"
- [x] 5.7 Export buttons per chart: CSV (payload flattened; `date,10y2y,10y3m` for spreads, one column per tenor for the curve), JSON (the file), PNG via `toImageButtonOptions` with `filename: "<id>_<last_observation>"`; `displaylogo: false`
- [x] 5.8 Regenerate `site/data/` via `scripts/dev.sh` and run the page through `node --check` on the inline script
- [x] 5.9 **Manual browser check** — verified 2026-09-13 via Claude in Chrome against `scripts/dev.sh 8899` on regenerated local data: all four tabs render with no console errors; Chart/Table/About sub-tabs work on every card; badges correctly stay hidden (all series on time against today 2026-09-13); the P/E About tab shows the earnings input as `discontinued` with its `status_note`, and its Table sub-tab's dagger marks estimated months starting Jan 2026; the yield-curve Table sub-tab headers show resolved comparison dates (e.g. "1-Week Change (vs 3 Sep 2026)"); the spreads Table sub-tab shows a per-row resolved date; CSV exports for dgs10/spreads/yield_curve/sp500_pe matched their required column shapes exactly (spreads: `date,10y2y,10y3m` with blanks; yield curve: one column per tenor); the yield-curve PNG export (via Plotly's modebar camera button) is named `yield_curve_2026-09-10.png` and the in-chart source line survives the export. Found and fixed one bug in the process: `.badge`'s own `display: inline-block` was overriding the browser's `[hidden]` rule (author CSS beats the UA stylesheet regardless of specificity), so an empty badge pill was showing on every chart; added an explicit `.badge[hidden] { display: none; }` rule. Did not test `dev.sh --live` (would require deploying first — the local-data badge-hidden state was verified instead, since local data is fresh)
- [x] 5.10 Remove the `last_updated` alias from `series_meta` once 5.1 is deployed — removed `last_updated_alias()` from `scripts/series_meta.py` and its call site from all five fetchers; regenerated all five `data/*.json` and confirmed `last_updated` is absent from each; `pytest -m "not staleness"` (57 tests) still green

## 6. Docs and close

- [x] 6.1 `CLAUDE.md`: Key Files rows for `series/` and `scripts/series_meta.py`; Architecture data-flow paragraph (seed from gh-pages, no commit-back, `main`'s `data/` are fixtures); Correctness Tests (metadata test, `staleness` marker); remove the "known failing check" paragraph; changelog entries for S4a and S4b
- [x] 6.2 `ARCHITECTURE.md`: decision-log entries for the header contract, the freshness rule and the failure policy; fix the chart 2 roadmap row
- [x] 6.3 Session Plan "Where things stand" and HANDOFF after each S4 half — S4a handoff/bullet already existed; added the S4b bullet to Session Plan and `HANDOFF — 13 Sep 2026 (S4b).md`, which supersedes the S4a one

## 7. Validate

- [x] 7.1 `openspec validate s3-series-metadata` clean and `openspec status --change s3-series-metadata` all done, before S4 starts (done in S3) and again before archive — **both run for real**: `openspec` (`@fission-ai/openspec@1.3.1`) turned out to be installed already, just under nvm's Node v18.20.8 rather than this shell's active v22.22.3, so it wasn't on PATH (`which openspec` found nothing); invoking `/Users/joemirza/.nvm/versions/node/v18.20.8/bin/openspec` directly worked fine. `validate s3-series-metadata` → "Change 's3-series-metadata' is valid"; `status --change s3-series-metadata` → all 4 artifacts (proposal/design/specs/tasks) complete
