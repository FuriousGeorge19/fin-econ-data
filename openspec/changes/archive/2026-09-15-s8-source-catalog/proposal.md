## Why

S8 of the cross-session plan (`~/Obsidian/Investing/Finance and Economic Data
Website/Session Plan.md`, Phase 2) is the first session on the source inventory What I
Want asks for: "a portion of the project that maintains an inventory of data sources,
access information and the types of data that can be retrieved from them … JSON of some
sort", and "maintain information on productive searches so that … you can build off some
of what you learned in past searches."

Today the only source information in the repo is the inline `sources[]` list in each
`series/<id>.json` (`{slug, name, url, licence}`), duplicated per series — `fred`
appears in five descriptors with identical name and licence text — and the synthesis
document's §4 tables in Obsidian, which nothing in the repo can read. The S3 design
(`2026-09-13-s3-series-metadata`, decision 1) reserved the `slug` seam for exactly this:
"S8's `catalog/sources/<slug>.json` can hoist the shared fields; until then they are
inline."

Three later sessions consume what this change builds and shape its design: **S9**, a
~12-agent workflow filling one catalogue file per remaining source from an exemplar and
a README, "unknown" allowed, a URL on every claim, a done-check each agent runs on its
own file; **S10**, the dry run that recommends charts for US Equity Valuations from the
catalogue alone (the test of whether the inventory pays off); and **S11b**, where the
chart-8 agent must record the ICE BofA republication terms in the catalogue before
rendering, without editing any shared file.

Decided by the user on 2026-09-14: design and build in this one session; a
provider-owned dataset that is hosted on FRED lives under its rights holder, marked
`via: fred`; each source carries a structured `datasets[]` list now.

## What Changes

- **A source catalogue** under `catalog/`: `sources/<slug>.json`, one file per rights
  holder (a set of terms and a way in), each with `access`, `terms`, and a `datasets[]`
  list (native cadence, coverage, lag, status, ids, units, `topics` from a small
  controlled vocabulary, per-dataset `access`/`terms` overrides, `via` for data reached
  through another catalogued source). `README.md` states the rules an S9 agent works
  from. Four seeds: `fred`, `shiller`, `spglobal`, `nber` — `access` and `terms` read
  from each official page this session; FRED's dataset families verified through the
  FRED API; what could not be read (S&P's pages return 403) is marked as such.
- **A stdlib validator, resolver and report**: `scripts/catalog.py` (`check [path…]`,
  `report [--topic T]`) plus `tests/test_catalog.py`. `check` on one file is the
  done-check a workflow agent runs in a shared checkout; bare `check` cross-references
  every `series/*.json`.
- **Descriptor hoist**: `series/<id>.json` `sources[]` becomes a list of references
  `{slug, dataset?, url?, note?}`; `inputs[]` gains optional `dataset`. The fetcher
  resolves references at fetch time (`series_meta.meta_from_descriptor()`), so
  `meta.sources[]` in the data file carries the catalogue's name, licence sentence,
  terms status and hosting note, and the browser never fetches the catalogue.
  **BREAKING (descriptor schema)**: `name` and `licence` are no longer allowed in a
  descriptor's `sources[]`. The `sp500_pe` price input's source moves from `fred` to
  `spglobal` (S&P DJI terms, via FRED), per the rights-holder rule.
- **About tab**: shows "via FRED" for hosted data and the terms status when it is not
  `verified`. Two template lines in `site/js/lib/asof.js`; old-shape data files still
  render.
- **Research log**: `catalog/research-log.md`, a fixed entry template, edited only by
  the session owner (workflow agents report research notes; the merge step appends).
  Back-filled with the productive searches from April–September 2026.
- **FRED API attribution footer**: reading the FRED API Terms of Use for the `fred` seed
  turned up a required notice the site did not carry; the user asked for it in the same
  session, so `scripts/build_site.py`'s page shell gains a footer with it (the one
  generator change in this proposal, with a `site-build` spec delta).
- No change to the workflow, any chart type, or `source_line`. `data/*.json` fixtures
  on `main` are not regenerated; the live site picks up the resolved shape on its next
  scheduled fetch.

## Capabilities

### New Capabilities

- `source-catalog`: the catalogue files and their schema, the boundary and `via` rules,
  the researched-or-not convention, the `terms.status` definitions, the topics
  vocabulary, the validator/report script, and the research log.

### Modified Capabilities

- `series-metadata`: "Series descriptor file" — `sources[]` becomes catalogue references
  and `inputs[]` may name a dataset; the validates-scenario requires every slug to exist.
  "Header contract of meta, as_of and payload" — `meta.sources[]` is resolved through the
  catalogue at fetch time rather than copied verbatim.
- `chart-chrome`: "About tab" — sources show the hosting source and a non-verified terms
  status when the resolved entry carries them.
- `site-build`: "Generated multi-page site from descriptors and manifests" — the page
  shell carries a footer with the FRED API attribution notice.

## Impact

- New: `catalog/README.md`, `catalog/sources/{fred,shiller,spglobal,nber}.json`,
  `catalog/research-log.md`, `scripts/catalog.py`, `tests/test_catalog.py`.
- Modified: `scripts/series_meta.py`, the five `series/*.json`, `site/js/lib/asof.js`,
  `scripts/build_site.py` and `site/css/site.css` (the footer), `tests/test_build_site.py`
  (one test for it), `CLAUDE.md`, `ARCHITECTURE.md`, `HOW-IT-WORKS.md`.
- Workflow: untouched. `scripts/fetch_all.py` already runs every fetcher; a bad
  catalogue reference fails that series' fetch (recorded in `data/fetch_status.json`)
  and the gating `pytest` step fails before deploy, since `tests/test_catalog.py` checks
  every descriptor reference.
- Rollback: revert the one commit. Data files written under the new contract carry a
  superset of the old `meta.sources[]` fields, so the previous `asof.js` renders them
  unchanged.
