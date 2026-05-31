## MODIFIED Requirements

### Requirement: FRED key supplied via secret

The workflow SHALL provide the FRED API key to fetch steps via the `FRED_API_KEY`
GitHub Actions secret. The Treasury, S&P 500 P/E, and yield-curve steps SHALL each
receive it through a step-level `env` block; the Pages deploy SHALL use the automatic
`GITHUB_TOKEN`.

#### Scenario: Secret injected into fetch steps

- **WHEN** the Treasury, S&P 500 P/E, and yield-curve fetch steps run in CI
- **THEN** each receives `FRED_API_KEY` from `secrets.FRED_API_KEY` in its environment
