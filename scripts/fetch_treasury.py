"""Fetch 10-Year Treasury Constant Maturity Rate (DGS10) from FRED."""

import json
import os
from datetime import datetime, timezone

from fred_utils import fetch_series

SERIES_ID = "DGS10"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dgs10.json")


def fetch_dgs10():
    # ~10 years of trading days; missing "." dropped and sorted oldest-first.
    observations = fetch_series(SERIES_ID, limit=2520)

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
