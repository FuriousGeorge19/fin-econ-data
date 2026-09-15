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
PORT="${1:-8888}"

# The file list — here (for --live), in the workflow's seed step, in
# build_site.py's data copy, and in staleness.py's check() — derives from
# series/*.json rather than being hand-copied in each place.
SERIES_IDS=()
for f in "$REPO_ROOT"/series/*.json; do
  SERIES_IDS+=("$(basename "$f" .json)")
done

if [ "$LIVE" = "1" ]; then
  echo "Downloading live data/*.json from joemirza.com..."
  for id in "${SERIES_IDS[@]}"; do
    curl -fsSL "https://joemirza.com/data/${id}.json" -o "$REPO_ROOT/data/${id}.json"
    echo "  ${id}.json"
  done
  echo ""
fi

# --include-unpublished: build charts marked presentation.publish false
# (the S&P 500 P/E) too. They are deliberately absent from the deployed
# site; locally they are the point of this loop.
python3 "$REPO_ROOT/scripts/build_site.py" --include-unpublished

echo "Local data/ freshness (this checkout — may lag the live site unless run with --live):"
python3 "$REPO_ROOT/scripts/staleness.py" local

echo ""
echo "Serving $REPO_ROOT/site at http://localhost:$PORT"
cd "$REPO_ROOT/site" && python3 -m http.server "$PORT"
