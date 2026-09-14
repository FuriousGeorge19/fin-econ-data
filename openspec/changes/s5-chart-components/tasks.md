## 1. Site config, generator, ignore rules (S6a)

- [x] 1.1 `pages/site.json`: site name and the three sections (`economy` "Economy", `markets` "Markets", `rates` "Rates & Yields") with taglines from the fixed-income conversation, per design decision 3
- [x] 1.2 `scripts/build_site.py` (stdlib only): load `pages/site.json`, every `series/*.json` and every `pages/*.json`; write `site/charts/<id>/index.html` for each descriptor with `presentation`, `site/<section>/index.html` (automatic grid, `half` blocks, sorted by `order`), and `site/<section>/<slug>/index.html` / `site/index.html` for manifests; each page = shell (`<title>`, `css/site.css`, every `css/charts/*.css`, Plotly 2.35.0 `<script>`, static two-row nav with the current item marked) + one `<div class="card" data-block="…">` per block + one inline `<script type="application/json" id="page">` carrying `{page, blocks:[{id, title, short_title, summary, href, presentation, size, preset}]}` + `<script type="module" src="/js/app.js">`; copy `data/<id>.json` → `site/data/` for every id; print every path written; per design decisions 1–3 and 6
- [x] 1.3 Generator validations that fail the build: `presentation.chart.type` module exists at `site/js/charts/<type>.js`; `sections` ⊆ `pages/site.json`; block `chart` names a descriptor with `presentation`; manifest `section` exists; presets match `^\d+[MY]$|YTD|All`; a descriptor id is not `timeseries` or `curve`; per design decisions 4, 6 and the risk list
- [x] 1.4 Do **not** write `site/index.html` unless `pages/home.json` exists (migration rule, design decision 2)
- [x] 1.5 `series/dgs10.json`: add `"fetcher": "fetch_treasury.py"` and the `presentation` block from design decision 4 (sections `rates`, `economy`; order 5; summary from today's subtitle; `timeseries`, `%` / `.2f`, presets `1M 6M 1Y 5Y All`, `recessions: false`, `stats: true`, `table {kind: recent, rows: 30}`)
- [x] 1.6 `.gitignore`: add `site/data/` and `site/**/index.html`; delete the stray `.envrc.DS_Store` line
- [x] 1.7 `scripts/dev.sh`: replace the copy loop with `python3 scripts/build_site.py`; keep `--live`, the staleness print and the port argument

## 2. Fetch runner and workflow (S6a)

- [x] 2.1 `scripts/fetch_all.py`: for each `series_meta.ids()`, run `scripts/<fetcher or fetch_<id>.py>` as a subprocess inside `::group::<id>` … `::endgroup::` with elapsed seconds; try/except per series; write `data/fetch_status.json` (`{id: {ok, returncode, seconds}}`); always exit 0; per design decision 7
- [x] 2.2 `.github/workflows/update-data.yml`: replace the five fetch steps (and the `OUTCOME_*` env and the id list in the summary step) with one `python scripts/fetch_all.py` step carrying `FRED_API_KEY`; replace the copy step with `python scripts/build_site.py`; the summary step and the final `if: always()` step read `data/fetch_status.json`; seed step, pytest gate, staleness step, deploy step unchanged
- [x] 2.3 Rollback check: `git diff` of the workflow is confined to those steps and indentation matches siblings
- [x] 2.4 **Manual CI check (post-merge)**: `workflow_dispatch`; confirm five `::group::` blocks, `fetch_status.json` all `ok`, the summary table renders, the generated pages are on `gh-pages` beside the old `index.html`, and `http://joemirza.com/charts/dgs10/` loads. Then a forced failure on a throwaway branch (break `fetch_usrec.py`'s series id, as in S4a task 4.9) confirms the carried-forward file, the deploy, and the red job

## 3. Tests (S6a)

- [x] 3.1 `tests/test_build_site.py`: run the generator into `tmp_path`; assert a page per descriptor with `presentation`; section pages list their charts in `order`; manifests resolve; the inline `#page` JSON parses; each data file has the shape its type expects (`series` or `observations` for `timeseries`, `tenors` for `curve`); every `type` module and `fetcher` script exists; no hex/rgb literal under `site/js`; no `margin`, `rangeslider`, `height` or `getElementById` outside `site/js/lib/plotly-layout.js` and `site/js/lib/card.js`; per design decision 8
- [x] 3.2 `tests/test_series_metadata.py`: `presentation` allowed keys and enums (`sections`, `order`, `summary`, `chart`, `stats`, `table`; `chart.type`, `y`, `presets`, `recessions`, `zeroline`, `overlays`, `custom_date`, `traces`); presets grammar; `sections` ⊆ `pages/site.json`; `fetcher` exists when given
- [x] 3.3 Full local run: `pytest -m "not staleness"` green; then `pytest` with `FRED_API_KEY` set

## 4. Shared runtime and the timeseries type (S6b)

- [x] 4.1 `site/css/site.css`: today's CSS moved verbatim (including `.est-badge` and `.yc-*`), the six existing tokens plus the S5b token names from design decision 5 (values from `site/css/tokens.css` if S5b has landed, otherwise today's hex values); card grid rules for `full | half | third` and the 640 px one-column rule
- [x] 4.2 `site/js/lib/dates.js`, `asof.js`, `export.js`, `data.js` (root-relative `/data/`), `theme.js` (reads the tokens into `ctx.theme`): today's shared functions moved into modules, one `fmtChange` replacing the four copies
- [x] 4.3 `site/js/lib/plotly-layout.js`: `baseLayout(ctx)` (transparent paper, margins with `margin.b` reserved for the source-line annotation, axis chrome and font from `ctx.theme`, legend top-horizontal, hover x-format from `meta.cadence`), `xaxisToToday` with `autorangeoptions`, start = min x over traces; the only file that sets `margin`/legend position/`rangeslider`/`height`; `PLOT_CONFIG` with `displaylogo: false` and `toImageButtonOptions`
- [x] 4.4 `site/js/charts/timeseries.js`: `render`, `stats`, `table` (`recent` and `changes` kinds), default `csv` (outer join on date, columns `date,<key>…`); the payload convention and options from design decision 4; recession bands from `ctx.recessions` in the initial `layout.shapes`; no module-level state, no `getElementById`, no colour literal

## 5. Card chrome, presets, app entry (S6b)

- [x] 5.1 `site/js/lib/presets.js`: buttons from `presentation.chart.presets`; `Plotly.relayout` with `[today − n, today]`, YTD, and `xaxis.autorange: true` for All; active state on `plotly_relayout`; `applyInitial(preset)`
- [x] 5.2 `site/js/lib/card.js`: `mount(block)` per design decision 5 — build the card DOM with Loading in every panel, eager fetch (+ `usrec.json` when `recessions`), error message owned here, badge/stats/table/About/exports as the fetch resolves, `import('/js/charts/<type>.js')` then `render` once, `Plotly.Plots.resize` on return to the Chart sub-tab, `destroy()`/`render()` on `themechange`, `initialPreset` applied after render
- [x] 5.3 `site/js/app.js`: parse `#page`, `mount` every block, compute `todayET()` once
- [x] 5.4 **Manual browser check** — `scripts/dev.sh`, then `/charts/dgs10/` and `/rates/` on first show: `_fullLayout.width === clientWidth`, zero console errors, All/reset = `[first_observation, today]`, presets relayout correctly, screenshot matches today's 10Y tab (chart, stats, table, About, exports); the old `/` unchanged (manual browser check)

## 6. Port the other three charts (S7 workflow, 3 + 1 agents)

- [x] 6.1 spreads → `timeseries` by config only: `series/spreads.json` `presentation` (economy, order 20, `series` payload gives two traces, `+.2f`, `zeroline`, `recessions: true`, presets `1Y 5Y 10Y 25Y All`, `stats: false`, `table {kind: changes, windows: [1M, 1Y]}`); hover format changes to the full date (intended); zero shared-file edits
- [x] 6.2 sp500_pe → custom module `site/js/charts/sp500_pe.js` importing `baseLayout`/`xaxisToToday`; confirmed + dashed estimated trace with the prepended last-confirmed point; `stats` (latest as `period_label`, long-term average over confirmed, 10Y high/low), `table` (24 rows, dagger `note`), `csv` (`date,pe,price,earnings,estimated`); `series/sp500_pe.json` `presentation` (markets, order 7, type `sp500_pe`, presets `1Y 10Y 25Y 50Y All`, `recessions: false`)
- [x] 6.3 yield_curve → new type `site/js/charts/curve.js`: closure state only, controls (overlay toggles, custom date with min/max from data) in `ctx.slots.controls`, `Plotly.react` on toggle, categorical tenor axis, `table` with resolved comparison dates in column titles, wide `csv`; `series/yield_curve.json` `presentation` (rates, order 10, `curve`, `overlays 1w 1m 1y 5y`, `custom_date: true`, `table: true`)
- [x] 6.4 Verifier: `python scripts/build_site.py`, `pytest -m "not staleness"`, then every page on first show in Chrome (width check, console, screenshots against today's tabs); report per agent (manual browser check)

## 7. Cutover and docs

- [ ] 7.1 `pages/home.json`: `slug home`, grid, the four charts at `half` in the order 10Y, yield curve, spreads, P/E
- [ ] 7.2 `git rm --cached site/index.html site/data/*.json`; run the generator; confirm `/` is the generated home page and `git status` is clean
- [ ] 7.3 Docs: `CLAUDE.md` (architecture block, key files, dev pattern "adding a series", iteration loop, changelog), `ARCHITECTURE.md` (decision-log entry; §5/§6 marked done), `HOW-IT-WORKS.md` rewrite (stale since S3)
- [ ] 7.4 **Manual browser check** — live site after the deploy: `/`, each section page, each chart page, one composite page if any; phone width 400 px on `/` (manual browser check)

## 8. Validate

- [ ] 8.1 `openspec validate s5-chart-components` clean before any build session; `openspec archive` after 7.4
