# daily-automation Specification

## Purpose

The GitHub Actions weekday cron (`.github/workflows/update-data.yml`) that refreshes
all data series, copies the resulting JSON into `site/data/`, and deploys the static
site to GitHub Pages under the custom domain `joemirza.com`.
## Requirements
### Requirement: Scheduled weekday data refresh

A GitHub Actions workflow (`.github/workflows/update-data.yml`) SHALL run on a cron
schedule of `15 23 * * 1-5` (23:15 UTC Mon–Fri, i.e. 19:15 EDT / 18:15 EST: after
FRED's ~16:15 ET H.15 update, hours before US Eastern midnight, and off the congested
top-of-hour slot) and SHALL also be manually triggerable via `workflow_dispatch`. On
each run it SHALL install pandas/xlrd/openpyxl and execute every descriptor's fetch
script through `scripts/fetch_all.py`.

#### Scenario: Scheduled run refreshes data

- **WHEN** the weekday cron fires (or a maintainer triggers the workflow manually)
- **THEN** the job checks out the repo, sets up Python 3.12, installs dependencies, and
  runs `scripts/fetch_all.py`, which runs the fetch script of every `series/*.json`
  (`fetch_treasury.py`, `fetch_sp500_pe.py`, `fetch_yield_curve.py`, `fetch_usrec.py`,
  `fetch_spreads.py` today)

### Requirement: Copy data into the site and deploy to Pages

After fetching and the gating tests, the workflow SHALL run `scripts/build_site.py`,
which copies each site data file (the list derived from `series/*.json`) into
`site/data/` and generates the site's pages, and SHALL then deploy the `site/`
directory to GitHub Pages via `peaceiris/actions-gh-pages`, setting the custom domain
through a `cname` of `joemirza.com`. The deploy SHALL run whenever the gating
correctness tests pass, regardless of fetch outcomes; redeploying unchanged data is
acceptable.

#### Scenario: Deploy after refresh

- **WHEN** the gating correctness tests pass
- **THEN** the workflow runs the generator, which copies every `data/<id>.json` named by
  `series/*.json` into `site/data/` and writes the pages, and publishes `site/` to the
  Pages branch with CNAME `joemirza.com`

### Requirement: FRED key supplied via secret

The workflow SHALL provide the FRED API key to the fetch runner step via the
`FRED_API_KEY` GitHub Actions secret through a step-level `env` block, so every fetch
script the runner starts inherits it; the Pages deploy SHALL use the automatic
`GITHUB_TOKEN`.

#### Scenario: Secret injected into fetch scripts

- **WHEN** the `scripts/fetch_all.py` step runs in CI
- **THEN** each fetch script it starts receives `FRED_API_KEY` from
  `secrets.FRED_API_KEY` in its environment

### Requirement: Deploy what succeeded

Before running any fetcher, the workflow SHALL fetch the `gh-pages` branch and restore
each site data file **by name** (never the `data/` directory) from it into `data/`, so
that a series whose fetch fails today carries forward the file that is live, not
`main`'s fixture. A file absent from `gh-pages` keeps `main`'s copy; a seed failure
SHALL emit a `::warning::` and continue. `scripts/fetch_all.py` SHALL run each fetch
script as a non-fatal subprocess and record each outcome in `data/fetch_status.json`,
always exiting 0. The correctness tests SHALL still gate the deploy with the
`staleness`-marked test deselected, so a wrong number blocks and a missing number does
not.

#### Scenario: One fetch fails

- **WHEN** `fetch_sp500_pe.py` exits non-zero and the other four fetchers succeed
- **THEN** `data/sp500_pe.json` is the copy restored from `gh-pages`,
  `fetch_status.json` marks `sp500_pe` not ok, the gating tests run, and the deploy
  publishes four fresh files and one carried-forward file

#### Scenario: Seed preserves fetch inputs

- **WHEN** the seed step runs
- **THEN** `data/earnings_overrides.json` (not present on `gh-pages`) is untouched

#### Scenario: New series first run

- **WHEN** a descriptor and fetcher for a series with no file on `gh-pages` are added
- **THEN** the seed step skips that file with a warning, the runner picks the fetcher up
  with no workflow edit, and the run proceeds

### Requirement: Staleness reported and failures surfaced after deploy

The staleness check SHALL run as its own step with `continue-on-error: true`, writing a
per-series table (last observation, `due_by`, overdue or not) to
`$GITHUB_STEP_SUMMARY`; it SHALL NOT block the deploy. A final step with `if:
always()` SHALL run after the deploy, read `data/fetch_status.json`, emit a
`::warning::` annotation for each failed fetch and each overdue series, and exit
non-zero if any fetch failed, so the job is marked failed (and GitHub notifies) after
the data has already shipped.

#### Scenario: Fetch failure still notifies

- **WHEN** any entry in `fetch_status.json` is not ok
- **THEN** the deploy has already completed and the job's final status is failed

#### Scenario: Overdue series does not fail the job

- **WHEN** every fetch succeeds but one series is overdue by the data-freshness rule
- **THEN** the job summary lists it, a warning annotation is emitted, and the job
  succeeds

