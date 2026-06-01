# data-pipeline Specification

## Purpose

The shared fetch → `data/<name>.json` → `site/data/<name>.json` contract: per-series
Python fetch scripts, the FRED access pattern, JSON output schema conventions,
missing-value handling, and the daily-timeline / 1st-of-month date rules that let
every series render on a common time axis without rework.

## Requirements

### Requirement: Per-series fetch script

Each data series SHALL be produced by a dedicated Python script in `scripts/`
named `fetch_<name>.py` that writes a single JSON file to `data/<name>.json`. Scripts
SHALL use only the Python standard library plus pandas (for Excel sources). There is no
`requirements.txt`, no build step, and no external runtime framework. Shared **internal**
utility modules under `scripts/` (e.g. `fred_utils.py`) ARE permitted and encouraged to
remove duplication; the "no framework" rule constrains external runtime dependencies
(package manifests, build systems, web frameworks), not internal code reuse.

#### Scenario: A fetcher produces its data file

- **WHEN** `python scripts/fetch_<name>.py` runs successfully
- **THEN** `data/<name>.json` is written (directory created if absent) and a summary
  line including the observation count and date range is printed to stdout

#### Scenario: Fetcher fails loudly

- **WHEN** a required source is unreachable or a required input is invalid
- **THEN** the script prints an `ERROR:` message to stderr and exits with a non-zero
  status, leaving no partial half-written output relied upon downstream

#### Scenario: Fetchers share internal helpers

- **WHEN** multiple fetch scripts need the same FRED access boilerplate
- **THEN** they MAY import a shared module under `scripts/` (e.g. `fred_utils.py`) rather
  than duplicating it, and this does not count as an external framework

### Requirement: FRED access pattern

Scripts that read from FRED SHALL call the St. Louis Fed observations API over HTTPS
using an API key supplied via the `FRED_API_KEY` environment variable, sending a
`User-Agent: joemirza-site/1.0` header, and filtering the sentinel `"."` to numeric
floats. This access pattern SHALL be provided by the shared `scripts/fred_utils.py`
module so all FRED-consuming fetchers share one implementation. The shared module SHALL
retry rate-limited (`HTTP 429`) and transient server/network errors with bounded
exponential backoff before giving up, so a single rate-limit response does not abort a
multi-series run. A missing key SHALL cause scripts whose primary source is FRED to exit
with an error; scripts for which FRED is a secondary/optional source (e.g. the S&P 500
P/E price extension) MAY instead degrade gracefully without exiting.

#### Scenario: Missing FRED key for a FRED-primary fetcher

- **WHEN** `fetch_treasury.py`, `fetch_yield_curve.py`, `fetch_spreads.py`, or
  `fetch_usrec.py` runs with no `FRED_API_KEY` set
- **THEN** the script prints an error to stderr and exits non-zero

#### Scenario: Rate-limited request is retried

- **WHEN** FRED returns `HTTP 429` (or a transient 5xx/network error) for a series request
- **THEN** `fred_utils` waits with exponential backoff and retries up to a bounded number
  of attempts before treating it as a failure, rather than aborting the run on the first 429

#### Scenario: Shared module is the single FRED access path

- **WHEN** a fetcher needs a FRED series
- **THEN** it obtains it through `fred_utils` rather than reimplementing the URL,
  headers, or `"."` filtering inline

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
