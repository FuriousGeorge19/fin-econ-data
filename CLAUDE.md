# fin-econ-data — Project Context for Claude

## What This Is

A public website at **joemirza.com** that displays economic and financial data with
interactive charts and tables. Currently a working POC with a single data series.
Built 2026-03-05.

## Current State

- **Live at**: http://joemirza.com (HTTPS certificate was pending as of initial deploy;
  check and enable "Enforce HTTPS" in repo Settings → Pages if not yet done)
- **GitHub repo**: https://github.com/FuriousGeorge19/fin-econ-data
- **Local path**: `~/Library/Mobile Documents/com~apple~CloudDocs/projects/fin-econ-data/`
- **Three data series active**:
  - 10-Year Treasury Constant Maturity Rate (DGS10) from FRED
  - S&P 500 Trailing P/E Ratio (1871–present, Shiller + S&P Global + FRED)
  - Treasury Yield Curve Snapshot (all 11 tenors, 1mo–30yr, from FRED)
- **Daily automation working**: GitHub Actions cron runs weekday evenings, fetches fresh
  data, and redeploys to GitHub Pages

## Architecture

```
scripts/           Python data fetchers (one per series)
data/              Raw JSON output from fetchers (committed to repo)
site/              Static site served by GitHub Pages
  index.html       Single-page app with Plotly.js charts
  data/            Copy of JSON data (deployed to gh-pages branch)
.github/workflows/ GitHub Actions for daily data refresh + deploy
```

- **No server / no backend** — entirely static, hosted free on GitHub Pages
- **Data flow**: Python script → JSON file → GitHub Actions commits to repo → deploys
  `site/` directory to `gh-pages` branch via `peaceiris/actions-gh-pages`
- **Frontend**: Vanilla HTML/CSS/JS with Plotly.js for interactive charts
- **Custom domain**: CNAME file in deploy sets `joemirza.com`; DNS A records point to
  GitHub Pages IPs (configured in Porkbun)

## Key Files

| File | Purpose |
|------|---------|
| `scripts/fetch_treasury.py` | Fetches DGS10 from FRED API, outputs `data/dgs10.json` |
| `scripts/fetch_sp500_pe.py` | Fetches S&P 500 P/E ratio (Shiller + overrides + FRED), outputs `data/sp500_pe.json` |
| `scripts/fetch_yield_curve.py` | Fetches all 11 Treasury tenors (DGS1MO–DGS30) from FRED, outputs `data/yield_curve.json` |
| `data/earnings_overrides.json` | **Manually maintained** — quarterly as-reported EPS from S&P Global (see below) |
| `site/index.html` | Full site — dark theme, three-tab Plotly dashboard |
| `.github/workflows/update-data.yml` | Daily cron + manual trigger, runs all fetches then deploys |
| `data/dgs10.json` | ~2400 daily observations, updated by the workflow |
| `data/sp500_pe.json` | ~1862 monthly observations (1871–present), updated by the workflow |
| `data/yield_curve.json` | ~6000 daily observations across 11 tenors (2002–present), updated by the workflow |
| `reference_resources/sp-500-eps-est.xlsx` | Source file for quarterly EPS (S&P Global, not auto-fetchable) |

## S&P 500 P/E — Quarterly Earnings Update (4x/year)

The `data/earnings_overrides.json` file must be manually updated each earnings season
(roughly Feb, May, Aug, Nov) when S&P Global publishes the latest quarterly scorecard.

**Steps:**
1. Download the new `sp-500-eps-est.xlsx` from S&P Global and replace `reference_resources/sp-500-eps-est.xlsx`
2. Run this snippet to regenerate `data/earnings_overrides.json`:

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/projects/fin-econ-data
python3 - <<'EOF'
import pandas as pd, json
from datetime import datetime

path = 'reference_resources/sp-500-eps-est.xlsx'
df = pd.read_excel(path, sheet_name='QUARTERLY DATA', header=None, engine='openpyxl')
df = df.iloc[6:, [0, 1, 2]].copy()
df.columns = ['quarter_end', 'operating_eps', 'as_reported_eps']
df['quarter_end'] = pd.to_datetime(df['quarter_end'], errors='coerce')
df['as_reported_eps'] = pd.to_numeric(df['as_reported_eps'], errors='coerce')
df = df[df['quarter_end'].notna() & df['as_reported_eps'].notna()].copy()
df = df.sort_values('quarter_end').reset_index(drop=True)
df['ttm_eps'] = df['as_reported_eps'].rolling(4).sum().round(2)
df = df[df['ttm_eps'].notna()].copy()

entries = []
for _, row in df.iterrows():
    qe = row['quarter_end']
    m = qe.month + 1; y = qe.year
    if m > 12: m, y = 1, y + 1
    entries.append({
        'quarter_end':    qe.strftime('%Y-%m-%d'),
        'effective_from': f'{y}-{m:02d}-01',
        'quarterly_eps':  round(float(row['as_reported_eps']), 2),
        'ttm_eps':        round(float(row['ttm_eps']), 2),
    })

out = {
    'description': 'S&P 500 quarterly and TTM as-reported EPS. Source: S&P Global sp-500-eps-est.xlsx.',
    'source': 'S&P Global / S&P Dow Jones Indices',
    'last_updated': datetime.now().strftime('%Y-%m-%d'),
    'entries': entries,
}
with open('data/earnings_overrides.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f"Wrote {len(entries)} entries, latest: {entries[-1]['quarter_end']}  TTM={entries[-1]['ttm_eps']}")
EOF
```

3. Commit and push — the next GitHub Actions run will pick up the new earnings.

## Secrets & Credentials

- **FRED API key** is stored as a GitHub Actions secret named `FRED_API_KEY`
  (key: `xxxxxxxxxxxxxx` — does not expire)
- The `GITHUB_TOKEN` used for Pages deploy is automatic (no setup needed)

## DNS Setup (Porkbun)

Domain `joemirza.com` has these records pointing to GitHub Pages:
- 4 × A records: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- 1 × CNAME: `www` → `FuriousGeorge19.github.io`
- MX and TXT records were left untouched (email/SPF)

## Planned Next Steps (User's Vision)

The user wants to grow this into a multi-series financial/economic data dashboard:
- **More data sources**: Kenneth French factors (Dartmouth), SEC EDGAR, potentially others
- **Tabs**: Each data source or category gets its own tab in the nav bar
- **Better visualizations**: More chart types, comparisons, derived metrics
- **More series from FRED**: Unemployment, CPI, yield curve, etc.

## Development Patterns

When adding a new data series:
1. Create a new Python script in `scripts/` (follow `fetch_treasury.py` pattern)
2. Output JSON to `data/<series>.json`
3. Add the fetch command to `.github/workflows/update-data.yml`
4. Add a new tab and chart/table section in `site/index.html`
5. Add a `cp data/<series>.json site/data/` line in the workflow

The architecture was chosen specifically to scale this way without rework.

## Tech Choices & Rationale

- **Plotly.js** (not matplotlib): Interactive browser charts, supports dropdowns/tabs natively
- **Static site** (not Streamlit): Full control over UI, free hosting, custom domain support,
  no server to maintain
- **GitHub Actions** (not a cron server): Free, reliable, no infrastructure to manage
- **Vanilla JS** (no React/framework): Keeps it simple for now; can migrate later if needed
- **No database**: JSON files are sufficient for this scale; easy to add SQLite or similar later

## Running Locally

```bash
# Fetch fresh data (requires pandas xlrd openpyxl installed)
FRED_API_KEY=xxxxxxxxxxxxxx python scripts/fetch_treasury.py
FRED_API_KEY=xxxxxxxxxxxxxx python scripts/fetch_sp500_pe.py

# Copy to site directory
cp data/dgs10.json site/data/
cp data/sp500_pe.json site/data/

# Serve locally
cd site && python3 -m http.server 8888
# Then open http://localhost:8888
```

## Changelog (recent work, newest first)

- **2026-04-01**: Added yield curve snapshot tab — fetches all 11 DGS tenors from FRED,
  interactive Plotly chart with categorical x-axis (evenly spaced tenors, Bloomberg-style),
  toggle overlays for 1w/1m/1y/5y ago, custom date picker, and yields table with period
  changes. New script `scripts/fetch_yield_curve.py`, workflow updated.
- **2026-03-05**: Added S&P 500 trailing P/E ratio tab — Shiller/Yale data back to 1871,
  S&P Global quarterly earnings overrides, FRED for recent price data. Estimated periods
  shown with dashed line. New script `scripts/fetch_sp500_pe.py`.
- **2026-03-05**: Initial build — 10Y Treasury rate dashboard with daily FRED updates,
  GitHub Actions automation, GitHub Pages deploy, custom domain setup.

## Model Recommendation

Sonnet is sufficient for most work on this project (adding series, UI changes, styling).
Use Opus only for complex architectural decisions or tricky debugging.
