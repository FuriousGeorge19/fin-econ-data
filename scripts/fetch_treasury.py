"""Fetch 10-Year Treasury Constant Maturity Rate (DGS10) from FRED."""

import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
SERIES_ID = "DGS10"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dgs10.json")


def fetch_dgs10():
    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={SERIES_ID}"
        f"&api_key={FRED_API_KEY}"
        f"&file_type=json"
        f"&sort_order=desc"
        f"&limit=2520"  # ~10 years of trading days
    )

    req = Request(url, headers={"User-Agent": "joemirza-site/1.0"})
    try:
        with urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode())
    except URLError as e:
        print(f"ERROR: Failed to fetch from FRED: {e}", file=sys.stderr)
        sys.exit(1)

    # Clean observations: drop missing values ("."), convert to float
    observations = []
    for obs in raw.get("observations", []):
        if obs["value"] != ".":
            observations.append({
                "date": obs["date"],
                "value": float(obs["value"]),
            })

    # Sort chronologically (oldest first) for charting
    observations.sort(key=lambda x: x["date"])

    output = {
        "series_id": SERIES_ID,
        "title": "10-Year Treasury Constant Maturity Rate",
        "units": "Percent",
        "frequency": "Daily",
        "source": "Federal Reserve Bank of St. Louis (FRED)",
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "observations": observations,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(observations)} observations to {OUTPUT_PATH}")
    print(f"Date range: {observations[0]['date']} to {observations[-1]['date']}")


if __name__ == "__main__":
    fetch_dgs10()
