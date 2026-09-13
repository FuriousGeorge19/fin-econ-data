#!/usr/bin/env bash
# Local iteration loop: copy committed data/ into site/data/, warn about any
# series known to be stale (no network calls — see scripts/staleness.py), then
# serve site/ on 8888. Works with FRED_API_KEY unset.
#
# Usage: scripts/dev.sh [port]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8888}"

mkdir -p "$REPO_ROOT/site/data"
# Same file list as the "Copy data to site directory" step in
# .github/workflows/update-data.yml — deliberately not data/*.json, since
# data/earnings_overrides.json is a fetch-time input (consumed by
# fetch_sp500_pe.py), not something the frontend reads.
for f in dgs10.json sp500_pe.json yield_curve.json usrec.json spreads.json; do
  cp "$REPO_ROOT/data/$f" "$REPO_ROOT/site/data/$f"
done

echo "Local data/ freshness (this checkout — may lag the live site, see CLAUDE.md):"
python3 "$REPO_ROOT/scripts/staleness.py" local

echo ""
echo "Serving $REPO_ROOT/site at http://localhost:$PORT"
cd "$REPO_ROOT/site" && python3 -m http.server "$PORT"
