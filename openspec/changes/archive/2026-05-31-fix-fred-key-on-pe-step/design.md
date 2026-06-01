## Context

This is a one-line-class fix to `.github/workflows/update-data.yml`: the S&P 500 P/E
step is the only FRED-consuming step without an `env` block passing `FRED_API_KEY`. The
fetch script (`scripts/fetch_sp500_pe.py`) already reads the key and degrades gracefully
when it is absent, so the gap is purely in the workflow wiring. The change is small but
touches CI, so it gets a short design to record the one real decision and the verification approach.

## Goals / Non-Goals

**Goals:**
- The daily CI build publishes the full S&P 500 P/E series (Shiller history + FRED-priced
  post-Shiller extension), matching what a local run with the key produces.
- Keep the change isolated to the workflow step plus the two affected specs.

**Non-Goals:**
- No change to `fetch_sp500_pe.py` (it already handles the key correctly).
- Not adding new error handling or making a missing key fail the build — graceful
  degradation is the intended safety behavior and is kept.
- Not touching the Treasury or yield-curve steps, which already pass the key.

## Decisions

- **Mirror the existing pattern exactly.** Add the same `env:` block the Treasury and
  yield-curve steps use, rather than introducing a job-level env or a different mechanism.
  - *Alternative considered:* set `FRED_API_KEY` once at the job level so every step
    inherits it. Rejected — it would silently re-wire the Shiller step's behavior and
    diverge from the established per-step pattern; an explicit per-step `env` keeps each
    step's dependencies legible and matches the reviewed baseline.

- **Model the spec change as replace-not-edit for the P/E CI requirement.** The existing
  requirement is literally named for the degraded behavior ("Shiller-only P/E in CI"), so
  it is REMOVED (with reason/migration) and a new "full P/E in CI" requirement is ADDED,
  rather than MODIFIED under a now-false name. The `daily-automation` secret requirement
  keeps its name and is MODIFIED in place to add the P/E step.

## Risks / Trade-offs

- **Secret missing or wrong in CI** → The script already warns and returns no prices, so
  the build still succeeds and falls back to today's Shiller-only output; no failure or
  data corruption. Verification: after the change, a `workflow_dispatch` run's logs should
  show the FRED SP500 fetch succeeding and the published `sp500_pe.json` gaining
  post-Shiller months.
- **Behavior only observable in CI** → Locally the key is already passed, so the bug
  never reproduces on a dev machine. Verify via an actual Actions run, not a local run.
