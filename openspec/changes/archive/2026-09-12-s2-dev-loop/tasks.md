## Tasks

- [x] `scripts/staleness.py` — extract `SERIES` table and `_business_days_between`
      from `tests/test_staleness.py` into an importable module both the test and
      `dev.sh` use. Add a `check(source)` helper returning per-series
      `(filename, last_date, lag_days, max_lag_days, stale: bool)` results.
- [x] `tests/test_staleness.py` — import from `scripts/staleness.py` instead of
      defining the table/function inline; confirm `pytest -v` still passes/skips/
      xfails identically to the S1 baseline. Verified: 18 passed, 5 skipped,
      1 xfailed (network unavailable in this sandbox, same as S1).
- [x] `scripts/dev.sh` — copy `data/*.json` → `site/data/`, run
      `scripts/staleness.py` in local mode and print a warning line per stale
      series (not a failure — dev iteration should still work on stale data, just
      not pretend it's current), then `python3 -m http.server` from `site/`.
      Takes an optional port arg (default 8888).
- [x] Verify `scripts/dev.sh` runs end-to-end with `FRED_API_KEY` unset and no
      network: staleness warnings printed for all five known-stale series, site
      loaded, all four tabs render with the local committed data. (Port 8888 was
      occupied by an unrelated process in this sandbox — verified on 8901 instead;
      the script itself has no dependency on a specific port.)
- [x] CLAUDE.md — add "Local Iteration Loop" section (edit → reload → Chrome
      screenshot with Claude → push), update Running Locally to point at
      `scripts/dev.sh` instead of the manual fetch/copy/serve steps, add Key Files
      rows and a changelog entry.
- [x] Chrome screenshot check: loaded `http://localhost:8901`, confirmed 10Y
      Treasury and S&P 500 P/E tabs render (tab-switch via ref click, since a
      coordinate click just missed the target once), no console errors captured.
