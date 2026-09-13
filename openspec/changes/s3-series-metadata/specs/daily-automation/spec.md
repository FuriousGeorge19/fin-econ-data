## MODIFIED Requirements

### Requirement: Scheduled weekday data refresh

A GitHub Actions workflow (`.github/workflows/update-data.yml`) SHALL run on a cron
schedule of `15 23 * * 1-5` (23:15 UTC Mon–Fri, i.e. 19:15 EDT / 18:15 EST: after
FRED's ~16:15 ET H.15 update, hours before US Eastern midnight, and off the congested
top-of-hour slot) and SHALL also be manually triggerable via `workflow_dispatch`. On
each run it SHALL install pandas/xlrd/openpyxl and execute all fetch scripts.

#### Scenario: Scheduled run refreshes data

- **WHEN** the weekday cron fires (or a maintainer triggers the workflow manually)
- **THEN** the job checks out the repo, sets up Python 3.12, installs dependencies, and
  runs `fetch_treasury.py`, `fetch_sp500_pe.py`, `fetch_yield_curve.py`,
  `fetch_usrec.py`, and `fetch_spreads.py`

### Requirement: Copy data into the site and deploy to Pages

After fetching, the workflow SHALL copy each site data file (the list derived from
`series/*.json`) into `site/data/` and deploy the `site/` directory to GitHub Pages via
`peaceiris/actions-gh-pages`, setting the custom domain through a `cname` of
`joemirza.com`. The deploy SHALL run whenever the gating correctness tests pass,
regardless of fetch-step outcomes; redeploying unchanged data is acceptable.

#### Scenario: Deploy after refresh

- **WHEN** the gating correctness tests pass
- **THEN** the workflow copies every `data/<id>.json` named by `series/*.json` into
  `site/data/` and publishes `site/` to the Pages branch with CNAME `joemirza.com`

## ADDED Requirements

### Requirement: Deploy what succeeded

Before running any fetcher, the workflow SHALL fetch the `gh-pages` branch and restore
each site data file **by name** (never the `data/` directory) from it into `data/`, so
that a series whose fetch fails today carries forward the file that is live, not
`main`'s fixture. A file absent from `gh-pages` keeps `main`'s copy; a seed failure
SHALL emit a `::warning::` and continue. Each fetch step SHALL have an `id` and
`continue-on-error: true`. The correctness tests SHALL still gate the deploy with the
`staleness`-marked test deselected, so a wrong number blocks and a missing number does
not.

#### Scenario: One fetch fails

- **WHEN** `fetch_sp500_pe.py` exits non-zero and the other four fetchers succeed
- **THEN** `data/sp500_pe.json` is the copy restored from `gh-pages`, the gating tests
  run, and the deploy publishes four fresh files and one carried-forward file

#### Scenario: Seed preserves fetch inputs

- **WHEN** the seed step runs
- **THEN** `data/earnings_overrides.json` (not present on `gh-pages`) is untouched

#### Scenario: New series first run

- **WHEN** a descriptor and fetcher for a series with no file on `gh-pages` are added
- **THEN** the seed step skips that file with a warning and the run proceeds on
  `main`'s copy

### Requirement: Staleness reported and failures surfaced after deploy

The staleness check SHALL run as its own step with `continue-on-error: true`, writing a
per-series table (last observation, `due_by`, overdue or not) to
`$GITHUB_STEP_SUMMARY`; it SHALL NOT block the deploy. A final step with `if:
always()` SHALL run after the deploy, emit a `::warning::` annotation for each failed
fetch step and each overdue series, and exit non-zero if any fetch step failed, so the
job is marked failed (and GitHub notifies) after the data has already shipped.

#### Scenario: Fetch failure still notifies

- **WHEN** any fetch step's outcome is `failure`
- **THEN** the deploy has already completed and the job's final status is failed

#### Scenario: Overdue series does not fail the job

- **WHEN** every fetch succeeds but one series is overdue by the data-freshness rule
- **THEN** the job summary lists it, a warning annotation is emitted, and the job
  succeeds
