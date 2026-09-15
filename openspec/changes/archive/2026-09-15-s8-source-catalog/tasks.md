## 1. Validator, README, exemplar

- [x] 1.1 `scripts/catalog.py` (stdlib only): `CATALOG_DIR`, `TOPICS`, `slugs()`,
      `load()`, `load_all()`, `merge_block()`, `validate(entry, *, slug, known_slugs)`
      returning a list of problem strings, `resolve_source_ref(ref)`, `used_by()`
      derived from `series/*.json`; CLI `check [path …]` and `report [--topic T]` per
      design decision 6, including every consistency rule listed there
- [x] 1.2 `catalog/README.md`: what the catalogue is; the boundary rule and `via`/merge
      rule (decision 1); `"unknown"` vs absent and `read_from` (decision 3); the
      `terms.status` table; `ids` convention per access method; "daily = each business
      day"; plain text, no HTML; never store `used_by`; `source_line` stays hand-written;
      the field table with "`python3 scripts/catalog.py check` is authoritative";
      "adding a source" ending in `check catalog/sources/<slug>.json`; the research-log
      template and the owner-edits-only rule; `shiller.json` named as the exemplar
- [x] 1.3 `catalog/sources/shiller.json` — the exemplar: `access` and `terms` read from
      the Shiller data page this session (`read_from`, `verified.on` 2026-09-14); one
      dataset `ie-data` with every field filled
- [x] 1.4 `python3 scripts/catalog.py check catalog/sources/shiller.json` clean

## 2. Seeds

- [x] 2.1 `catalog/sources/fred.json`: `access` from the FRED API docs, `terms` from the
      FRED legal/terms page (both `read_from`); the description sentence from decision
      1; datasets `dgs`, `gs`, `tb`, `dfii`, `breakevens`, `fedfunds`, `sofr`, `cpi`,
      `usrec`, `nfci`, `expinf`, `hqmcb`, `t10y-spreads` from synthesis §4c, each with
      `topics` and start/frequency/notes verified via the FRED API (`read_from` = the
      series pages); `mich` left out as third-party data under the boundary rule
- [x] 2.2 `catalog/sources/spglobal.json`: `sp-500-eps` (manual workbook, quarterly,
      `discontinued`, `coverage.end` 2026-01-31, `auth: manual`) and `sp500-index`
      (`via: fred`, `ids: ["SP500"]`, native daily, trailing ten years, terms from the
      FRED series notes page); `terms.status` per decision 3's evidence rule
- [x] 2.3 `catalog/sources/nber.json`: `chronology` as a `web-page` dataset (no `via`),
      note pointing at `fred/usrec`; `terms` from the NBER page
- [x] 2.4 Bare `python3 scripts/catalog.py check` clean; `report` output matches the
      verification list in design decision 6

## 3. Hoist

- [x] 3.1 `scripts/series_meta.py`: `meta_from_descriptor()` resolves `sources[]` through
      `catalog.resolve_source_ref()` (lazy import); raises naming the descriptor and slug
- [x] 3.2 `series/{dgs10,spreads,yield_curve,usrec,sp500_pe}.json`: `sources[]` to
      references with `dataset`; `name`/`licence` removed; `inputs[].dataset` added;
      `sp500_pe` price input `source` → `spglobal`
- [x] 3.3 `site/js/lib/asof.js`: `renderAboutHTML()` shows `dataset_name`, "via X" and
      "terms <status>" when present (decision 5); no colour literal, no forbidden key
- [x] 3.4 `tests/test_catalog.py`: every file validates (parametrized over `slugs()`);
      every descriptor reference resolves; descriptor `sources[]` allow-list `{slug,
      dataset, url, note}`; `resolve_source_ref()` unit tests; every committed
      `data/*.json` `meta.sources[].slug` exists; sandbox negative tests per validation
      rule (unknown key, bad `via`, self `via`, duplicate dataset id, `verified` without
      quote, discontinued with `ongoing`, topic outside the vocabulary, `reference` with
      datasets, future `verified.on`)
- [x] 3.5 `tests/test_series_metadata.py` unchanged; confirm `test_input_sources_exist`
      still passes with the new shape

## 4. Research log

- [x] 4.1 `catalog/research-log.md`: header, template, and the back-filled entries listed
      in design decision 7, each marked "back-filled 2026-09-14, not re-verified", plus
      this session's terms-page verification entry recording what each page said

## 5. Verify

- [x] 5.1 `pytest -m "not staleness"` green (87 + new); full `pytest` with `FRED_API_KEY`
- [x] 5.2 **Manual browser check**: run the fetchers locally, `scripts/dev.sh` on
      `127.0.0.1`, then `/charts/sp500_pe/` About (three sources, dataset names, "via
      FRED", terms status), `/charts/dgs10/` and `/charts/spreads/` About (unchanged apart
      from status text), zero console errors (manual browser check)
- [x] 5.3 `git checkout -- data/` after 5.2; `git status` shows no fixture change

## 6. Docs and validate

- [x] 6.1 `CLAUDE.md`: Architecture tree (`catalog/`), Key Files rows, "Adding a data
      source" pattern and the new `sources[]` shape under "adding a series", Correctness
      Tests paragraph, Licence Notes pointer, changelog entry
- [x] 6.2 `ARCHITECTURE.md`: one decision-log entry. `HOW-IT-WORKS.md`: descriptor
      section updated; short "The source catalogue" subsection
- [x] 6.3 `openspec validate s8-source-catalog` clean; stop for review with `git status`
- [x] 6.4 (added at review) FRED API attribution footer: `render_shell()` in
      `scripts/build_site.py`, `.site-footer` in `site/css/site.css`, a
      `tests/test_build_site.py` assertion that every generated page carries the
      sentence, a `site-build` spec delta; browser check (manual browser check)
