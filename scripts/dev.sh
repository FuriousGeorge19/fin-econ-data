#!/usr/bin/env bash
# Local iteration loop: run scripts/build_site.py (generates the multi-page
# site and copies committed data/ into site/data/), warn about any series
# known to be overdue (no network calls — see scripts/staleness.py), then
# serve site/ on 8888. Works with FRED_API_KEY unset.
#
# Usage: scripts/dev.sh [--live] [port]
#   --live   download each series' live data/<id>.json from joemirza.com
#            into data/ before serving, for local work that needs current
#            data rather than main's fixtures (see CLAUDE.md's data-flow
#            note: main's data/*.json are test fixtures, not the deploy
#            history — gh-pages is).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

LIVE=0
if [ "${1:-}" = "--live" ]; then
  LIVE=1
  shift
fi
# 8899, not 8888: 8888 is permanently occupied on the author's machine by an
# unrelated node server (see the port check before the serve step below).
PORT="${1:-8899}"

# The file list derives from series/*.json rather than being hand-copied here,
# in the workflow's seed step, in build_site.py's data copy and in
# staleness.py's check().
#
# --live pulls only the PUBLISHED series: a series marked
# presentation.publish false is deliberately absent from the deploy, so
# curl -f would 404 on it and (under set -e) abort the whole script. That is
# what happened from 2026-09-15, when sp500_pe became the first unpublished
# series, until this was fixed on 2026-09-17.
SERIES_IDS=()
while IFS= read -r id; do
  SERIES_IDS+=("$id")
done < <(python3 - "$REPO_ROOT" <<'PY'
import glob, json, os, sys
for path in sorted(glob.glob(os.path.join(sys.argv[1], "series", "*.json"))):
    with open(path) as fh:
        descriptor = json.load(fh)
    presentation = descriptor.get("presentation") or {}
    if presentation.get("publish") is not False:
        print(descriptor["id"])
PY
)

if [ "$LIVE" = "1" ]; then
  # http, not https: joemirza.com still serves GitHub's *.github.io wildcard
  # certificate, so an https fetch fails cert validation outright (open item
  # since the March 2026 deploy — fix is to re-add the custom domain in
  # Settings -> Pages). Flip this back to https once that is resolved.
  echo "Downloading live data/*.json from joemirza.com (published series only)..."
  for id in "${SERIES_IDS[@]}"; do
    curl -fsSL "http://joemirza.com/data/${id}.json" -o "$REPO_ROOT/data/${id}.json"
    echo "  ${id}.json"
  done
  echo ""
  echo "Note: series marked presentation.publish false are not on the live site;"
  echo "      their data/ files keep this checkout's fixtures."
  echo ""
fi

# --include-unpublished: build the charts marked presentation.publish false
# too. As of 2026-09-17 that is sp500_pe, sp500_cape, sp500_dividend_yield,
# sp500_earnings_yield and equity_risk_premium — every one of them S&P-derived
# and unpublishable on terms grounds. They are deliberately absent from the
# deployed site, and locally they are the point of this loop: this script is
# the only way to look at them.
python3 "$REPO_ROOT/scripts/build_site.py" --include-unpublished

echo "Local data/ freshness (this checkout — may lag the live site unless run with --live):"
python3 "$REPO_ROOT/scripts/staleness.py" local

echo ""

# Fail with an explanation rather than a Python traceback. Port 8888 — this
# script's own historical default — is occupied on the author's machine by an
# unrelated long-running node server, which is why requests to it come back
# with someone else's content instead of this site's. Verified 2026-09-17 with
# lsof; the default moved to 8899 the same day.
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "ERROR: port $PORT is already in use:" >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2
  echo "" >&2
  echo "Pass a different port:  scripts/dev.sh $((PORT + 1))" >&2
  exit 1
fi

echo "Serving $REPO_ROOT/site at http://127.0.0.1:$PORT  (use 127.0.0.1, not localhost — see CLAUDE.md)"
cd "$REPO_ROOT/site" && python3 -m http.server "$PORT"
