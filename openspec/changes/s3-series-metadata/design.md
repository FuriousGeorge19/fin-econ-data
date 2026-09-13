## Context

This is the first of the two design sessions in the multi-session plan (S3; the other
is S5, chart components). Its output is a contract, not a feature: how every dataset
describes itself, how "overdue" is decided and shown, what "today" and "as of" mean on
a static site, and what happens when a fetch fails. S4 builds it; S5 (components and
page manifests), S8 (source catalogue) and S11d (yields table with a per-row as-of
stamp) all read the header this change defines, so the cost of getting it wrong grows
with every chart built afterwards.

The system today: five fetchers write five JSON files whose only freshness signal is
`last_updated`, the pipeline run time, and that is the one header field the page reads.
No file records its last observation; `usrec.json` collapses USREC to intervals and
throws the last month away. `scripts/staleness.py` has one integer per series (5, 5, 5,
45, 10 business days) that fuses cadence, publication lag and slack, no holiday
calendar, and a naive `date.today()`; `tests/test_staleness.py` runs in CI before the
deploy and fails the job. The workflow is a chain: a failed fetch stops everything and
the whole site stays on yesterday's deploy. `sp500_pe.json`'s header disagrees with its
data because `get_ttm_for_month()` marks every month covered by the newest earnings
quarter as estimated, including the three months that quarter legitimately confirms.
The page has no About tab, no annotation inside any Plotly figure, autoranges every
x-axis to the last observation, and computes "one year ago" three different ways.

Two facts found while surveying, recorded because they shape the design:

- FRED publishes the DGS series for day X at about 16:15 ET on X+1 (the 11 Sep 23:25 ET
  run got data through 10 Sep). Deploys currently land anywhere from 01:12 to 09:54 UTC
  because the cron sits on the congested midnight slot; 12 of 135 deploys landed after
  04:00 UTC (midnight EDT).
- FRED's `SP500` monthly average includes the month in progress and moves daily: the
  Aug 2026 P/E point first appeared on 26 Aug at 7713.72 and was revised on every deploy
  until 1 Sep. Shiller's prices are full-month averages.
- The S&P Global EPS workbook the P/E depends on says its public files were discontinued
  on 31 Jan 2026 (`ESTIMATES&PEs!A1`, `A4`). The manual earnings input has no successor.
  The workbook also carries as-of cells (`SECTOR EPS!B2/B3/B4`) that the builder ignores.

Decided by the user on 2026-09-13: descriptor file per dataset at `series/<id>.json`;
seed from gh-pages and deploy what succeeded, with no commit-back to `main`; badge
lateness in calendar days.

## Goals / Non-Goals

**Goals:**
- One place per dataset that says what it is, where it comes from, how often it
  updates, how long the source takes to publish, whether it is revised, and how it was
  computed; embedded into the data file so the page needs nothing else.
- A freshness rule that is right for daily, monthly and quarterly series, never shows a
  badge on a healthy day, and shows one the morning after a single missed run.
- Every chart image carries its source and data-through date; every chart has an About
  tab; time-series x-axes run to today; comparisons say which dates they compare.
- A fetch failure leaves that one series on yesterday's live data with a badge, and the
  other series fresh, while still notifying.
- The P/E's confirmed/estimated flag means what it says.

**Non-Goals (explicitly out of scope):**
- Chart components, page manifests, the section nav, light/dark tokens (S5, S5b, S6).
- The source catalogue (`catalog/sources/<slug>.json`, S8); only a `slug` seam is
  reserved here.
- Committing fetched data back to `main` (decided against; see decision 9).
- A replacement for the discontinued S&P earnings file (an S9 research item).
- Vintage/ALFRED data (see decision 8).
- Restyling the page; S4's About tab and badge are the minimum that satisfies the specs.

If any of these turns out to be required to land S4 cleanly, stop and flag it rather
than expanding scope.

## Decisions

### 1. One descriptor file per dataset, embedded into the header at fetch time

`series/<id>.json` for `dgs10`, `sp500_pe`, `yield_curve`, `spreads`, `usrec` (id = the
data file stem). Hand-maintained JSON: no new dependency, no markdown renderer, and the
repo is JSON everywhere else. The fetcher loads its descriptor, writes it verbatim under
`meta`, and adds a runtime `as_of` block. `staleness.py`, the tests, `dev.sh` and the
workflow's copy and seed steps all derive their file lists from `series/*.json`, so
cadence, lag and *the list of site data files* are each defined exactly once (today the
file list is hand-copied in the workflow and `dev.sh`, and the lag table is a third copy).

- *Alternative considered — keep static facts in each fetcher's dict literal (status
  quo, extended):* fewer files, but methodology prose lives in Python strings, tests
  cannot validate metadata without running a fetcher, and S5's file-additive rule ("one
  manifest file per series, shared files generated") would have to invent the per-series
  file anyway. The descriptor *is* that file; S5 adds a `presentation` block to it.
- *Alternative considered — one shared `catalog.json` listing every series:* a file every
  workflow agent would edit. Rejected by the file-additive constraint.
- *Seam for S8:* each `sources[]` entry carries a `slug` (`fred`, `shiller`, `spglobal`,
  `nber`). S8's `catalog/sources/<slug>.json` can hoist the shared fields; until then they
  are inline.

### 2. Descriptor schema

```json
{
  "id": "sp500_pe",
  "title": "S&P 500 Trailing P/E Ratio (as-reported)",
  "short_title": "S&P 500 P/E",
  "kind": "timeseries",
  "units": "Ratio",
  "cadence": "monthly",
  "publication_lag_business_days": 1,
  "revisions": "occasional",
  "revision_note": "Shiller restates earnings. The site always shows the latest revision; every daily deploy is kept in the gh-pages history.",
  "source_line": "Shiller/Yale · S&P Global · FRED SP500",
  "sources": [
    {"slug": "fred", "name": "Federal Reserve Bank of St. Louis (FRED)",
     "url": "https://fred.stlouisfed.org/series/SP500", "licence": "S&P Dow Jones Indices terms via FRED"},
    {"slug": "shiller", "name": "Robert Shiller / Yale",
     "url": "http://www.econ.yale.edu/~shiller/data.htm", "licence": "Free download; no republication restriction found"},
    {"slug": "spglobal", "name": "S&P Global, sp-500-eps-est.xlsx (manual)",
     "url": "https://www.spglobal.com/spdji/", "licence": "Unverified; only the derived TTM EPS is published"}
  ],
  "inputs": [
    {"id": "price", "label": "Monthly average S&P 500 price", "source": "fred",
     "series_id": "SP500", "cadence": "monthly", "publication_lag_business_days": 1},
    {"id": "earnings", "label": "Trailing 12-month as-reported EPS", "source": "spglobal",
     "cadence": "quarterly", "publication_lag_business_days": 60, "manual": true,
     "status": "discontinued",
     "status_note": "S&P's public EPS file was discontinued on 31 Jan 2026; earnings are estimated from the last confirmed quarter until a replacement source is found."}
  ],
  "methodology": ["…"],
  "notes": ["…"],
  "presentation": {}
}
```

- `kind`: `timeseries` (x-axis-to-today applies) | `curve` (snapshot, exempt) |
  `intervals` (usrec). It drives chart chrome, not fetching.
- `cadence`: `daily` (business days) | `monthly` | `quarterly`. Extend the enum when a
  series needs weekly or annual; `period_end` is defined only for these three.
- `publication_lag_business_days`: after the period ends, how many business days until
  the source publishes. Seeded values and their basis: DGS series **1** (H.15 publishes
  day X at X+1 ~16:15 ET, confirmed against the deploy log); FRED `SP500` monthly average
  **1** (final once the month's last daily value is in); USREC **5** (month M lands the
  first business day of M+1); S&P quarterly EPS **60** (an estimate; the figure firms up
  over roughly three months). All in the descriptor, so a wrong guess is a one-field edit.
- Multi-input datasets list `inputs[]` each with cadence and lag; `inputs[].required`
  defaults true; `inputs[].status` is `active` (default) or `discontinued` with a
  `status_note`. Dataset-level `cadence`/lag describe the primary input.
- `revisions`: `none` | `occasional` | `regular` | `retroactive` (USREC: NBER dates peaks
  4–21 months later and flips past months to 1) plus a `revision_note`.
- `methodology` and `notes` are arrays of plain-text paragraphs, rendered as `<p>`.
- `presentation` is reserved for S5 and is **not embedded** into the data JSON, so
  presentation edits never require regenerating data.

### 3. Header contract: `meta` + `as_of` + payload; `last_updated` retired

```json
{
  "meta": { "…descriptor minus presentation…": true },
  "as_of": {
    "fetched_at": "2026-09-12T03:25:14Z",
    "first_observation": "1871-01-01",
    "last_observation": "2026-08-01",
    "period_label": "Aug 2026",
    "observation_count": 1868,
    "due_by": "2026-10-01",
    "inputs": {
      "price":    {"last_observation": "2026-08-01", "period_label": "Aug 2026", "due_by": "2026-10-01"},
      "earnings": {"last_observation": "2025-09-30", "period_label": "Q3 2025", "due_by": "2026-03-30",
                   "confirmed_through": "2025-12-01", "value": 234.06}
    }
  },
  "observations": []
}
```

- Payload keys and shapes are unchanged: `observations` (list or date-keyed dict),
  `series` (spreads), `recessions` (usrec), and `tenors`/`tenor_months` **stay
  top-level**. They are payload shape, not metadata: `index.html` reads `ycData.tenors`
  at lines 686, 761 and 793 and would throw if they moved. Every existing test and
  render path keeps working.
- `title`, `units`, `frequency`, `source`, `methodology`, `description` and `series_id`
  move under `meta`; `last_ttm_earnings` becomes `as_of.inputs.earnings.value`.
- `as_of.series.<key>` (first and last observation, count, `period_label`, `due_by`) is
  present when the payload holds more than one series: spreads (legs start 1976-06-01
  and 1981-09-01) and yield_curve (per tenor). This is what S11d's per-row stamps read.
- `as_of.latest_value` is optional; usrec uses it for the last USREC month's 0/1.
- `period_label` is computed in Python (`10 Sep 2026`, `Aug 2026`, `Q3 2025`) so JS, CSV
  filenames and the About tab all agree, and by the same principle as decision 4: the
  browser displays, it does not derive. Dates are `YYYY-MM-DD`; timestamps ISO 8601 UTC.
- `last_updated` (old format) is kept as an alias of `fetched_at` for one release so S4a
  can deploy before S4b; S4b removes the reads, then the alias.
- Writes are atomic (`<path>.tmp` then `os.replace`) in the shared `write_json`. Today
  every fetcher does `open(path, "w")` + `json.dump`; all their exit paths precede the
  write, so a failure leaves the old file, but an I/O error mid-dump would truncate it.
  Atomic writes also make `data-pipeline`'s "no partial half-written output" scenario
  literally true.

### 4. The overdue rule, generalised from the 2026-08-29 decision

Already decided: x-axis to today; overdue = business days past cadence + publication
lag; a daily series on a Saturday is not overdue. The generalisation that also works for
monthly and quarterly inputs:

```
period_end(last_observation)   daily: that day; monthly: last day of that month;
                               quarterly: last day of that calendar quarter
next_period_end = period_end advanced one cadence step (daily: next business day)
due_by          = next_period_end + publication_lag business days
overdue on viewing date V  <=>  V > due_by
```

For a daily input with lag 1 this reduces exactly to the decided rule. Hand-computed
fixtures (holidays applied), which S4's calendar tests use:

| Input | last_observation | next_period_end | due_by | Note |
|---|---|---|---|---|
| DGS10 | Thu 2026-09-10 | Fri 09-11 | Mon 09-14 | Healthy: Friday's value lands Monday evening; badge only if Monday's run fails, from Tuesday |
| DGS10 | Thu 2026-09-03 | Fri 09-04 | Tue 09-08 | Labor Day Mon 09-07 skipped; matches the deploy log |
| DGS10 | Wed 2026-11-25 | Fri 11-27 | Mon 11-30 | Thanksgiving skipped; the Friday after is a business day |
| SP500 monthly | 2026-08-01 | Wed 09-30 | Thu 10-01 | lag 1 |
| USREC | 2026-08-01 | Wed 09-30 | Wed 10-07 | lag 5 |
| Earnings | 2025-09-30 | Wed 12-31 | Mon 2026-03-30 | 60 business days, skipping 1 Jan, 19 Jan, 16 Feb. On 2026-09-13: 167 days late |

- **Business day** = Mon–Fri excluding US bond-market holidays: the federal holidays plus
  Good Friday, computed by rule in `staleness.py` with no dependency, plus an
  `extra_closures` list for one-off closures (e.g. 2025-01-09). Good Friday is a trading
  day in some years (DGS10 has values on 2021-04-02, 2023-04-07 and 2026-04-03); treating
  it as closed is the safe direction: one extra day of slack that week, never a false
  badge.
- **Python computes `due_by` at fetch time; the browser only compares dates.** The date
  depends only on the last observation and the descriptor, both known at fetch time, so
  it stays right if the pipeline stops running, which is the case it most needs to
  catch. No holiday list or business-day arithmetic in JS.
- **"Today" is the US Eastern calendar date**, in JS via
  `toLocaleDateString('en-CA', {timeZone: 'America/New_York'})`, for the badge and the
  x-axis end. The data's publication clock is ET; a Sydney viewer at 10:00 Tuesday is
  looking at Monday-evening US data and must not see a badge. Judged on the viewer's
  local date, everyone east of UTC would see a spurious badge for hours every business
  day, and US viewers on any morning the deploy slipped past midnight ET.
- **Dataset `due_by` is the minimum over required, active inputs.** A `discontinued`
  input is excluded and is rendered as a statement, not an alarm: the P/E says
  "earnings estimated since Jan 2026 (source discontinued)" in its source line and About
  tab instead of an "overdue" badge that can never clear.
- **Lateness in the badge is in calendar days** because the browser has no holiday
  calendar; "3 business days late" would be false precision there. The threshold is the
  business-day rule.
- *Alternative considered — one tolerance integer per series (status quo):* cannot
  express cadence, cannot say when the next update is due, and needs slack for holidays.
- *Alternative considered — compute overdue in the workflow and ship a freshness JSON:*
  stale the moment the workflow stops running.
- *Alternative considered — add one business day of slack:* would hide a single missed
  run. Rejected because decision 11 removes the timing artefact it would paper over.

### 5. Freshness display

- Every chart always shows its as-of inside the figure: a bottom-left annotation
  `{source_line} · data through {period_label}`, e.g. `FRED DGS10 · data through
  10 Sep 2026`. The P/E names both inputs: `… · price through Aug 2026 · earnings
  confirmed through Q3 2025, estimated since Jan 2026 (source discontinued)`. This is
  the 2026-09-12 decision; S3 fixes the text, S4 draws it.
- The overdue badge is HTML chrome beside the chart title, shown only when overdue:
  `Overdue · expected by 14 Sep 2026 · 3 days late`; for a multi-input dataset it names
  the input: `Earnings overdue · Q4 2025 expected by 30 Mar 2026 · 167 days late`.
  Fresh charts show no badge; the in-chart line already carries the date.
- Grid pages (S12) get this per tile; a page-level "oldest data on this page" line is
  S12's call, and `as_of` already carries what it needs.

### 6. x-axis end rule and comparison as-of

- `kind: timeseries` charts set the x-axis range end to today (ET date). The gap after
  the last observation is deliberate and visible. Range buttons count back from today.
  An open-ended recession band extends to today (today it stops at the last plotted
  date, `index.html:833-849`).
- `kind: curve` snapshots are exempt (categorical tenor axis).
- Comparisons ("1-year change", overlays) anchor on the **last observation**, snap to the
  nearest observation **on or before** the target, and **display the resolved date**
  (`vs 10 Sep 2025`). One shared helper, using UTC-only string/`Date.UTC` arithmetic:
  the current yield-curve and spreads code parse local midnight and serialise with
  `toISOString()`, which shifts the target a day east of UTC. It replaces the DGS10 stat
  tile's positional `slice(-252)` and the spreads table's private copy. Stat tiles show
  the date beside "Latest".

### 7. About tab contents

A sub-tab strip per chart (`Chart | Table | About`; What I Want asks for "tabs on the
charts and tables"), rendered entirely from `meta`/`as_of`: title and description;
sources (name, link, licence or republication note); inputs table (label, source series
ID, cadence, publication lag, last observation, status including discontinued); next
update expected by, with "judged on the US Eastern date"; last fetched (UTC); the
revision sentence; coverage (first observation, count); methodology paragraphs; notes
(the 30-year 2002–2006 gap, the NBER announcement lag, the estimated-earnings rule).
Placement and styling are S4's minimum; S5 may restyle.

### 8. Revisions: always the latest revision, stated in the About tab

`revisions` and `revision_note` in the descriptor; no ALFRED or vintage integration.
gh-pages keeps one commit per deploy (137 since 5 Mar 2026), so any daily vintage is
`git show <sha>:data/<id>.json`; the revision sentence says so. Closes Areas of
Uncertainty #1.

### 9. Failure policy: deploy what succeeded, seed from the live copy, staleness reports

The workflow (spec `daily-automation`):

1. After checkout, `git fetch --depth=1 origin gh-pages`, then restore **each site data
   file by name** (list derived from `series/*.json`) from `FETCH_HEAD`. Never the
   directory: `git restore --source` runs in no-overlay mode by default and would delete
   `data/earnings_overrides.json`, which is not on gh-pages, after which the P/E fetcher
   warns and silently produces Shiller-only output ending in 2023. A series with no live
   file yet keeps `main`'s copy. A seed failure warns and continues.
2. Each fetch step has an `id` and `continue-on-error: true`. A failure leaves the seeded
   file (every exit path precedes the write; decision 3 makes writes atomic anyway).
3. `pytest` still gates the deploy for integrity and cross-check failures (a *wrong*
   number), with the `staleness`-marked test deselected. The staleness check runs as its
   own `continue-on-error` step and writes a per-series table to
   `$GITHUB_STEP_SUMMARY`.
4. The deploy always runs; redeploying unchanged data is harmless.
5. A final `if: always()` step after the deploy emits a `::warning::` per failed fetch
   and per overdue series and **exits 1 if any fetch step failed**, so the job goes red
   and GitHub notifies, after the data has already shipped. Without it,
   `continue-on-error` would remove the pipeline's only failure signal.

This closes Areas of Uncertainty #4 and the commit-back question that S0, S1 and S2
each worked around: **no commit-back**. gh-pages is the data history; `main`'s `data/`
files are test fixtures. `dev.sh --live` downloads the site data files from
joemirza.com for local work that needs current data.

- *Alternative considered — commit fetched data back to `main` daily:* the strongest case
  is that `git pull` gives fresh local data, there is one source of truth, and the
  `STALENESS_SOURCE` and `dev.sh` warning workarounds go away. Costs: about 250 bot
  commits a year on `main`, a rebase/push step in the workflow, and a commit every day
  because `fetched_at` moves even when no data changed. gh-pages already holds the
  history, so the unique benefit is local freshness, which `dev.sh --live` covers.
  Revisit if S7/S11 workflow agents turn out to need fresh fixtures on `main`.
- *Alternative considered — keep all-or-nothing:* simplest, but with per-series
  thresholds one FRED hiccup freezes all five series with no badge.

### 10. P/E semantics: confirmed vs estimated, and no partial months

- Month M is **confirmed** iff the earnings file contains the calendar quarter ending
  strictly before M begins (the existing `effective_from = quarter_end + 1 month`
  convention, so the Q3 entry applies to Oct, Nov and Dec); otherwise M reuses the last
  confirmed TTM EPS and is **estimated** (`is_estimated = month >= effective_from(last)
  + 3 months`). With the file ending at Q3 2025: Oct–Dec 2025 confirmed on 234.06,
  Jan 2026 onward estimated, `confirmed_through = 2025-12-01`, and the dashed segment
  starts at Jan 2026. The S1 header bug disappears by definition:
  `as_of.inputs.earnings.value` is the last entry's TTM.
- The S1 `xfail` test is replaced by structural invariants: `as_of.inputs.earnings.value
  == overrides[-1].ttm_eps`; the last `estimated=false` month equals `confirmed_through`
  equals `effective_from(last) + 2 months`; every later observation is estimated and
  every earlier override-era one is not. (The old header-vs-last-observation check would
  pass tautologically under forward-fill.)
- **Drop the unfinished month**: `fetch_fred_prices` includes month M only when the fetch
  date (ET) is later than M's last day. Shiller's prices are full-month averages; a
  partial FRED month would mean something different and move daily.
  - *Alternative considered — keep the partial point flagged `partial: true`:* more
    current, but a monthly series with a moving last point contradicts its own cadence
    and label. A daily S&P level chart (roadmap items 15–17) is the right home for
    "current".
- `build_earnings_overrides.py` reads the workbook's `SECTOR EPS!B2/B3/B4` into the
  overrides header (`data_as_of`, `actuals_through`), caps entries at `actuals_through`
  so a preliminary figure can never enter as confirmed, and derives the calendar quarter
  from `effective_from` (the sheet's `quarter_end` values are last trading days such as
  2024-06-28).

### 11. Cron moves off midnight UTC

`15 23 * * 1-5` (19:15 EDT / 18:15 EST, Mon–Fri): after FRED's ~16:15 ET H.15 update,
hours before ET midnight, off the congested top-of-hour slot. Same data as today (day
X's value published on X+1), so the lag model is unchanged; what changes is that a
deploy can no longer slip past ET midnight and trip the badge on a healthy day. Modifies
`daily-automation` "Scheduled weekday data refresh".

### 12. Spec decomposition and ownership

- **NEW `series-metadata`** — the descriptor file, the `meta` + `as_of` header contract,
  period labels, atomic writes, the transitional alias, the metadata tests.
- **NEW `data-freshness`** — the calendar, the `due_by` rule with fixtures, the roll-up
  over inputs, the US-Eastern "today", the badge, discontinued inputs, the staleness
  check reading `as_of`.
- **NEW `chart-chrome`** — the frame around every chart: in-chart source line, About tab,
  x-axis end rule, comparison as-of, export buttons.
- **MODIFIED `daily-automation`** — cron; seed, non-fatal fetches, staleness summary,
  deploy-always, failure surfaced after deploy.
- **MODIFIED `data-pipeline`** — "JSON output schema conventions" defers to
  `series-metadata`.
- **MODIFIED `sp500-pe-series`** — four requirements: stitched sources and header fields;
  the confirmed/estimated rule; overrides as-of and discontinuation; "through the last
  completed month".
- **MODIFIED `nber-recession-data`**, **`treasury-10y-series`**,
  **`treasury-spreads-series`**, **`yield-curve-series`** — each requirement that named
  a top-level header field, "the latest charted date", or an unlabelled comparison
  period, rewritten to reference the new contract.
- **`dashboard-site` unchanged** — it is agnostic to which series exist and to what a
  chart draws around itself; the chrome belongs to `chart-chrome`.

Ownership: `series-metadata` owns the descriptor and header; `data-freshness` owns the
rule and the badge; `daily-automation` owns CI mechanics; `chart-chrome` owns everything
drawn around a chart. The other specs reference rather than restate. Every MODIFIED
block copies the whole requirement with an exactly matching header, because the
validator checks only shape and a partial block is silently truncated at archive.

## Risks / Trade-offs

- **The header change breaks the page if S4a deploys before S4b.** → The `last_updated`
  alias (decision 3) keeps the old page rendering on new data for one release;
  `tenors`/`tenor_months` stay top-level. S4b removes the alias reads before the alias is
  dropped.
- **Seeded publication lags are guesses for the slow inputs.** → They are descriptor
  fields, one edit each; the DGS lag is confirmed against the deploy log, the others are
  generous. A wrong guess shows as a badge, not a wrong number.
- **The calendar is hand-rolled.** → Federal holidays are rule-based and stable; Good
  Friday is treated as closed in every year (safe direction); `extra_closures` handles
  the rest. The calendar tests carry the fixtures in decision 4.
- **`continue-on-error` hides failures.** → Decision 9 step 5 fails the job after the
  deploy so GitHub still notifies. Staleness alone does not fail the job; the badge is
  its signal.
- **Seeding from gh-pages depends on the deploy branch layout.** → The seed restores
  named files only, derived from `series/*.json`; a missing file warns and falls back to
  `main`'s copy. Never the directory (`earnings_overrides.json` is not on gh-pages).
- **The P/E earnings input is discontinued and stays estimated indefinitely.** →
  `status: discontinued` turns it into a statement rather than a permanent alarm; the
  chart, source line and About tab say so. Finding a replacement is an S9 research item.
- **Dropping the partial month makes the P/E up to five weeks behind the market.** →
  That is what a monthly series means; the About tab says "through the last completed
  month". A daily S&P level chart is a separate roadmap item.
- **A viewer east of UTC sees "today" as an earlier date than their own.** → Intended:
  the freshness clock is the data's, and the About tab says so.
- **`meta` equality tests would couple every descriptor edit to fixture regeneration.**
  → The metadata test compares only pipeline-owned keys and recomputes `due_by`;
  prose and source edits never fail it.

## Migration Plan

S4a (Python, tests, workflow) ships first: descriptors, `series_meta`, the calendar and
rule, the five fetchers, the P/E fix, the workflow edits, regenerated `data/*.json`
fixtures, with the `last_updated` alias in place. The existing page keeps working on the
new files. S4b (JS) then reads `meta`/`as_of`, adds the chrome, and removes the alias
reads; the alias is dropped from the fetchers in the same or the following change.
Rollback: the workflow edits are one file; each fetcher's header change is independent;
the alias means either half of S4 reverts alone.
