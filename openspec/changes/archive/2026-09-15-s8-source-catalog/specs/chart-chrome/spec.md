## MODIFIED Requirements

### Requirement: About tab

Each card SHALL have a sub-tab strip (`Chart | Table | About`) built by the card chrome
(`site/js/lib/card.js`). The About tab SHALL be rendered entirely from `meta` and
`as_of` and SHALL show: title and description; sources (name, link, licence or
republication note, the dataset name when the entry carries one, the hosting source
when the entry carries `via`, and the terms status when the entry carries a
`terms_status` other than `verified`); an inputs table (label, source series ID, cadence,
publication lag, last observation, status); the next update expected by (`due_by`, with
the note that freshness is judged on the US Eastern date); last fetched (UTC); the
revision sentence; coverage (first observation, observation count); methodology
paragraphs; and notes. No About text SHALL be hard-coded in HTML or in a generator
template. A data file whose `meta.sources[]` predates the catalogue (no `dataset_name`,
`via` or `terms_status`) SHALL render as before.

#### Scenario: About rendered from data

- **WHEN** a descriptor's `notes` paragraph is changed and the data file regenerated
- **THEN** the About tab shows the new paragraph with no change to any file under
  `site/`

#### Scenario: Discontinued input visible

- **WHEN** an input has `status: discontinued`
- **THEN** the inputs table shows `discontinued` in its status column with the
  `status_note`

#### Scenario: Hosted source and terms status

- **WHEN** `data/sp500_pe.json`'s `meta.sources[]` carries the resolved S&P Global index
  entry with `via: "FRED"` and `terms_status: "unverified"`
- **THEN** the Sources list shows that entry's name and dataset name linked to the FRED
  series page, followed by its licence sentence, "via FRED", and "terms unverified"

#### Scenario: Pre-catalogue data file

- **WHEN** a data file's `meta.sources[]` entries carry only `slug`, `name`, `url` and
  `licence`
- **THEN** the Sources list renders each as name, link and licence with no hosting or
  status text
