## Why

S1 of the cross-session plan (`~/Obsidian/Investing/Finance and Economic Data
Website/Session Plan.md`) calls for a correctness test suite so that future workflow
agents (S7, S9, S11b) have a done-check that isn't "the agent grading its own work."
Right now nothing verifies a fetcher's output against an independent source, so a
silent drift — a units mismatch, a stale forward-fill, a broken "." sentinel — would
only surface if someone happened to eyeball the chart. S0 already found one such
drift by hand: `sp500_pe.json`'s header `last_ttm_earnings` (222.53) disagrees with
the earnings every recent observation actually uses (234.06).

## What Changes

- New `tests/` (pytest): `test_data_integrity.py` (dates unique/monotone, no FRED
  `"."` sentinel became 0, P/E internal price/earnings/pe arithmetic, the header/
  earnings mismatch as an `xfail`), `test_fred_utils.py` (mocked unit tests on the
  shared FRED helper — no network), `test_spreads.py` (sampled dates vs FRED's own
  precomputed `T10Y2Y`/`T10Y3M`), `test_yield_curve.py` (three fixed dates vs a
  direct `DGS*` pull per tenor), `test_sp500_pe.py` (Shiller-only era vs a fresh
  pull of Shiller's own P/E columns), `test_staleness.py` (each series' last
  observation within an expected publication lag).
- `pytest.ini` registers a `network` marker; network-dependent tests skip
  automatically when unreachable or `FRED_API_KEY` is unset, so the suite runs
  clean in any environment.
- `requirements-test.txt` (currently just `pytest`).
- A `pytest` step added to `.github/workflows/update-data.yml`, right after the
  day's fetch and before the site is copied/deployed — with `STALENESS_SOURCE=local`
  so it checks the data the workflow just fetched, not yesterday's live copy.
- `CLAUDE.md`: new Correctness Tests section, `tests/` row in Key Files, a `pytest`
  line under Running Locally, changelog entry.

**Decision made here** (the open question S0 left for S1/S2): `test_staleness.py`
checks the *live* published data (`https://joemirza.com/data/*.json`) by default,
not the locally committed `data/*.json`, because the committed copy is known to lag
what's live (the workflow never commits fetched data back to `main`). A
`STALENESS_SOURCE=local` env var switches it to the local copy — used only by CI,
right after that day's fetch, when local `data/` is briefly the freshest copy that
exists. This does not resolve the bigger architecture question (should the workflow
commit data back to `main`?) — that's left for a later session — it only makes the
staleness check meaningful today without depending on that decision.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
<!-- None — no spec describes a test suite's own behavior; this change adds
verification tooling around existing fetch behavior, it doesn't change what any
fetcher does (except surfacing, not fixing, the known P/E header bug). -->

## Impact

- **Affected**: new `tests/`, `pytest.ini`, `requirements-test.txt`;
  `.github/workflows/update-data.yml` (new step); `CLAUDE.md` (edited).
- **Not affected**: no fetch script's output logic changes. The `sp500_pe.json`
  header/earnings mismatch is documented and covered by an `xfail` test, not fixed —
  fixing it is a `fetch_sp500_pe.py` code change, out of scope here.
- **Rollback**: remove `tests/`, `pytest.ini`, `requirements-test.txt`, the workflow
  step, and the CLAUDE.md additions; nothing else depends on any of it.
