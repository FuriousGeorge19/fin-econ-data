## Tasks

- [x] `tests/conftest.py` — fixtures loading each committed `data/*.json`, plus
      `scripts/` on `sys.path` so fetch scripts and `fred_utils` are importable.
- [x] `tests/test_data_integrity.py` — dates unique/monotone (dgs10, sp500_pe,
      yield_curve, spreads, usrec intervals non-overlapping); no `"."` sentinel
      became 0; yield values finite/in-range; P/E internal consistency
      (price/earnings ≈ pe, relative tolerance for the low-precision 19th-century
      earnings); the header/earnings mismatch as `xfail` with a documented reason.
- [x] `tests/test_fred_utils.py` — mocked unit tests: `"."` dropped not zeroed,
      oldest-first sort, missing-key required/not-required behavior.
- [x] `tests/test_spreads.py` — 10y-2y and 10y-3m vs FRED's own `T10Y2Y`/`T10Y3M`
      on three sampled dates. Verified passing with `FRED_API_KEY` set.
- [x] `tests/test_yield_curve.py` — three fixed dates (2015-06-15, 2018-01-02,
      2022-09-01), all 11 tenors, vs a direct per-tenor FRED pull. Verified passing.
- [x] `tests/test_sp500_pe.py` — Shiller-only era vs a fresh pull of Shiller's own
      P/E columns via `fetch_sp500_pe.parse_shiller`. Verified passing.
- [x] `tests/test_staleness.py` — business-day lag per series; live site by
      default, `STALENESS_SOURCE=local` override. Verified: fails correctly
      against local (stale since 2026-03/05) data; the live-site path skips
      gracefully when unreachable rather than erroring.
- [x] `pytest.ini` — `testpaths = tests`, registers the `network` marker.
- [x] `requirements-test.txt`.
- [x] Add the `pytest` step to `.github/workflows/update-data.yml`, after the
      fetch steps and before "Copy data to site directory", with
      `STALENESS_SOURCE=local` and `FRED_API_KEY` from secrets.
- [x] `CLAUDE.md`: Correctness Tests section, Key Files row, Running Locally
      command, changelog entry.
- [x] Full local run: `pytest -v` — 18 passed, 5 skipped (live-site unreachable
      from this sandbox — a network-egress artifact, not a test bug), 1 xfailed
      (the known P/E header bug, expected).
