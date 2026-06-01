## Why

The site at joemirza.com is a working production system (three live data series,
daily automated refresh, custom domain) but has **zero specs** capturing how it
behaves. Future changes have nothing to diff against, and the conventions that make
the architecture scale (the data-flow contract, timeline rules, estimated-vs-confirmed
handling) live only in code comments and CLAUDE.md. This change codifies the current
running system as the OpenSpec baseline so every subsequent change is a delta against
documented behavior.

This is documentation-only: it describes what already exists. No code, data, or
workflow changes.

## What Changes

- Create the initial `openspec/specs/` tree by capturing the existing system as six
  capability specs (the data pipeline, three data series, the dashboard, the daily
  automation).
- Each spec records observed behavior, not aspirations — the requirements describe
  what the code does today.
- No production code, data files, fetch scripts, `site/index.html`, or the GitHub
  Actions workflow are modified.
- Surface (but do not fix) one behavioral note: the `fetch_sp500_pe.py` step in the
  workflow does not pass `FRED_API_KEY`, so the price-extension path degrades to
  Shiller-only in CI. Captured as a known gap in the relevant spec, fixed in a later change.

## Capabilities

### New Capabilities
- `data-pipeline`: The shared fetch → `data/<name>.json` → `site/data/<name>.json`
  contract, FRED access pattern, JSON output schema conventions, missing-value
  handling, and the daily-timeline / 1st-of-month rules.
- `treasury-10y-series`: DGS10 fetcher and the 10-Year Treasury chart + recent-observations table.
- `sp500-pe-series`: Trailing P/E built by stitching Shiller history, S&P Global
  earnings overrides, and FRED prices, with confirmed-vs-estimated marking.
- `yield-curve-series`: All 11 Treasury tenors fetched daily, with the snapshot chart,
  historical overlays, date picker, and current-yields table.
- `dashboard-site`: The single-file static dashboard — tabbed nav, dark theme, Plotly
  charts, no build step.
- `daily-automation`: The GitHub Actions weekday cron that refreshes data and deploys
  `site/` to GitHub Pages on the custom domain.

### Modified Capabilities
<!-- None — no specs exist yet; this change establishes the baseline. -->

## Impact

- **Affected**: `openspec/specs/` (new spec files only).
- **Not affected**: all production code, data, `site/index.html`, fetch scripts, and
  `.github/workflows/update-data.yml` are read-only references for this change.
- **Rollback**: delete the created spec files; no runtime impact since nothing executable changes.
