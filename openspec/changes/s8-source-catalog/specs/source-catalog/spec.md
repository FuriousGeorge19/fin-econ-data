## ADDED Requirements

### Requirement: One catalogue file per rights holder

The source catalogue SHALL live at `catalog/sources/<slug>.json`, one file per source,
where a source is one set of terms and one access method and `<slug>` matches
`^[a-z0-9][a-z0-9-]*$` and equals the file's `slug` field. A dataset SHALL get its own
file only when its terms differ from its host's or its publisher serves it directly;
public-domain data reached only through FRED SHALL be a dataset of `fred`, naming the
originating agency in its description. Data reached through another catalogued source
SHALL say so with `via: <slug>` in the source-level or dataset-level `access`; a
dataset's `access` and `terms` SHALL be merged over the source's key by key by one shared
function used by both the validator and the resolver. `via` SHALL name an existing slug
and SHALL never be the file's own.

#### Scenario: Provider-owned data hosted on FRED

- **WHEN** the S&P 500 index level is catalogued
- **THEN** it is a dataset of `catalog/sources/spglobal.json` whose merged `access`
  carries `via: fred` and `ids: ["SP500"]`, and `catalog/sources/fred.json` is not
  edited

#### Scenario: Public-domain series on FRED

- **WHEN** the Treasury constant-maturity yields are catalogued
- **THEN** they are a dataset of `catalog/sources/fred.json` whose description names
  the Federal Reserve's H.15 release, and no `catalog/sources/h15.json` exists

### Requirement: Source entry schema

A catalogue file SHALL carry exactly the top-level keys `schema_version`, `slug`,
`role` (`data` or `reference`), `name`, `short_name`, `homepage`, `description`,
`access`, `terms`, `datasets`, `verified`, and optionally `notes`; an unknown key SHALL
fail validation naming the file. `access` SHALL carry `method` (`api`, `file-download`,
`manual-download`, `web-page` or `none`), `url`, `format`, `auth` (`none`, `free-key`,
`paid-key`, `login` or `manual`), and MAY carry `rate_limit`, `via`, `notes` and
`read_from`. `terms` SHALL carry `summary` and `status` and MAY carry `url`, `quote`
and `read_from`. `verified` SHALL carry `on` (a date not after today) and `by`. Every
dataset SHALL carry `id` (unique within the file), `name`, `gives`, `ids`, `topics`,
`cadence` (`daily`, `weekly`, `monthly`, `quarterly`, `annual`, `irregular` or
`"unknown"`), `coverage` (`{start, end}` with `end` a date or `"ongoing"`, or
`"unknown"`), `publication_lag_business_days` (an integer ≥ 0 or `"unknown"`) and
`status` (`active` or `discontinued`), and MAY carry `units`, `access` and `terms`
overrides, `roadmap`, `verified_on`, `read_from` and `notes`. A `reference` source SHALL
have no datasets. A `discontinued` dataset SHALL have a dated `coverage.end`. Any scalar
fact MAY be the string `"unknown"`, meaning it was researched and could not be
established; an absent optional field means it was not researched. `url` fields SHALL
start with `http://` or `https://` and MAY contain placeholders such as `{year}`.
Catalogue text SHALL be plain text, never HTML.

#### Scenario: Unknown key

- **WHEN** a file carries a top-level key `licence` or a dataset key `used_by`
- **THEN** validation fails naming the file and the key

#### Scenario: Discontinued dataset

- **WHEN** a dataset has `status: discontinued` and `coverage.end: "ongoing"`
- **THEN** validation fails naming the file and the dataset id

### Requirement: Terms status carries evidence

`terms.status` SHALL be one of `verified` (the terms were read and permit the site's
use), `restricted` (the terms were read and limit republication), `unverified` (a terms
page was found but not read), or `unknown` (no terms statement was found). `verified`
and `restricted` SHALL require `terms.url` and a non-empty verbatim `terms.quote`;
`unverified` SHALL require `terms.url`. A fact block (`access`, `terms`, a dataset) MAY
carry `read_from` — the URL or list of URLs it was read from; the validator SHALL NOT
require it, and a workflow verifier SHALL treat a block without it as unverified.

#### Scenario: Verified without a quote

- **WHEN** `terms.status` is `verified` and `terms.quote` is absent or empty
- **THEN** validation fails naming the file

#### Scenario: Copied, not read

- **WHEN** a fact block's source is not a web page (a notice inside a downloaded
  workbook) or the page could not be fetched
- **THEN** it carries no `read_from`, its `notes` say so, and `catalog.py report` counts
  it among the file's blocks lacking `read_from`

### Requirement: Datasets carry topics from a controlled vocabulary

Every dataset SHALL carry `topics`, a non-empty list drawn from the vocabulary defined in
`scripts/catalog.py` (initially `rates`, `credit`, `inflation`, `equity-valuation`,
`equity-returns`, `macro`, `recession-dating`, `real-estate`, `global`,
`expectations`). A topic outside the vocabulary SHALL fail validation naming the file
and the value.

#### Scenario: Query by topic

- **WHEN** `python3 scripts/catalog.py report --topic equity-valuation` runs against the
  seeds
- **THEN** it lists `shiller/ie-data` and `spglobal`'s datasets and no `fred` yield
  family

### Requirement: Validator, resolver and report in a stdlib script

`scripts/catalog.py` SHALL use only the Python standard library and SHALL provide
`slugs()`, `load(slug)`, `validate()`, `resolve_source_ref()`, and a command line:
`check [path …]` validates the named files alone (schema plus `via` slugs present on
disk) or, with no paths, every file plus every `series/*.json` reference, exiting 1 with
one line per problem naming the file; `report [--topic T]` prints each source's role,
datasets, the series that use it (derived from `series/*.json`, never stored), terms
status, verified date and count of fact blocks lacking `read_from`, then the `via`
reverse index. `tests/test_catalog.py` SHALL call the same `validate()` for every file
and every descriptor reference.

#### Scenario: One file in a shared checkout

- **WHEN** an agent runs `check catalog/sources/damodaran.json` while another agent's
  file in the same directory is half-written
- **THEN** only problems in `damodaran.json` are reported

#### Scenario: Descriptor names a missing source

- **WHEN** `series/x.json` references a slug with no catalogue file
- **THEN** bare `check` and `pytest` both fail naming `series/x.json` and the slug

### Requirement: Research log

`catalog/research-log.md` SHALL hold one entry per productive search, newest first,
each with a dated heading, `topics:`, the question, what was searched or read (with
URLs), what was found, an outcome of `adopted`, `rejected`, `gap` or `open`, and where
it landed. It SHALL be edited only by the session owner; a workflow agent SHALL put its
research notes in its report in the same template, for the merge step to append.

#### Scenario: A search that found nothing

- **WHEN** a session searches for a free daily S&P 500 history longer than ten years
  and finds none
- **THEN** the log gains an entry with outcome `gap` or `open` naming what was searched,
  so the next session does not repeat it
