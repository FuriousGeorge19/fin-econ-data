## MODIFIED Requirements

### Requirement: Fetch 10-Year Treasury rate

`scripts/fetch_treasury.py` SHALL fetch the DGS10 series (10-Year Treasury Constant
Maturity Rate) from FRED, requesting the most recent ~2520 daily observations
(approximately 10 years of trading days), and write `data/dgs10.json` under the
`series-metadata` header contract.

#### Scenario: Successful fetch

- **WHEN** `fetch_treasury.py` runs with a valid `FRED_API_KEY`
- **THEN** `data/dgs10.json` is written with `meta` from `series/dgs10.json` (input
  `series_id` `DGS10`, units `Percent`, cadence `daily`, source FRED), `as_of` with the
  last observation and `due_by`, and observations sorted oldest-first, each having a
  `date` and a numeric `value`

#### Scenario: Missing values dropped

- **WHEN** the DGS10 response contains `"."` entries (holidays/gaps)
- **THEN** those entries are excluded and only numeric observations appear in the output
