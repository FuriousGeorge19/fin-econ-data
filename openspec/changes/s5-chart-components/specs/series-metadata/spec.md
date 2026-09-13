## MODIFIED Requirements

### Requirement: Series descriptor file

Every dataset SHALL have a hand-maintained descriptor at `series/<id>.json`, where
`<id>` is the data file stem (`dgs10`, `sp500_pe`, `yield_curve`, `spreads`, `usrec`).
The descriptor SHALL contain: `id`; `title`; `short_title`; `kind` (`timeseries`,
`curve`, or `intervals`); `units`; `cadence` (`daily`, `monthly`, or `quarterly`);
`publication_lag_business_days` (integer); `revisions` (`none`, `occasional`,
`regular`, or `retroactive`) with a `revision_note`; `source_line` (the short form
drawn inside the chart); `sources` (a list of `{slug, name, url, licence}`); `inputs`
(a list of `{id, label, source, series_id, cadence, publication_lag_business_days}`,
each optionally `required` (default true), `manual`, and `status` (`active` by default,
or `discontinued` with a `status_note`)); and `methodology` and `notes` (arrays of
plain-text paragraphs). A `presentation` object MAY be present, with the schema defined
by the `chart-components` capability; it SHALL NOT be embedded into the data file, and a
descriptor without it is a data-only dataset with no page. A `fetcher` string MAY name
the fetch script under `scripts/` (default `fetch_<id>.py`). The descriptor set SHALL be
the single source of the list of site data files and fetch scripts: `scripts/dev.sh`,
`scripts/build_site.py`, `scripts/fetch_all.py`, the workflow's seed step, and
`scripts/staleness.py` SHALL derive their lists from `series/*.json` rather than
carrying their own.

#### Scenario: Descriptor validates

- **WHEN** `pytest` runs `tests/test_series_metadata.py`
- **THEN** every `series/*.json` parses, carries every required field, uses only the
  enumerated values for `kind`, `cadence`, `revisions` and `inputs[].status`, every
  `inputs[].source` names a slug present in `sources`, every `presentation` satisfies
  the `chart-components` schema, and every `fetcher` names an existing script

#### Scenario: File list derives from descriptors

- **WHEN** a sixth descriptor `series/<new>.json` is added
- **THEN** `scripts/dev.sh`, `scripts/build_site.py`, `scripts/fetch_all.py`, the
  workflow seed step and the staleness check include `<new>` without any of them being
  edited

### Requirement: Header contract of meta, as_of and payload

Each `data/<id>.json` SHALL consist of `meta` (the descriptor minus `presentation` and
`fetcher`, copied verbatim at fetch time), `as_of` (runtime fields written by the
fetcher), and the unchanged payload keys (`observations` as a list or a date-keyed
object, `series`, `recessions`, `tenors`, `tenor_months`). `as_of` SHALL carry
`fetched_at` (ISO 8601 UTC), `first_observation`, `last_observation`, `period_label`,
`observation_count`, and `due_by` (all dates `YYYY-MM-DD`). When the descriptor lists
more than one input, `as_of.inputs` SHALL carry `{last_observation, period_label,
due_by}` per input id. When the payload holds more than one series (spreads legs,
yield-curve tenors), `as_of.series` SHALL carry `{first_observation, last_observation,
observation_count, period_label, due_by}` per series key. `as_of.latest_value` MAY be
present. The descriptive fields formerly at the top level (`title`, `units`,
`frequency`, `source`, `methodology`, `description`, `series_id`) SHALL live only under
`meta`.

#### Scenario: Single-input daily series

- **WHEN** `fetch_treasury.py` writes `data/dgs10.json`
- **THEN** the file has `meta.id` equal to `dgs10`, `as_of.last_observation` equal to
  the date of the last observation in the payload, an `as_of.period_label` such as
  `10 Sep 2026`, `as_of.due_by` per the data-freshness rule, and no top-level `title`,
  `units`, `frequency`, `source` or `series_id`

#### Scenario: Multi-input dataset

- **WHEN** `fetch_sp500_pe.py` writes `data/sp500_pe.json`
- **THEN** `as_of.inputs.price` and `as_of.inputs.earnings` each carry
  `last_observation`, `period_label` and `due_by`, and `as_of.inputs.earnings`
  additionally carries `confirmed_through` and `value`

#### Scenario: Multi-series payload

- **WHEN** `fetch_spreads.py` writes `data/spreads.json`
- **THEN** `as_of.series["10y2y"].first_observation` is `1976-06-01` and
  `as_of.series["10y3m"].first_observation` is `1981-09-01`, each with its own
  `last_observation`, `observation_count`, `period_label` and `due_by`

#### Scenario: Payload shapes unchanged

- **WHEN** any fetcher writes its file under the new contract
- **THEN** every existing read of `observations`, `series`, `recessions`, `tenors`
  and `tenor_months` in `tests/` and the chart type modules under `site/js/charts/`
  still finds those keys at the top level with the same shape
