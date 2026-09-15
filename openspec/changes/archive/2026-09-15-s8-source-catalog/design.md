## Context

Phase 2 of the multi-session plan. The `s5-chart-components` rebuild (S5→S7c) is
complete and archived; the site is a generated multi-page build with four charts on the
chart-component pattern. This change adds a separate subsystem — the source inventory —
that nothing in `series/`, `site/js/` or `scripts/build_site.py` depends on today, but
that the next roadmap charts (S11) and every future research workflow will reference.

What exists: `series/<id>.json` carries an inline `sources[]` list (`{slug, name, url,
licence}`) that `series_meta.meta_from_descriptor()` copies verbatim into the data
file's `meta`, and `site/js/lib/asof.js`'s `renderAboutHTML()` renders as the About
tab's Sources list. `inputs[].source` names a slug that `tests/test_series_metadata.py::
test_input_sources_exist` requires to be present in that descriptor's own `sources[]`.
The slugs in use are `fred`, `shiller`, `spglobal`, `nber`. The synthesis document's §4
(Obsidian) holds a hand-written catalogue of ~17 machine-readable sources, ~10
chartbooks, a FRED series reference and derived-series definitions — none of it
reachable from the repo.

Who consumes this change, and the constraint each imposes:

- **S9** (workflow, ~12 Sonnet agents + a verifier): one agent per remaining source,
  writing one file from an exemplar and a README; may answer "unknown", may not guess;
  every claim carries the URL it was read from; reads official pages only; runs a
  done-check on its own file; never edits a shared file. The verifier schema-validates
  every file and spot-checks three claims per entry against the cited URL.
- **S10** (dry run): "recommend charts for US Equity Valuations from the catalogue
  only" — the catalogue must answer "which datasets bear on equity valuation" without a
  human re-reading free text.
- **S11b** (workflow): the chart-8 agent must record ICE BofA's republication terms in
  the catalogue before rendering — as a new file, since it may not edit `fred.json`.

Decided by the user before this design (2026-09-14): design and build in this session;
a provider-owned dataset hosted on FRED lives under its rights holder with `via: fred`;
each source carries a structured `datasets[]` list now. The draft was then walked
through by two critics — one as the S9 agent, the S11b chart-8 agent and the S9
verifier; one as the S10 dry run plus a simplicity pass — and their findings are folded
into the decisions below (each notes what it fixed).

## Goals / Non-Goals

**Goals:**
- One place in the repo that says, per source: what it is, how to reach it, under what
  terms, what datasets it offers (cadence, coverage, lag, status, topics), when that was
  last checked and from which page.
- A file-additive shape: a workflow agent adds one file and runs one check; the
  catalogue never needs a shared-file edit to grow.
- Descriptors reference the catalogue instead of repeating it, and the About tab shows
  what the catalogue knows (licence sentence, hosting, terms status).
- A research log that carries productive searches — including ones that found
  nothing — forward, in a form a session can grep by topic.
- Honest seeds: four entries whose `access` and `terms` were read from official pages in
  this session, and whose copied-from-notes facts say so.

**Non-Goals (explicitly out of scope):**
- Filling any source beyond the four seeds (S9), or replacing the discontinued S&P
  earnings workbook (an S9 research item).
- Publishing the catalogue on the site (no `/sources/` page, no copy into `site/data/`).
- Regenerating the committed `data/*.json` fixtures.
- Any change to the workflow, chart types, `source_line`, or the open theme-toggle /
  HTTPS items. (`scripts/build_site.py` was a non-goal in the draft; decision 11 records
  the one exception the user asked for.)

If any of these turns out to be required to land this change cleanly, stop and flag it
rather than expanding scope.

## Decisions

### 1. One file per rights holder; hosted data says `via`; the boundary rule is written down

`catalog/sources/<slug>.json`, slug = filename. A source is one set of terms and one
way in. The boundary rule, stated so twelve agents draw it the same way:

> A dataset gets its own file only when its terms differ from the host's (S&P DJI's
> `SP500` and Case-Shiller on FRED; ICE BofA's `BAML*` on FRED) or the publisher serves
> it directly in a form we would use (Treasury.gov's daily curve CSVs). Public-domain
> data reached only through FRED is a FRED dataset — name the originating agency (Board
> of Governors H.15, BLS, Cleveland Fed) in `gives`.

`via` names the hosting source's slug. It may sit in the source-level `access` (a
provider whose whole presence is through FRED) or on a dataset; a dataset's `access` and
`terms` are merged over the source's key by key, through one function
(`catalog.merge_block`) that both the validator and the resolver call, so "what applies
to this dataset" has one answer.

`fred.json`'s description states that it lists only the families evaluated so far and
that any FRED series is reachable through the same `access` block — add a dataset and a
research-log entry when one is evaluated. S10 may therefore propose an unlisted FRED
series (`GDP` for the Buffett indicator) as long as it records it.

Consequences: `sp500_pe`'s price input moves from `source: fred` to `source: spglobal`
(dataset `sp500-index`, `via: fred`); its About tab reads "S&P Global … via FRED".
S11b's chart-8 agent adds `catalog/sources/ice-bofa.json` and
`series/credit_spreads.json`, editing nothing shared. NBER's chronology is a `web-page`
dataset with no `via` — USREC is FRED's own construction from NBER's dates, not hosted
NBER data — with a note pointing at `fred/usrec` as the machine-readable form.

- *Alternative considered — everything under the host with a per-dataset `terms`
  override:* the simpler "source = where the bytes come from" model and fewer files, but
  `fred.json` becomes a shared file that every provider-terms task edits (ICE BofA in
  S11b, Case-Shiller in the real-estate phase), breaking the never-edit-a-shared-file
  rule unless a verifier merges. Rejected on the workflow constraint.
- *Fixed by the critique:* the rule was unstated, and the draft's seeds broke it
  (USREC catalogued twice, once as `nber/chronology via fred`).

### 2. `datasets[]` inside each source file, each tagged with `topics`; `role` separates feeds from references

A dataset is one thing you can fetch — a series family, a workbook, a CSV endpoint —
with its own native `cadence`, `coverage`, `publication_lag_business_days`, `status`,
`ids`, `units`, optional `access`/`terms` overrides, and `topics`. This is the unit S10
recommends from and S11 fetchers cite.

`topics` is ≥1 value from a controlled vocabulary owned by `scripts/catalog.py`
(`rates`, `credit`, `inflation`, `equity-valuation`, `equity-returns`, `macro`,
`recession-dating`, `real-estate`, `global`, `expectations`), validated. Tracing S10
without it: CAPE surfaces only if Shiller's `gives` happens to say "CAPE"; the dividend
yield only if it says "dividends" rather than "D"; the Buffett indicator needs Z.1's
equity market value plus FRED `GDP`, which no free-text search joins. With it, `report
--topic equity-valuation` is the query. The vocabulary grows by editing one constant.

A top-level `role: data | reference` separates fetchable sources from the chartbooks in
synthesis §4b (JPMorgan Guide, Yardeni, Crestmont…) that S9 will also catalogue as
design references. `reference` ⇒ `datasets` is empty; the validator enforces it.

`units` is optional free text per dataset (`percent`, `index`, `ratio`, …) — the
log-axis convention ("price levels held over long spans") needs it and an S9 agent can
read it off any series page.

- *Alternative considered — a second directory, `catalog/datasets/<id>.json`:* perfectly
  file-additive, but two directories and a join for every read, for ~15–60 entries.
- *Fixed by the critique:* `topics`, `role`, `units` added; a `research[]` back-pointer
  list on sources cut (the log already says where each finding landed, and agents can't
  append to the log anyway).

### 3. Facts are researched-or-not, explicitly; the validator checks shape, the verifier checks evidence

Any scalar fact may be the literal string `"unknown"` — "looked, could not establish
it." An absent field is "nobody looked." Every fact-bearing block (`access`, `terms`,
each dataset) may carry `read_from`: the URL, or list of URLs, the facts were read from.

`catalog.py check` does **not** require `read_from`. A seed block whose facts come from
somewhere that is not a web page — S&P Global's access and terms (both pages returned
403 to automated fetches), the EPS workbook's discontinuation notice (read from the
workbook itself) — would fail its own validator if it did, while not requiring it means
the validator cannot enforce S9's URL-on-every-claim rule. So the split is: `check`
validates shape; `report` prints per file how many fact blocks lack `read_from`; S9's
*verifier* rejects an agent-filled file with any missing. A claim with no `read_from` is
not treated as verified by anyone. (The draft expected FRED's dataset families to be
copied from planning notes; in the build they were verified through the FRED API's
`/fred/series` endpoint instead, so every `fred` block carries `read_from`.)

`verified: {on, by}` at the top level covers `access` and `terms`. A dataset may carry
its own `verified_on`, so a later session adding a dataset (S11b) does not falsify the
file's stamp.

`terms.status` has operational definitions the validator enforces, because it is the
highest-stakes field — chart 8 is gated on it and the About tab prints it:

| status | meaning | evidence `check` requires |
|---|---|---|
| `verified` | the terms page was read and permits what the site does | `terms.url` set; `terms.quote` a non-empty verbatim sentence from it |
| `restricted` | the terms page was read and limits republication or redistribution | same evidence; `summary` states the limit |
| `unverified` | a terms page was found but not read or quoted | `terms.url` set |
| `unknown` | the official site was searched and no terms statement found | `terms.url` may be `"unknown"` |

Seeds follow the same rule. S&P Global is expected to land `unverified` or
`restricted`, not `verified` — that is a finding.

- *Fixed by the critique:* the draft said "a claim with no `read_from` is not a claim"
  and would have failed its own seeds; the status values had no definitions.

### 4. Descriptors reference the catalogue; the fetcher resolves at fetch time

`series/<id>.json` `sources[]` becomes `[{slug, dataset?, url?, note?}]`. `name` and
`licence` are removed from descriptors and the schema test rejects them, so the
duplication cannot creep back. `inputs[]` gains optional `dataset`.

Descriptor input `cadence` is the cadence *as used* — the P/E price input is FRED
`SP500` requested at `frequency=m`, `aggregation_method=avg` — while a dataset's
`cadence` is its *native* one (`SP500` is daily). There is no equality check between
them; the validator checks only that the reference resolves. Chart 4's monthly GS10
stitched from daily data and item 11's monthly HQM table would hit the same wall.

`series_meta.meta_from_descriptor()` resolves each reference (importing `catalog` lazily
inside the function, as `build_as_of` already does for `staleness`, to avoid the
`catalog` → `series_meta` → `catalog` cycle) into the entry the About tab reads:

```json
{"slug": "spglobal", "dataset": "sp500-index",
 "name": "S&P Global (S&P Dow Jones Indices)", "dataset_name": "S&P 500 index level (via FRED)",
 "url": "https://fred.stlouisfed.org/series/SP500",
 "licence": "…the merged terms.summary…", "terms_status": "unverified",
 "via": "FRED", "note": null}
```

`url` defaults to the source's `homepage`; `licence` is the merged `terms.summary`;
`via` is the hosting source's `short_name`; `dataset_name` is what disambiguates two
`spglobal` entries on the P/E About tab. A bad reference raises, naming the descriptor
and slug, so that series' fetch fails (recorded by `fetch_all.py`) and
`tests/test_catalog.py` fails the gating step before deploy. The browser never fetches
the catalogue; data files written before this change (inline shape) still render.
`source_line` stays hand-written even though `short_name` now exists.

- *Alternative considered — the browser fetching `/data/catalog/<slug>.json`:* a second
  fetch per card and the join logic in JS; the repo's conviction is that the data file is
  the contract between fetchers and the site.
- *Fixed by the critique:* the draft's cadence-equality test would have failed on the
  P/E seed itself.

### 5. The About tab shows what the catalogue adds, minimally

`renderAboutHTML()` appends " via FRED" when a resolved entry carries `via`, and
"· terms unverified" (or `unknown`/`restricted`) when `terms_status` is present and not
`verified`. Two template lines in `site/js/lib/asof.js`; nothing else under `site/js`
changes, and the colour-literal and forbidden-key scans still apply. Old data files lack
both fields and render as before. Catalogue text is plain text — the renderer
interpolates raw (pre-existing), so the README says no HTML.

### 6. Validation is a stdlib script the tests import, and it is the schema's authority

`scripts/catalog.py`: `slugs()`, `load(slug)`, `load_all()`, `merge_block()`,
`validate(entry, *, slug, known_slugs)` → list of problems, `resolve_source_ref(ref)`,
and `used_by()` (derived from `series/*.json`, never stored). CLI:

- `check [path …]` — with paths: schema plus `via` slugs present on disk, for those files
  only. This is what an S9 agent runs in a shared checkout without tripping on a
  neighbour's half-written file (S7's lesson: don't run shared-tree checks from inside a
  fan-out). Bare: every file plus cross-references against every `series/*.json`. Exit 1
  with one line per problem naming the file.
- `report [--topic T]` — slug × role × datasets × used-by series × terms status ×
  verified-on × fact blocks lacking `read_from`, then the `via` reverse index ("fred
  hosts: spglobal/sp500-index …"). With `--topic`, only datasets carrying that topic.

The README's field table is a rendering of what `check` enforces and says so; the spec
stays at requirement level (field names and rules, not enum lists), so archive-time
drift is one place. Same pattern as `series_meta.py` and `build_site.py`; no JSON-Schema
dependency.

Consistency rules the validator carries: unknown top-level or dataset keys fail
(as the `presentation` test does); slug matches filename and the slug grammar; dataset
ids unique within a file; `via` names an existing slug and is never the file's own;
`status: discontinued` ⇒ `coverage.end` is a date, not `"ongoing"`;
`publication_lag_business_days` is an integer ≥ 0 or `"unknown"` (Treasury.gov publishes
same day); `verified.on` and any `verified_on` parse and are not in the future; `url`
fields start with `http://` or `https://` and may contain `{year}`-style placeholders;
`topics` ⊆ the vocabulary; `role: reference` ⇒ no datasets.

### 7. The research log is markdown with a fixed template, edited only by the session owner

`catalog/research-log.md`, newest first. Each entry: a dated heading, `topics:`, the
question, what was searched or read (URLs), what was found, the outcome (`adopted`,
`rejected`, `gap`, `open`), and where it landed (catalogue slug/dataset, series id,
Session Plan item). Structured enough to grep, loose enough to record a search that
found nothing — which is the point.

Workflow agents never append: every S9/S11 agent's report carries a "Research notes"
block in the template, and the verify/merge step appends them. Without this rule the
log is a shared file every agent edits.

Back-filled in this change from the synthesis document's §4 and the April–September
2026 sessions, each marked "back-filled 2026-09-14, not re-verified." The Case-Shiller
idea becomes an `open` entry under `real-estate`, not a stub dataset with no evidence.

### 8. Seed four, not three; verify what the seeds claim

`fred`, `shiller`, `spglobal`, and `nber` — the hoist requires every referenced slug to
exist and `usrec` already references `nber`. Each seed's `access` and `terms` are read
from the official page in this session and stamped `verified.on: 2026-09-14`; what
cannot be established is `"unknown"`. FRED's dataset families come from synthesis §4c
but their start dates, frequencies, units and notes were read from the FRED API's
`/fred/series` endpoint on 2026-09-14 and cite the series pages in `read_from`. `shiller.json` is the
exemplar S9 agents copy: small, every block filled. `spglobal.json` has two datasets:
`sp-500-eps` (the manual workbook, `discontinued`, `coverage.end` 2026-01-31) and
`sp500-index` (`via: fred`, native daily, trailing ten years). `t10y-spreads`
(T10Y2Y/T10Y3M) is named for what it is, with a note that the repo uses it as a test
oracle, not a chart input.

### 9. Fixtures are not regenerated into the commit

For the browser check, the fetchers run locally (`FRED_API_KEY` and the Excel
dependencies are present), `scripts/dev.sh` builds and serves, the About tabs are
checked, then `git checkout -- data/` restores the fixtures. Nothing requires the new
shape on `main` — `tests/test_series_metadata.py` deliberately does not assert full
equality of `meta` with the descriptor, and the new tests accept both shapes — and
thousands of fixture diff lines would bury the change under review. The live site gets
the resolved shape on its next scheduled fetch. Fallback if a fetcher cannot run: copy
the fixture under `site/data/` with `meta` swapped via `meta_from_descriptor()` — the
exact resolution path, no network.

### 10. Not published to the site

No `/sources/` page, no copy of `catalog/` into `site/data/`. The About tab is the only
public surface. Not now rather than never: a sources page is a small `build_site.py`
change if a use appears.

### 11. The FRED API attribution notice goes in the page shell's footer

Reading the FRED API Terms of Use for the `fred` seed (decision 8) turned up a
requirement the site did not meet: "This product uses the FRED® API but is not endorsed
or certified by the Federal Reserve Bank of St. Louis." The draft logged it as an open
item for the next generator session; the user asked for it now. `render_shell()` in
`scripts/build_site.py` adds a `<footer class="site-footer">` with the sentence to every
page, `site/css/site.css` styles it in the muted text colour under the nav's padding
rules, `tests/test_build_site.py` asserts every generated page carries it, and the
`site-build` spec's shell requirement lists it. Every page rather than only chart pages
because every page loads FRED-sourced data.

## Risks / Trade-offs

- **Some FRED family details are only spot-checked.** Start dates were read for the
  series named in each dataset's `read_from`; sibling series (DFII7/20/30, GS tenors
  other than GS1/GS10, HQMCB2YR…29YR) are noted as unchecked. S9's FRED-adjacent agents
  can close those in passing.
- **Two `spglobal` entries on one About tab.** `dataset_name` disambiguates; the browser
  check confirms it reads well.
- **The topics vocabulary is a guess at ten.** Cheap to extend; the validator names the
  file when an agent uses an unlisted topic, which is the signal to extend it.
- **`"unknown"` as a string in numeric fields** complicates every consumer. Accepted:
  the only consumers are the validator, `report`, and humans; no fetcher reads the
  catalogue's numbers.

## Migration Plan

1. Land `scripts/catalog.py`, `catalog/`, the descriptor edits, `series_meta.py`,
   `asof.js` and the tests in one commit; `pytest -m "not staleness"` green.
2. The next scheduled workflow run fetches with the new `meta_from_descriptor()` and
   deploys data files carrying resolved `meta.sources[]`; the About tab shows the new
   fields. Until then the live files carry the inline shape, which the new `asof.js`
   renders exactly as before. No workflow edit; no manual step.
3. Rollback: revert the commit. Data files written under the new contract render on the
   old `asof.js` (superset of fields).

## Open Questions (handed on, not blocking)

- **S9**: the verifier's rule is "every fact block in an agent-filled file has
  `read_from`, and three claims per entry are spot-checked against it"; agents run
  `python3 scripts/catalog.py check catalog/sources/<slug>.json` and put research notes
  in their report, not the log. Whether the §4b chartbooks (`role: reference`) are worth
  an agent each, or one agent for all of them, is an S9 sizing call.
- **S10**: the recommender reads `series/*.json` as well as `catalog.py report`, since
  derived series (spreads, P/E, a future ERP) exist only as descriptors.
- **A replacement for the discontinued S&P EPS workbook** is the first research-log
  `open` item S9 should close.
