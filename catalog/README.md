# Source catalogue

`catalog/sources/<slug>.json` — one file per data source, recording what it is, how to
reach it, under what terms, what datasets it offers, and when that was last checked and
from which page. `catalog/research-log.md` records the searches that produced or
rejected entries, so a later session builds on them instead of searching again.

The catalogue is read by three things: `scripts/series_meta.py` at fetch time (a
descriptor's `sources[]` references resolve to the name, licence sentence, terms status
and hosting note the About tab shows), `python3 scripts/catalog.py report` (what exists,
by topic, and which series use it), and people or agents planning charts. Nothing under
`site/` reads it; the data file is the contract with the browser.

`python3 scripts/catalog.py check` is the authority on the schema. The field table
below is a rendering of what `check` enforces; if they ever disagree, `check` wins and
the table is wrong.

## Rules

1. **One file per rights holder.** A source is one set of terms and one way in. A
   dataset gets its own file only when its terms differ from its host's (S&P DJI's
   `SP500` on FRED; ICE BofA's `BAML*` on FRED) or the publisher serves it directly in a
   form we would use (Treasury.gov's daily curve CSVs). Public-domain data reached only
   through FRED is a FRED dataset — name the originating agency (Board of Governors
   H.15, BLS, Cleveland Fed) in `gives`.
2. **Hosted data says `via`.** Data reached through another catalogued source carries
   `"via": "<slug>"` in `access`, either at the source level (a provider whose whole
   presence is through FRED) or on the dataset. A dataset's `access` and `terms` are
   merged over the source's key by key — the dataset's key wins — so "what applies to
   this dataset" has one answer. `via` never names the file's own slug.
3. **Researched or not, explicitly.** Any scalar fact may be the string `"unknown"`,
   meaning you looked and could not establish it. An absent optional field means nobody
   looked. Never guess.
4. **Every fact block may say where it was read.** `access`, `terms` and each dataset
   may carry `read_from`: the URL, or list of URLs, the facts were read from. `check`
   does not require it; a workflow verifier does, and treats a block without it as
   unverified. Read official pages only — the provider's own site, or the FRED series
   page for data hosted there.
5. **`terms.status` means something specific** (the table below). `verified` and
   `restricted` need the terms URL and a verbatim quote; `unverified` needs the URL.
6. **`ids` depends on the access method.** API → series ids (`"DGS10"`); file or manual
   download → file name(s) or the query value that selects the dataset; web page → `[]`.
   Column names go in `gives`, not `ids`.
7. **Cadence is the native publication cadence.** `daily` means each business day. A
   descriptor's input may use the data at a different cadence (the P/E takes FRED's
   monthly average of a daily series); that is the descriptor's business.
8. **Never store which series use a source.** `catalog.py report` derives it from
   `series/*.json`.
9. **Plain text only.** `name`, `summary`, `gives` and notes are rendered raw into the
   About tab; no HTML.
10. **`source_line` in a descriptor stays hand-written.** The catalogue's `short_name`
    does not replace it.
11. **The research log is edited by the session owner only.** A workflow agent puts its
    research notes in its report, in the entry template below; the merge step appends
    them.

## Fields

Top level — all required unless marked optional; unknown keys fail `check`:

| Field | Meaning |
|---|---|
| `schema_version` | `1` |
| `slug` | Equals the file name; `^[a-z0-9][a-z0-9-]*$` |
| `role` | `data` (something we can fetch) or `reference` (a chartbook or dashboard we look at for framing; has no datasets) |
| `name` | Display name — what the About tab shows |
| `short_name` | Compact form, used as the hosting note ("via FRED") |
| `homepage` | URL |
| `description` | One to three sentences: what it is |
| `access` | See below |
| `terms` | See below |
| `datasets` | List (empty for `reference`) |
| `verified` | `{on: YYYY-MM-DD, by: who}` — when `access` and `terms` were last checked |
| `notes` | Optional list of strings |

`access` — `method`, `url`, `format`, `auth` required:

| Field | Meaning |
|---|---|
| `method` | `api`, `file-download`, `manual-download` (a person downloads it), `web-page` (read, not fetched), `none` |
| `url` | Entry point. Must start with `http://` or `https://`; may contain a placeholder such as `{year}` |
| `format` | `json`, `csv`, `xls`, `xlsx`, `html`, … |
| `auth` | `none`, `free-key`, `paid-key`, `login`, `manual` |
| `rate_limit` | Optional string, or `"unknown"` |
| `via` | Optional slug of the hosting source |
| `notes` | Optional list of strings (quirks: caching, missing-value sentinel, …) |
| `read_from` | Optional URL or list of URLs |

`terms` — `summary` and `status` required:

| Field | Meaning |
|---|---|
| `summary` | The sentence the About tab shows as the licence / republication note |
| `status` | See the table below |
| `url` | The terms page, or `"unknown"` |
| `quote` | A verbatim sentence from the terms page |
| `read_from` | Optional URL or list of URLs |

| `terms.status` | Meaning | What `check` requires |
|---|---|---|
| `verified` | The terms were read and permit what the site does (republish values on a public, free page with attribution) | `url` and a non-empty `quote` |
| `restricted` | The terms were read and limit republication or redistribution; `summary` states the limit | `url` and a non-empty `quote` |
| `unverified` | A terms page was found but not read or quoted | `url` |
| `unknown` | The official site was searched and no terms statement was found | — (`url` may be `"unknown"`) |

`datasets[]` — one entry per thing you can fetch:

| Field | Meaning |
|---|---|
| `id` | Kebab-case, unique within the file |
| `name` | Shown on the About tab after the source name |
| `gives` | What it contains — fields, series, columns — in plain text; name the originating agency for data hosted elsewhere |
| `ids` | Series ids, file names, or the selecting query value (rule 6) |
| `topics` | One or more of: `rates`, `credit`, `inflation`, `equity-valuation`, `equity-returns`, `macro`, `recession-dating`, `real-estate`, `global`, `expectations` (the list lives in `scripts/catalog.py`; extend it there) |
| `units` | Optional: `percent`, `index`, `ratio`, `usd-bn`, … |
| `cadence` | `daily`, `weekly`, `monthly`, `quarterly`, `annual`, `irregular`, or `"unknown"` |
| `coverage` | `{start, end}` — `YYYY`, `YYYY-MM` or `YYYY-MM-DD`; `end` may be `"ongoing"`; or `"unknown"`. A `discontinued` dataset needs a dated `end` |
| `publication_lag_business_days` | Integer ≥ 0 (0 = same day), or `"unknown"` |
| `status` | `active` or `discontinued` |
| `access` | Optional partial override of the source's `access` (rule 2) |
| `terms` | Optional partial override of the source's `terms` |
| `roadmap` | Optional list of strings: `"chart 8"`, `"item 11"` |
| `verified_on` | Optional `YYYY-MM-DD` for a dataset checked on a different day than the file |
| `read_from` | Optional URL or list of URLs |
| `notes` | Optional list of strings |

`shiller.json` is the exemplar: small, every block filled, every fact block with a
`read_from`.

## Adding a source

1. Decide the file boundary with rule 1. If the data is on FRED under FRED's own terms,
   it is a dataset in `fred.json`, not a new file.
2. Copy `shiller.json` to `catalog/sources/<slug>.json` and fill it from the official
   pages. Record each page in `read_from`. Write `"unknown"` for what you could not
   establish; leave out what you did not research.
3. Set `terms.status` by the table above, with the quote.
4. Run `python3 scripts/catalog.py check catalog/sources/<slug>.json` until it prints
   nothing. (Bare `check` also cross-references every `series/*.json`; use the one-file
   form when other files in the directory may be in progress.)
5. Put your research notes — including searches that found nothing — in your report,
   in the log template below. Do not edit `research-log.md` yourself unless you are the
   session owner.

To use the source from a series, reference it in `series/<id>.json`:

```json
"sources": [{"slug": "shiller", "dataset": "ie-data"}],
"inputs":  [{"id": "price", "source": "shiller", "dataset": "ie-data", ...}]
```

A `sources[]` entry may carry only `slug`, `dataset`, `url` (the series-specific page;
defaults to the source's homepage) and `note`. Name and licence come from the catalogue
at fetch time.

## Research log

`catalog/research-log.md`, newest entry first. One entry per productive search — a
search that found nothing is productive if it stops the next session repeating it.

```markdown
## YYYY-MM-DD — Short title
topics: rates, credit
- **Question**: what we were trying to find
- **Searched / read**: the queries and pages, with URLs
- **Found**: what the pages actually said
- **Outcome**: adopted | rejected | gap | open
- **Landed in**: catalog/sources/<slug>.json (dataset <id>) · series/<id>.json · Session Plan item N
```
