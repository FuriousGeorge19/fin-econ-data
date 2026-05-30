# How joemirza.com Works — Complete Technical Explanation

This document explains every piece of the system end-to-end: how data is fetched, how the
site is built, how it deploys, how the daily automation works, and how DNS routes your
domain to the live site.

---



## Table of Contents

1. [Overview](#overview)
2. [The Data Pipeline](#the-data-pipeline)
3. [The Website](#the-website)
4. [GitHub Actions — Daily Automation](#github-actions--daily-automation)
5. [GitHub Pages — Hosting](#github-pages--hosting)
6. [DNS and Custom Domain](#dns-and-custom-domain)
7. [HTTPS / SSL Certificate](#https--ssl-certificate)
8. [What Happens When Someone Visits joemirza.com](#what-happens-when-someone-visits-joemiracom)
9. [What Happens Every Day at Midnight UTC](#what-happens-every-day-at-midnight-utc)
10. [Project File Structure](#project-file-structure)
11. [How to Add a New Data Series](#how-to-add-a-new-data-series)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The site is a **static website** — there is no server running, no database, no backend
application. The entire site is a single HTML file plus a JSON data file, served directly
by GitHub's free hosting service (GitHub Pages).

A **GitHub Actions workflow** runs on a schedule (daily on weekdays). It executes a Python
script that calls the FRED API to get the latest 10-Year Treasury rate data, saves it as
a JSON file, and then deploys the updated site to GitHub Pages.

The key insight: we separate **data fetching** (Python, runs in GitHub's cloud) from
**data display** (HTML/JavaScript, runs in the visitor's browser). The Python script runs
once a day and produces a static JSON file. The website reads that file and renders it.

---

## The Data Pipeline

### Source: FRED (Federal Reserve Economic Data)

FRED is a free public API maintained by the Federal Reserve Bank of St. Louis. It provides
thousands of economic data series. We use the **DGS10** series, which is the daily 10-Year
Treasury Constant Maturity Rate — essentially the yield on 10-year U.S. government bonds.

- FRED website: https://fred.stlouisfed.org/series/DGS10
- API docs: https://fred.stlouisfed.org/docs/api/fred/

### The Fetch Script: `scripts/fetch_treasury.py`

This is a standard Python script with **no external dependencies** (uses only the standard
library). Here's what it does step by step:

1. **Reads the FRED API key** from the `FRED_API_KEY` environment variable. The key is
   never hardcoded in the script — it's stored as a GitHub Actions secret and passed in
   at runtime.

2. **Constructs the API URL** requesting the DGS10 series observations. Key parameters:
   - `series_id=DGS10` — the specific data series
   - `file_type=json` — return JSON (FRED also supports XML)
   - `sort_order=desc` — newest first (so we can limit to ~10 years)
   - `limit=2520` — approximately 10 years of trading days (252 trading days/year × 10)

3. **Makes the HTTP request** using Python's built-in `urllib` (no `requests` library
   needed). Includes a `User-Agent` header as good API citizenship.

4. **Cleans the data**: FRED returns `"."` for dates with no data (weekends, holidays).
   The script filters these out and converts the remaining values from strings to floats.

5. **Sorts chronologically** (oldest to newest) — FRED returns newest-first, but charts
   need oldest-first.

6. **Writes a JSON file** to `data/dgs10.json` with this structure:
   ```json
   {
     "series_id": "DGS10",
     "title": "10-Year Treasury Constant Maturity Rate",
     "units": "Percent",
     "frequency": "Daily",
     "source": "Federal Reserve Bank of St. Louis (FRED)",
     "last_updated": "2026-03-05 08:14 UTC",
     "observations": [
       {"date": "2016-07-06", "value": 1.37},
       {"date": "2016-07-07", "value": 1.36},
       ...
     ]
   }
   ```

The metadata fields (`title`, `units`, `source`, etc.) are included so the frontend
doesn't need to hardcode them — useful when we add more series later.

---

## The Website

### `site/index.html`

The entire site is a single HTML file with embedded CSS and JavaScript. No build step,
no npm, no bundler. This is intentional — it keeps things simple and deployable as-is.

#### CSS / Styling

The site uses a dark theme with CSS custom properties (variables) defined in `:root`:
- `--bg`: Deep navy background (`#0f172a`)
- `--surface`: Card backgrounds (`#1e293b`)
- `--accent`: Cyan highlight color (`#38bdf8`)
- etc.

This makes it easy to tweak the entire color scheme by changing a few values. The layout
is responsive — it adjusts for mobile screens using a `@media` query at 640px.

#### Tab Navigation

The `<nav>` section has buttons for each data tab. Currently there's only "10Y Treasury",
but the JavaScript tab-switching logic is already wired up. Adding a new tab means:
1. Add a `<button>` in the `<nav>`
2. Add a corresponding content `<div>` in `<main>`
3. Update the click handler to show/hide tabs

#### Chart: Plotly.js

We use [Plotly.js](https://plotly.com/javascript/) loaded from a CDN. Plotly was chosen
because:
- **Interactive out of the box**: zoom, pan, hover tooltips, range selection
- **Built-in range selector buttons**: the 1M / 6M / 1Y / 5Y / All buttons are a Plotly
  feature, not custom code
- **Range slider**: the minimap at the bottom of the chart is also built-in
- **Dark theme support**: all colors are configurable
- **No build step needed**: just a `<script>` tag

The `renderChart()` function creates a Plotly trace from the JSON data and configures
the layout (colors, axes, range selectors). Key settings:
- `paper_bgcolor` and `plot_bgcolor` set to `'transparent'` so the card background shows
- `rangeslider` enabled for the x-axis minimap
- `rangeselector` with preset time range buttons
- `hovertemplate` for clean tooltips showing date and rate

#### Summary Stats

The `renderStats()` function computes:
- **Latest**: most recent observation value
- **1-Year High/Low**: max/min over the last ~252 trading days
- **1-Year Change**: latest value minus value from ~252 trading days ago

The change is color-coded: red for increases (rates going up = bonds losing value) and
green for decreases.

#### Data Table

The `renderTable()` function shows the 30 most recent observations in reverse
chronological order (newest first). Each row shows the date, rate, and daily change
from the previous observation. Changes are color-coded the same way as the stats.

#### Data Loading

The `loadData()` function fetches `data/dgs10.json` relative to the page URL. This works
both locally (`http://localhost:8888/data/dgs10.json`) and in production
(`https://joemirza.com/data/dgs10.json`). If the fetch fails, an error message is shown
in place of the chart.

---

## GitHub Actions — Daily Automation

### `.github/workflows/update-data.yml`

GitHub Actions is a free CI/CD service built into GitHub. You define workflows as YAML
files in `.github/workflows/`. Our workflow does two things: fetches fresh data and
deploys the site.

#### Triggers

```yaml
on:
  schedule:
    - cron: '0 0 * * 2-6'  # Midnight UTC (7 PM ET), Tuesday–Saturday
  workflow_dispatch:         # Manual trigger button in GitHub UI
```

- **`schedule`**: Runs automatically on a cron schedule. `0 0 * * 2-6` means "at 00:00
  UTC on days 2 (Tuesday) through 6 (Saturday)". This covers Monday–Friday market days
  (Tuesday 00:00 UTC = Monday 7 PM ET, after markets close).
- **`workflow_dispatch`**: Adds a "Run workflow" button in the GitHub Actions UI so you
  can trigger it manually anytime.

**Important caveat**: GitHub Actions cron is not precise. Jobs can be delayed by 5–60
minutes. For daily financial data this doesn't matter — the data is the same whether
we fetch it at midnight or 12:45 AM.

#### Permissions

```yaml
permissions:
  contents: write
```

The workflow needs write access to push to the `gh-pages` branch.

#### Job Steps

1. **`actions/checkout@v4`**: Checks out the repository code so the Python script and
   site files are available.

2. **`actions/setup-python@v5`**: Installs Python 3.12 on the GitHub runner. Our script
   uses only the standard library, so no `pip install` step is needed.

3. **Fetch latest data from FRED**: Runs the Python script with the `FRED_API_KEY`
   environment variable pulled from GitHub Secrets (encrypted, never visible in logs).

4. **Copy data to site directory**: Copies `data/dgs10.json` to `site/data/dgs10.json`
   so it's included in the deployed site.

5. **Deploy to GitHub Pages**: Uses the `peaceiris/actions-gh-pages@v4` action, which:
   - Takes the contents of `./site`
   - Force-pushes them to a branch called `gh-pages`
   - Includes a `CNAME` file with `joemirza.com` (tells GitHub Pages the custom domain)
   - GitHub Pages then serves the contents of `gh-pages` as the website

### GitHub Secrets

The FRED API key is stored as a secret in the repository settings:
- Go to: GitHub repo → Settings → Secrets and variables → Actions
- Secret name: `FRED_API_KEY`
- This is the only secret needed. The `GITHUB_TOKEN` used for deploying is provided
  automatically by GitHub Actions.

---

## GitHub Pages — Hosting

GitHub Pages is a free static site hosting service. It serves files from a specific branch
of your repository as a website.

### How It's Configured

- **Source branch**: `gh-pages` (created and updated automatically by the deploy action)
- **Source path**: `/` (root of the branch)
- **Custom domain**: `joemirza.com` (set via the CNAME file in the deploy)

The `gh-pages` branch is completely managed by the deploy action — you should never edit
it directly. It contains only the built/deployable files:
- `index.html`
- `data/dgs10.json`
- `CNAME`
- `.nojekyll` (tells GitHub not to process files through Jekyll)

Your working code lives on the `main` branch. The `gh-pages` branch is just a deployment
artifact.

---

## DNS and Custom Domain

DNS (Domain Name System) translates human-readable domain names into IP addresses that
computers use to find servers.

### The Chain: Browser → DNS → GitHub → Your Site

1. Someone types `joemirza.com` in their browser
2. Their computer asks DNS "what IP address is joemirza.com?"
3. DNS returns one of the four GitHub Pages IP addresses (configured in Porkbun)
4. The browser connects to that GitHub server
5. GitHub looks at the `Host: joemirza.com` header in the request
6. GitHub finds your repository because it has a CNAME file matching `joemirza.com`
7. GitHub serves `index.html` from your `gh-pages` branch

### DNS Records (Configured in Porkbun)

| Type | Host | Value | Purpose |
|------|------|-------|---------|
| A | *(root)* | 185.199.108.153 | Points joemirza.com to GitHub |
| A | *(root)* | 185.199.109.153 | Redundancy — GitHub has 4 servers |
| A | *(root)* | 185.199.110.153 | Redundancy |
| A | *(root)* | 185.199.111.153 | Redundancy |
| CNAME | www | FuriousGeorge19.github.io | Points www.joemirza.com to GitHub |

**A records** map a domain directly to an IP address. We have four for redundancy — if
one GitHub server is down, browsers will try the others.

**CNAME record** maps `www.joemirza.com` to `FuriousGeorge19.github.io`, which GitHub
then resolves to the same site. This ensures both `joemirza.com` and `www.joemirza.com`
work.

---

## HTTPS / SSL Certificate

GitHub Pages automatically provisions a free SSL/TLS certificate from Let's Encrypt for
custom domains. This enables `https://joemirza.com`.

The certificate was in "pending" state right after DNS was configured (GitHub needs to
verify it can reach the domain before issuing a cert). It typically takes 5–15 minutes.

Once issued, "Enforce HTTPS" can be enabled in the repo's Settings → Pages section. This
redirects all `http://` requests to `https://`.

---

## What Happens When Someone Visits joemirza.com

Here's the complete sequence:

1. **DNS resolution**: Browser resolves `joemirza.com` → `185.199.108.153` (or one of
   the other three IPs)
2. **TLS handshake**: Browser establishes an HTTPS connection using GitHub's certificate
3. **HTTP request**: Browser sends `GET / HTTP/2` with `Host: joemirza.com`
4. **GitHub routing**: GitHub matches the Host header to the CNAME in your `gh-pages`
   branch and serves `index.html`
5. **HTML parsing**: Browser receives the HTML and starts parsing it
6. **CSS rendering**: The embedded `<style>` block renders the dark theme layout
7. **Plotly.js load**: Browser fetches `plotly-2.35.0.min.js` from Plotly's CDN (~3.5 MB)
8. **Data fetch**: The `loadData()` JavaScript function fetches `data/dgs10.json` from
   your site (~150 KB)
9. **Chart rendering**: Plotly creates the interactive SVG chart in the browser
10. **Stats & table**: JavaScript computes summary stats and populates the HTML table

Total load time is typically 1–2 seconds, dominated by the Plotly.js library download
(which gets cached after the first visit).

---

## What Happens Every Day at Midnight UTC

1. **GitHub Actions scheduler** wakes up and sees the cron trigger matches
2. A **fresh Ubuntu virtual machine** (called a "runner") is provisioned in GitHub's cloud
3. The runner **checks out** the latest code from the `main` branch
4. Python 3.12 is **installed** on the runner
5. The **fetch script** runs:
   - Reads `FRED_API_KEY` from the encrypted GitHub secret
   - Makes an HTTPS request to `api.stlouisfed.org`
   - Receives ~2500 observations as JSON
   - Cleans the data (removes missing values, converts types)
   - Writes `data/dgs10.json`
6. The **copy step** puts the JSON file into `site/data/`
7. The **deploy action** takes the entire `site/` directory and force-pushes it to the
   `gh-pages` branch, including the CNAME file
8. GitHub Pages detects the new commit on `gh-pages` and **rebuilds the site** (takes
   ~30 seconds)
9. The runner is **destroyed** — nothing persists between runs
10. The site at `joemirza.com` now shows the updated data

If the FRED API is down or returns an error, the Python script exits with a non-zero
status code, the workflow step fails, and the deploy step is skipped — so the site
continues serving the last successful data. You'll see a red X on the workflow run in
the GitHub Actions tab.

---

## Project File Structure

```
fin-econ-data/
├── .github/
│   └── workflows/
│       └── update-data.yml      # GitHub Actions: daily fetch + deploy
├── data/
│   └── dgs10.json               # Raw data from FRED (~2400 observations)
├── scripts/
│   └── fetch_treasury.py        # Python script to fetch DGS10 from FRED
├── site/
│   ├── data/
│   │   └── dgs10.json           # Copy of data for the live site
│   └── index.html               # The entire website (HTML + CSS + JS)
├── .gitignore                   # Ignores __pycache__, .env
├── CLAUDE.md                    # Context file for Claude AI sessions
└── HOW-IT-WORKS.md              # This file
```

**Why are there two copies of `dgs10.json`?**

- `data/dgs10.json` is the "source of truth" — written by the Python script
- `site/data/dgs10.json` is the copy that gets deployed to GitHub Pages

The deploy action only publishes the `site/` directory. We keep the original in `data/`
so scripts can read/write there without worrying about the site structure. The workflow
copies it over before deploying.

---

## How to Add a New Data Series

This architecture was designed to make adding new series straightforward:

### 1. Create a New Fetch Script

Copy `scripts/fetch_treasury.py` as a starting point. For example, for the Fama-French
3-factor data from Kenneth French's website:

```
scripts/fetch_fama_french.py
```

The script should:
- Fetch data from the source (API call, CSV download, etc.)
- Clean and normalize it
- Write a JSON file to `data/<series_name>.json` with the same structure (metadata +
  observations array)

### 2. Update the GitHub Actions Workflow

Add the new fetch command and copy step to `.github/workflows/update-data.yml`:

```yaml
- name: Fetch Fama-French factors
  run: python scripts/fetch_fama_french.py

- name: Copy data to site directory
  run: |
    mkdir -p site/data
    cp data/dgs10.json site/data/
    cp data/fama_french.json site/data/    # ← add this
```

### 3. Add a Tab to the Website

In `site/index.html`:
1. Add a new `<button>` in the `<nav>` section
2. Add a new content `<div>` for the tab
3. Add a `loadData()` variant that fetches the new JSON file
4. Add chart/table rendering functions for the new data

### 4. Test Locally

```bash
# Fetch both datasets
FRED_API_KEY=your_key python3 scripts/fetch_treasury.py
python3 scripts/fetch_fama_french.py

# Copy to site
cp data/*.json site/data/

# Preview
cd site && python3 -m http.server 8888
```

---

## Troubleshooting

### The site shows old data

- Check the GitHub Actions tab: did the latest workflow run succeed?
- If it failed, click into the run to see which step failed and the error message
- If the FRED API was temporarily down, just re-run the workflow manually (Actions tab →
  "Run workflow" button)

### The site is completely down

- Check if GitHub Pages is having an outage: https://www.githubstatus.com/
- Check DNS: run `dig joemirza.com` and verify it returns GitHub's IPs
- Check the repo Settings → Pages to make sure it's still configured

### I want to force a data refresh right now

Go to the GitHub repo → Actions tab → "Update Data" workflow → "Run workflow" button.
Or from the command line:

```bash
cd "/path/to/fin-econ-data"
gh workflow run update-data.yml
gh run watch  # watch it complete
```

### I changed the site locally but it's not updating online

Local changes need to be committed and pushed to `main`. But note: the site is deployed
from `gh-pages`, not `main`. After pushing to `main`, you need to either:
- Wait for the next scheduled workflow run, or
- Trigger the workflow manually (`gh workflow run update-data.yml`)

The workflow will check out `main`, run the scripts, and deploy to `gh-pages`.

### DNS isn't resolving / site shows Porkbun parking page

- Verify A records in Porkbun point to GitHub's four IPs
- Make sure the old ALIAS and wildcard CNAME records pointing to Porkbun were deleted
- DNS propagation can take up to 48 hours (though usually minutes with Porkbun)
- Test with: `dig +short joemirza.com A`
