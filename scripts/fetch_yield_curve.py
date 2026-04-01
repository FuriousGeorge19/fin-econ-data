"""Fetch all Treasury yield curve tenors (daily DGS series) from FRED."""

import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "yield_curve.json")

# All standard tenors on the Treasury yield curve
TENORS = [
    {"id": "DGS1MO", "label": "1mo",  "months": 1},
    {"id": "DGS3MO", "label": "3mo",  "months": 3},
    {"id": "DGS6MO", "label": "6mo",  "months": 6},
    {"id": "DGS1",   "label": "1yr",  "months": 12},
    {"id": "DGS2",   "label": "2yr",  "months": 24},
    {"id": "DGS3",   "label": "3yr",  "months": 36},
    {"id": "DGS5",   "label": "5yr",  "months": 60},
    {"id": "DGS7",   "label": "7yr",  "months": 84},
    {"id": "DGS10",  "label": "10yr", "months": 120},
    {"id": "DGS20",  "label": "20yr", "months": 240},
    {"id": "DGS30",  "label": "30yr", "months": 360},
]


def fetch_series(series_id, limit=6300):
    """Fetch a single series from FRED. ~6300 = ~25 years of trading days."""
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}"
        f"&api_key={FRED_API_KEY}"
        f"&file_type=json"
        f"&sort_order=desc"
        f"&limit={limit}"
    )
    req = Request(url, headers={"User-Agent": "joemirza-site/1.0"})
    with urlopen(req, timeout=30) as resp:
        raw = json.loads(resp.read().decode())

    # Return dict of date -> value, skipping missing (".") entries
    out = {}
    for obs in raw.get("observations", []):
        if obs["value"] != ".":
            out[obs["date"]] = float(obs["value"])
    return out


def main():
    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Fetch all tenor series
    tenor_data = {}
    for tenor in TENORS:
        print(f"  Fetching {tenor['id']}...", end=" ", flush=True)
        try:
            tenor_data[tenor["label"]] = fetch_series(tenor["id"])
            print(f"{len(tenor_data[tenor['label']])} observations")
        except URLError as e:
            print(f"FAILED: {e}", file=sys.stderr)
            sys.exit(1)

    # Collect all unique dates across all tenors, sorted
    all_dates = sorted(set().union(*tenor_data.values()))

    # Build observations: one entry per date with available tenors
    observations = {}
    for date in all_dates:
        yields = {}
        for tenor in TENORS:
            label = tenor["label"]
            if date in tenor_data[label]:
                yields[label] = tenor_data[label][date]
        if yields:  # skip dates with no data at all
            observations[date] = yields

    output = {
        "title": "U.S. Treasury Yield Curve",
        "units": "Percent",
        "frequency": "Daily",
        "source": "Federal Reserve Bank of St. Louis (FRED)",
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "tenors": [t["label"] for t in TENORS],
        "tenor_months": {t["label"]: t["months"] for t in TENORS},
        "observations": observations,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(observations)} dates to {OUTPUT_PATH}")
    print(f"Date range: {all_dates[0]} to {all_dates[-1]}")


if __name__ == "__main__":
    main()
