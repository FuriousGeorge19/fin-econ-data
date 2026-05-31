## Why

The daily workflow's S&P 500 P/E step does not pass `FRED_API_KEY` to its environment,
so in CI the FRED price fetch warns and returns nothing — the published series silently
degrades to Shiller-only history with no post-Shiller monthly extension. This is the
known gap documented in `sp500-pe-series`. Wiring the key in (exactly as the Treasury
and yield-curve steps already do) closes it so the automated build publishes the full,
current P/E series.

## What Changes

- Add an `env: FRED_API_KEY: ${{ secrets.FRED_API_KEY }}` block to the "Fetch S&P 500
  P/E ratio" step in `.github/workflows/update-data.yml` (one step, matching the other
  two FRED steps).
- Update `sp500-pe-series`: the "Daily refresh produces Shiller-only P/E in CI"
  requirement (which documents the gap) is replaced by one stating the daily refresh
  produces the full post-Shiller extension in CI.
- Update `daily-automation`: the "FRED key supplied via secret" requirement broadens to
  include the P/E step among the steps that receive the key.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `sp500-pe-series`: the CI-refresh requirement flips from documenting the Shiller-only
  degradation to requiring the full FRED-extended series in CI.
- `daily-automation`: the FRED-secret requirement now covers the Treasury, S&P 500 P/E,
  and yield-curve steps.

## Impact

- **Affected**: `.github/workflows/update-data.yml` (one step gains an `env` block);
  spec files for `sp500-pe-series` and `daily-automation`.
- **Not affected**: `scripts/fetch_sp500_pe.py` already reads `FRED_API_KEY` and degrades
  gracefully — no script change needed. No data schema, site, or other series change.
- **Rollback**: revert the one-step `env` addition in `update-data.yml` (single commit
  revert). The script's graceful degradation means a bad value or missing secret simply
  returns to the current Shiller-only behavior rather than failing the build; no data
  corruption risk. The next scheduled run (or a manual `workflow_dispatch`) re-publishes.
