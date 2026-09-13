## Why

S2 of the cross-session plan (`~/Obsidian/Investing/Finance and Economic Data
Website/Session Plan.md`) calls for a local iteration loop: right now, trying a UI
change means manually copying five `data/*.json` files into `site/data/` and
remembering the `python3 -m http.server` invocation — friction that discourages
testing changes in a browser before pushing. It should work with `FRED_API_KEY`
unset, since most UI iteration doesn't need fresh data, only what's already
committed.

The HANDOFF (12 Sep 2026, §1) flagged one thing for this session specifically: local
`data/*.json` is known to lag production (the workflow never commits fetched data
back to `main` — see CLAUDE.md's data-flow note), so a no-network dev mode serving
that data silently would misrepresent it as current. `tests/test_staleness.py`
already has the business-day-lag logic to detect this; S2 reuses it rather than
re-deriving it.

## What Changes

- New `scripts/dev.sh`: copies `data/*.json` → `site/data/`, prints a staleness
  warning per series (reusing the lag table/logic from `tests/test_staleness.py`,
  extracted into a shared `scripts/staleness.py` module so neither copy drifts from
  the other), then serves `site/` on port 8888. No network calls — reads only the
  local `data/` committed to the repo.
- `tests/test_staleness.py` refactored to import the table and business-day-lag
  function from `scripts/staleness.py` instead of defining them inline. Test
  behavior is unchanged (same table, same assertions).
- CLAUDE.md: new "Local Iteration Loop" section documenting the edit → reload →
  Chrome screenshot with Claude → push workflow, replacing the current ad hoc
  "Fetch fresh data / Copy to site directory / Serve locally" steps under Running
  Locally with a pointer to `scripts/dev.sh`.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
<!-- None — this adds developer tooling around the existing static site; it
doesn't change what the site or any fetcher does. -->

## Impact

- **Affected**: new `scripts/dev.sh`, new `scripts/staleness.py`;
  `tests/test_staleness.py` (refactored, not behavior-changed); `CLAUDE.md` (edited).
- **Not affected**: no fetch script, no site HTML/JS, no workflow file.
- **Rollback**: remove `scripts/dev.sh` and `scripts/staleness.py`, revert
  `tests/test_staleness.py` to its inline table, revert the CLAUDE.md section.
