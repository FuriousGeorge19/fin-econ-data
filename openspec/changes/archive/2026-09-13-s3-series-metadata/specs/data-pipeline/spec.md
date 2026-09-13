## MODIFIED Requirements

### Requirement: JSON output schema conventions

Each output JSON SHALL follow the header contract defined by the `series-metadata`
capability: a `meta` object (the dataset's `series/<id>.json` descriptor, copied
verbatim minus `presentation`) and an `as_of` object (`fetched_at` in ISO 8601 UTC,
`first_observation`, `last_observation`, `period_label`, `observation_count`, `due_by`,
and per-input / per-series as-of where applicable), alongside the observations
payload. Descriptive metadata (`title`, `units`, `frequency`, `source`, `methodology`)
SHALL live only under `meta`. Observations SHALL be ordered chronologically (oldest
first) or keyed by date such that the site can render them on a time axis without
re-sorting. Files SHALL be written atomically through the shared `write_json`.

#### Scenario: Output carries metadata and as-of

- **WHEN** any fetcher writes its JSON file
- **THEN** the file contains `meta` with the descriptor's `title`, `units`, `cadence`
  and `sources`, and `as_of` with `fetched_at`, `last_observation` and `due_by`
