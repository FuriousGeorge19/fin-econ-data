## ADDED Requirements

### Requirement: Per-series fetch script

Each data series SHALL be produced by a dedicated Python script in `scripts/`
named `fetch_<name>.py` that writes a single JSON file to `data/<name>.json`. Scripts
SHALL use only the Python standard library plus pandas (for Excel sources); there is no
`requirements.txt`, no build step, and no shared framework between scripts.

#### Scenario: A fetcher produces its data file

- **WHEN** `python scripts/fetch_<name>.py` runs successfully
- **THEN** `data/<name>.json` is written (directory created if absent) and a summary
  line including the observation count and date range is printed to stdout

#### Scenario: Fetcher fails loudly

- **WHEN** a required source is unreachable or a required input is invalid
- **THEN** the script prints an `ERROR:` message to stderr and exits with a non-zero
  status, leaving no partial half-written output relied upon downstream

### Requirement: FRED access pattern

Scripts that read from FRED SHALL call the St. Louis Fed observations API over HTTPS
using an API key supplied via the `FRED_API_KEY` environment variable, sending a
`User-Agent: joemirza-site/1.0` header. A missing key SHALL cause scripts whose primary
source is FRED to exit with an error.

#### Scenario: Missing FRED key for a FRED-primary fetcher

- **WHEN** `fetch_treasury.py` or `fetch_yield_curve.py` runs with no `FRED_API_KEY` set
- **THEN** the script prints `ERROR: FRED_API_KEY environment variable not set` and exits non-zero

### Requirement: Missing-value handling

FRED observations with the sentinel value `"."` SHALL be dropped during fetch. Numeric
values SHALL be parsed to floats. No missing values are forward-filled or interpolated
at the pipeline level (series-specific forward-fill, where it exists, is defined in that
series' spec).

#### Scenario: FRED returns gaps

- **WHEN** a FRED response contains observations with value `"."`
- **THEN** those observations are excluded from the output JSON and only real numeric
  observations remain

### Requirement: JSON output schema conventions

Each output JSON SHALL include descriptive metadata (`title`, `units`, `frequency`,
`source`) and a UTC `last_updated` timestamp formatted `YYYY-MM-DD HH:MM UTC`, alongside
the observations payload. Observations SHALL be ordered chronologically (oldest first)
or keyed by date such that the site can render them on a time axis without re-sorting.

#### Scenario: Output carries metadata and timestamp

- **WHEN** any fetcher writes its JSON file
- **THEN** the file contains `title`, `units`, `frequency`, `source`, and a
  `last_updated` field in `YYYY-MM-DD HH:MM UTC` form

### Requirement: Daily timeline and date conventions

All series SHALL be presented on a daily timeline. Monthly historical data SHALL be
assigned to the first of the month (`YYYY-MM-01`). Frequency differences SHALL be
communicated by natural gaps in the data rather than by upsampling lower-frequency
series to daily points.

#### Scenario: Monthly data placed on first-of-month

- **WHEN** a monthly observation for a given month is emitted (e.g. an S&P 500 P/E month)
- **THEN** its date is `YYYY-MM-01` and no synthetic intra-month points are generated

### Requirement: JSON files are the fetcher/site contract

The JSON files in `data/` SHALL be the sole interface between fetchers and the site.
The fetcher's output JSON is what the corresponding tab consumes — there is no other
data path between Python and the browser.

#### Scenario: Site consumes only JSON

- **WHEN** the site renders a series
- **THEN** it reads the corresponding `site/data/<name>.json` and renders the chart
  and any tables from that file alone