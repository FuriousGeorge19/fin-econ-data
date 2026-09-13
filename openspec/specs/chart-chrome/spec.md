# chart-chrome Specification

## Purpose
TBD - created by archiving change s3-series-metadata. Update Purpose after archive.
## Requirements
### Requirement: In-chart source line

Every chart SHALL draw a single-line annotation inside its Plotly figure (paper
coordinates, bottom-left, muted small type) reading `<meta.source_line> · data through
<as_of.period_label>`. A multi-input dataset SHALL name each input's data-through in
the same line. Because it is part of the figure, the line SHALL appear in PNG exports
and cropped screenshots. No chart control (range slider, range buttons, legend, mode
bar) SHALL overlap the line, and time-series charts SHALL NOT use Plotly's range slider.

#### Scenario: Single-input line

- **WHEN** the 10Y Treasury chart renders with `as_of.period_label` `10 Sep 2026`
- **THEN** the figure contains the annotation `FRED DGS10 · data through 10 Sep 2026`

#### Scenario: P/E line names both inputs

- **WHEN** the P/E chart renders with price through Aug 2026 and earnings confirmed
  through Q3 2025 with the earnings input discontinued
- **THEN** the annotation reads `Shiller/Yale · S&P Global · FRED SP500 · price through
  Aug 2026 · earnings confirmed through Q3 2025, estimated since Jan 2026 (source
  discontinued)`

#### Scenario: Line survives export

- **WHEN** the user exports the chart as PNG
- **THEN** the exported image contains the source line

#### Scenario: Line unobstructed

- **WHEN** any chart renders at the desktop (400px) or mobile (300px) chart height
- **THEN** the source line is fully inside the figure with nothing drawn over it

### Requirement: About tab

Each chart SHALL have a sub-tab strip (`Chart | Table | About`). The About tab SHALL be
rendered entirely from `meta` and `as_of` and SHALL show: title and description;
sources (name, link, licence or republication note); an inputs table (label, source
series ID, cadence, publication lag, last observation, status); the next update
expected by (`due_by`, with the note that freshness is judged on the US Eastern
date); last fetched (UTC); the revision sentence; coverage (first observation,
observation count); methodology paragraphs; and notes. No About text SHALL be
hard-coded in HTML.

#### Scenario: About rendered from data

- **WHEN** a descriptor's `notes` paragraph is changed and the data file regenerated
- **THEN** the About tab shows the new paragraph with no change to `site/index.html`

#### Scenario: Discontinued input visible

- **WHEN** an input has `status: discontinued`
- **THEN** the inputs table shows `discontinued` in its status column with the
  `status_note`

### Requirement: Time-series x-axis ends at today

Charts for datasets with `kind: timeseries` SHALL set the x-axis range end to today's
US Eastern date, so the gap between the last observation and today is visible. Range
buttons SHALL count back from today. The "All" button, the mode bar's reset-axes button
and a double-click on the plot SHALL each set the range to `[first observation, today]`,
never to Plotly's padded data extent. An open-ended recession interval (`end: null`)
SHALL be shaded through to today. Charts with `kind: curve` are exempt.

#### Scenario: Gap visible

- **WHEN** the spreads chart renders on 2026-09-13 with data through 2026-09-10
- **THEN** the x-axis extends to 2026-09-13 and the last three days are empty

#### Scenario: All returns to full history through today

- **WHEN** the user clicks "All" on the P/E chart on 2026-09-13
- **THEN** the x-axis range is `['1871-01-01', '2026-09-13']`

#### Scenario: Reset matches All

- **WHEN** the user clicks the mode bar's reset-axes button or double-clicks the plot
- **THEN** the x-axis range is the same `[first observation, today]` range

#### Scenario: Curve snapshot unchanged

- **WHEN** the yield curve snapshot renders
- **THEN** its categorical tenor axis is unaffected by this rule

### Requirement: Comparison windows anchor on the last observation

Every period comparison SHALL anchor on the dataset's last observation, not today
(stat tiles such as "1-year change", table change columns, historical overlays); SHALL
resolve the comparison date to the nearest observation on or before the target using
UTC-only date arithmetic; and SHALL display the resolved date beside the comparison
(`vs 10 Sep 2025`). Stat tiles SHALL show the last observation's date beside the
latest value. One shared helper SHALL serve every tab.

#### Scenario: Resolved date shown

- **WHEN** the yield-curve table computes a 1-month change from a last observation of
  Thu 2026-09-10 and 2026-08-10 has no observation
- **THEN** the comparison uses the nearest earlier observation and the column header or
  cell shows that resolved date

#### Scenario: No local-midnight shift

- **WHEN** the page is viewed in a timezone east of UTC
- **THEN** the resolved comparison dates are identical to those a viewer in UTC sees

### Requirement: Export buttons

Each chart SHALL offer export of the underlying data as CSV and as the JSON file, and
of the chart as PNG via `Plotly.toImage` or `toImageButtonOptions`. Filenames SHALL be
`<id>_<as_of.last_observation>.<ext>`. The CSV SHALL contain one row per observation
with a header row matching the payload's fields (date-keyed payloads flattened to one
column per series). The Plotly logo SHALL be hidden (`displaylogo: false`).

#### Scenario: PNG filename carries as-of

- **WHEN** the user exports the 10Y Treasury chart with `as_of.last_observation`
  `2026-09-10`
- **THEN** the download is named `dgs10_2026-09-10.png` and includes the source line

#### Scenario: CSV of a multi-series payload

- **WHEN** the user exports the spreads data as CSV
- **THEN** the file has columns `date,10y2y,10y3m`, one row per date, blank where a
  series has no value

