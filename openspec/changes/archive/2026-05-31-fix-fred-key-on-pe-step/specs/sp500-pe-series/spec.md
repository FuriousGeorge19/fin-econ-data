## ADDED Requirements

### Requirement: Daily refresh produces full P/E in CI

The daily GitHub Actions workflow SHALL run `scripts/fetch_sp500_pe.py` with
`FRED_API_KEY` present in the step's environment so that the FRED-based price
extension runs in CI. The published `data/sp500_pe.json` SHALL therefore include
the post-Shiller monthly extension (FRED-priced months with overrides-based and
forward-filled TTM earnings), matching what a local run with the key produces.

#### Scenario: P/E refresh in CI with the key wired in

- **WHEN** the daily workflow runs the S&P 500 P/E step
- **THEN** the FRED SP500 price fetch succeeds and the published `sp500_pe.json`
  contains observations through the current month, including post-Shiller months
  marked `estimated=true` where earnings are forward-filled

#### Scenario: Secret absent falls back safely

- **WHEN** the S&P 500 P/E step runs but `FRED_API_KEY` is missing or invalid
- **THEN** the script warns to stderr, returns no FRED prices, and still completes
  with Shiller-only output rather than failing the build

## REMOVED Requirements

### Requirement: Daily refresh produces Shiller-only P/E in CI

**Reason**: The gap this requirement documented is now closed — the P/E workflow
step passes `FRED_API_KEY`, so CI no longer degrades to Shiller-only output.
**Migration**: Superseded by "Daily refresh produces full P/E in CI" above. No data
migration needed; the next scheduled run (or a manual `workflow_dispatch`) republishes
`sp500_pe.json` with the post-Shiller extension included.
