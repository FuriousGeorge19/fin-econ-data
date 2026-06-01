## MODIFIED Requirements

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
