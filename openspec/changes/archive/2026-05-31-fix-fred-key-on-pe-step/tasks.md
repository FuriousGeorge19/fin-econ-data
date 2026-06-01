## 1. Wire the FRED key into the P/E step

- [x] 1.1 In `.github/workflows/update-data.yml`, add an `env:` block with `FRED_API_KEY: ${{ secrets.FRED_API_KEY }}` to the "Fetch S&P 500 P/E ratio from Shiller/Yale" step, matching the Treasury and yield-curve steps
- [x] 1.2 Confirm via `git diff` that only that one step changed and the YAML indentation matches the sibling steps

## 2. Verify behavior

- [ ] 2.1 Sanity-check locally: run `FRED_API_KEY=<key> python scripts/fetch_sp500_pe.py` and confirm the output includes post-Shiller months (this already works locally; confirms the script path the CI step now exercises) — **deferred to user**: requires the FRED secret (not available in this environment) and would overwrite `data/sp500_pe.json`
- [ ] 2.2 After merge, trigger the workflow via `workflow_dispatch` and confirm the run logs show the FRED SP500 fetch succeeding (not the "no price extension" warning) — **manual CI check (post-merge, user)**
- [ ] 2.3 Confirm the redeployed `site/data/sp500_pe.json` gains post-Shiller observations through the current month — **manual CI check (post-merge, user)**

## 3. Validate the change

- [x] 3.1 Run `openspec validate fix-fred-key-on-pe-step` (with Node 22 on PATH) and resolve any errors
