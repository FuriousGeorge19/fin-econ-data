## Context

This is the most substantial change of Cycle 1: two new fetch scripts, two new JSON
contracts, a shared `fred_utils` module that the three existing fetchers adopt, a new
dashboard tab with a reusable recession-shading helper, two new capability specs, and a
modification to the `data-pipeline` baseline. It implements Chart #2 from `ARCHITECTURE.md`
and deliberately trips three planned evolution triggers at once (Trigger #1 shared FRED
utility, Trigger #2 recession shading as shared data, Trigger #3 Python-side derived
series) because Chart #2 is the first chart that needs all three, and doing them now
avoids three separate refactors later.

The existing system: three fetchers each carry their own FRED boilerplate (the yield-curve
script already has an internal `fetch_series` that is the natural generalization seed).
`site/index.html` is a single file with three tabs, each fetching one JSON and rendering a
Plotly chart + table. The daily workflow runs the fetchers, copies JSON into `site/data/`,
and deploys to Pages.

## Goals / Non-Goals

**Goals:**
- Ship the 10y-2y / 10y-3m spreads chart with NBER recession shading and a current-values table.
- Extract `scripts/fred_utils.py` and have all FRED-consuming fetchers use it, removing
  duplicated boilerplate without changing any existing output.
- Produce `data/usrec.json` as a clean, reusable shared dataset (not coupled to spreads).
- Keep each fetcher independent and the JSON-file contract intact.

**Non-Goals (explicitly out of scope — later `ARCHITECTURE.md` triggers):**
- Lazy-loading of tab data (all series still fetch on page load).
- Splitting `site/index.html` into separate JS files (Trigger #5).
- Section-based nav grouping — Economy / Markets / Rates (Trigger #6).
- A monolithic `fetch_fred_series.py` driven by a config dict (the "also consider" in
  Trigger #1). `fred_utils` is a helper module, not a unified fetcher.
- Parallel execution in the GitHub Actions workflow.
- Reading one fetcher's output from another (no `data/yield_curve.json` reuse in spreads).

If any of these turns out to be genuinely required to land the change cleanly, stop and
flag it rather than expanding scope.

## Decisions

### 1. Daily DGS series, not monthly GS — an intentional divergence from ARCHITECTURE.md

`ARCHITECTURE.md`'s Chart #2 row lists the inputs as **GS10, GS2, TB3MS** (all *monthly*
FRED series). This change instead uses the **daily** constant-maturity series **DGS10,
DGS2, DGS3MO**. This divergence is deliberate:

- **Daily is the canonical convention for spread/recession charts.** FRED's own published
  spread series — `T10Y2Y` and `T10Y3M` — are daily, and the 10y-3m in particular is the
  academically favored recession predictor, tracked daily.
- **Single time grain keeps the dashboard coherent.** We already fetch the daily DGS
  equivalents for the yield-curve tab; using daily here means every rates series shares one
  grain, and the recession-band overlay (a date-range concept) aligns cleanly.
- **No information loss vs. the doc's intent.** The chart's analytical purpose (cycle
  positioning, inversion episodes) is better served at daily resolution.

`ARCHITECTURE.md` is a planning document, not a contract; this records the as-built choice
diverging from it. (A follow-up doc-sync of the Chart #2 row is optional housekeeping, not
part of this change.)

### 2. Compute spreads in Python at fetch time; do not use FRED's precomputed T10Y2Y/T10Y3M

Per `config.yaml`'s conviction and Trigger #3, `fetch_spreads.py` pulls the three component
series and computes `10y2y = DGS10 - DGS2` and `10y3m = DGS10 - DGS3MO` itself, date-aligning
in Python. We do **not** fetch FRED's ready-made `T10Y2Y`/`T10Y3M`, even though they exist.
- *Why not the precomputed series:* the project's standing convention is that derived series
  are computed and inspectable in our own JSON; pulling components keeps the door open to
  derived variants (e.g. a different short tenor) and keeps the "compute-in-Python" rule
  uniform across charts 2/5/7.
- *Date alignment:* a spread is only defined on dates where both legs report. The script
  emits a spread observation only for dates present in both component series; non-overlapping
  dates are omitted (no forward-fill, no interpolation) — consistent with the pipeline's
  missing-value rule.

### 3. `fred_utils.py` is a thin shared module; existing fetchers adopt it conservatively

Extract `fetch_series(series_id, limit, *, api_key=None, ...)` plus the shared concerns
(URL building, `User-Agent: joemirza-site/1.0`, `"."` filtering → floats, missing-key
error, **and rate-limit/transient-error retry**). The three existing fetchers are
refactored to call it, deleting their inline copies. The yield-curve script's internal
`fetch_series` is the template.

Refactor scope is **behavior-preserving on success, plus added resilience**: for any
successful fetch the output bytes, ordering, limits, and the missing-key error are
identical to before. The one intentional behavior change is failure-under-load — see the
rate-limiting note below.
- *Alternative considered — new scripts only, leave the old three alone:* smaller blast
  radius, but leaves three copies of the boilerplate and contradicts Trigger #1's
  "generalize it." Chosen against because the duplication is exactly what the trigger exists
  to remove, and the refactor is mechanical and verifiable against committed JSON.
- *Alternative considered — monolithic config-driven fetcher:* explicitly out of scope (see
  Non-Goals); too much, too early, and reduces modularity.

### 3a. Rate-limit handling lives in `fred_utils` (revised during implementation)

`ARCHITECTURE.md` Trigger #1 explicitly lists "rate limiting" as a boilerplate concern
`fred_utils` should own. The committed fetchers had none: the yield-curve script pulls 11
series in a tight loop and a single FRED `HTTP 429` aborts the whole run via `sys.exit(1)`.
This change adds two more FRED-fetching scripts (spreads, USREC), increasing burst load, and
the 429 was in fact hit during implementation. `fred_utils.fetch_series` therefore retries
`429`/`5xx` and transient network errors with bounded exponential backoff (4 attempts: 2s,
4s, 8s, 16s), honoring a `Retry-After` header when present.

This is the deliberate exception to "strictly behavior-preserving": previously a 429 aborted
the run, now it is retried. On success the output is byte-identical to a single call — only
the failure-under-load path changed, and strictly for the better. Captured here rather than
silently introduced.
- *Alternative considered — fixed inter-request sleep in the multi-series fetchers:* lighter,
  but doesn't help a cold 429 and isn't reusable; rejected in favor of centralized retry.

### 4. USREC is its own fetcher and its own dataset

`fetch_usrec.py` → `data/usrec.json`, independent of spreads, because USREC is shared by
charts 2/3/5/7/8. Modeling it as a standalone capability (`nber-recession-data`) now means
future charts depend on a stable contract rather than re-deriving recession bands.
- USREC is a monthly 0/1 indicator. Rather than ship ~900 monthly points, the fetcher
  collapses runs into recession **intervals** (`[{start, end}]`) since that is exactly what
  band-shading consumes; the raw monthly series is not needed by the frontend. The JSON also
  notes ongoing recessions (open-ended `end: null`) so the helper can shade to the chart edge.

### 5. Recession shading: shared JS helper, but the *requirement* binds to the chart

Add `addRecessionBands(plotDiv, usrecData)` to `site/index.html` (Trigger #2) so charts
3/5/7/8 reuse it. The helper is a dashboard implementation detail; the normative spec
requirement lives in `treasury-spreads-series` and states that the spreads chart renders
NBER recession periods as overlay shading. This keeps the spec about observable behavior
(bands appear on the chart) rather than about a particular function existing.

### 6. Spec decomposition

- **NEW `treasury-spreads-series`** — fetcher contract, `spreads.json` shape, the
  derived-spread computation + date alignment, the tab + chart contract (dual line, zero
  reference line), the recession-band overlay requirement, the current-values table
  convention, and the "Treasury Spreads" tab label.
- **NEW `nber-recession-data`** — USREC fetcher contract and `usrec.json` interval shape,
  framed as shared/reusable.
- **MODIFIED `data-pipeline`** — clarify the internal-module vs external-framework
  distinction in the "Per-series fetch script" requirement, and broaden "FRED access
  pattern" to name `fred_utils` as the shared access path.
- **MODIFIED `daily-automation`** — two new fetch steps (with `FRED_API_KEY`) and their
  copy-to-site lines.
- **`dashboard-site` unchanged** — per the prior baseline refactor, tab labels are owned by
  each series' own spec; the dashboard spec is agnostic to which series exist.

## Risks / Trade-offs

- **Refactoring three working fetchers could change their output.** → Refactor is
  behavior-preserving on success; verify by running the committed vs refactored script
  back-to-back and diffing their output (identical except `last_updated`). Where FRED
  rate-limiting prevents a clean back-to-back baseline (the committed yield-curve script
  has no retry), fall back to diffing the refactored output against the git-committed JSON
  on the intersection of dates (new dates are expected data drift). Tasks call this out as a gate.
- **`fetch_sp500_pe.py` is only partly a FRED consumer** (its primary source is Shiller; FRED
  is the price extension). → Only its FRED price call moves to `fred_utils`; the Shiller/Excel
  path and its graceful-degradation-on-missing-key behavior stay exactly as-is. `fred_utils`
  must therefore support the "missing key" case without `sys.exit` for callers that degrade,
  while FRED-primary callers still exit — handle via a parameter/return contract, not a hard exit inside the util.
- **Spread date alignment / sparse early history.** DGS2 begins 1976, DGS3MO 1982, DGS10
  1962. The 10y-2y series simply starts when both legs exist; the chart shows each spread
  over its own valid range. No fabricated early values.
- **USREC release lag.** NBER dates recessions with long lags; `usrec.json` reflects only
  officially dated periods, so the most recent months may show no band even in a downturn.
  This is correct behavior, not a bug — note it in the data's `source`/`description`.
- **Open-ended current recession.** If USREC's latest value is 1, the final interval has
  `end: null`; `addRecessionBands` must shade to the latest chart date. Tested via the
  helper, not assumed.
- **Growing page weight.** Another always-on-load fetch (two more JSONs). Acceptable at this
  tab count; lazy-loading remains a deferred Trigger-5/7 concern, explicitly out of scope here.

## Migration Plan

Additive for data/site. Deploy via the normal workflow. Rollback = revert the two workflow
steps + two copy lines (CI), and/or remove the new tab block and two scripts (site). The
`fred_utils` adoption is independently revertible since it preserves behavior.
