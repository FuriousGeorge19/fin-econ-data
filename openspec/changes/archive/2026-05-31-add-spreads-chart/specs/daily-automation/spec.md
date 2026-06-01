## MODIFIED Requirements

### Requirement: Scheduled weekday data refresh

A GitHub Actions workflow (`.github/workflows/update-data.yml`) SHALL run on a cron
schedule of `0 0 * * 2-6` (midnight UTC Tue–Sat, i.e. after each US weekday market
close) and SHALL also be manually triggerable via `workflow_dispatch`. On each run it
SHALL install pandas/xlrd/openpyxl and execute all fetch scripts.

#### Scenario: Scheduled run refreshes data

- **WHEN** the weekday cron fires (or a maintainer triggers the workflow manually)
- **THEN** the job checks out the repo, sets up Python 3.12, installs dependencies, and
  runs `fetch_treasury.py`, `fetch_sp500_pe.py`, `fetch_yield_curve.py`,
  `fetch_usrec.py`, and `fetch_spreads.py`

### Requirement: Copy data into the site and deploy to Pages

After fetching, the workflow SHALL copy each `data/<name>.json` into `site/data/` and
deploy the `site/` directory to GitHub Pages via `peaceiris/actions-gh-pages`, setting
the custom domain through a `cname` of `joemirza.com`.

#### Scenario: Deploy after refresh

- **WHEN** the fetch steps complete successfully
- **THEN** the workflow copies `dgs10.json`, `sp500_pe.json`, `yield_curve.json`,
  `usrec.json`, and `spreads.json` into `site/data/` and publishes `site/` to the Pages
  branch with CNAME `joemirza.com`

### Requirement: FRED key supplied via secret

The workflow SHALL provide the FRED API key to fetch steps via the `FRED_API_KEY`
GitHub Actions secret. The Treasury, S&P 500 P/E, yield-curve, USREC, and spreads steps
SHALL each receive it through a step-level `env` block; the Pages deploy SHALL use the
automatic `GITHUB_TOKEN`.

#### Scenario: Secret injected into fetch steps

- **WHEN** the Treasury, S&P 500 P/E, yield-curve, USREC, and spreads fetch steps run in CI
- **THEN** each receives `FRED_API_KEY` from `secrets.FRED_API_KEY` in its environment
