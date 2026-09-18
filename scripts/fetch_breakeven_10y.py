"""Fetch the 10-Year Breakeven Inflation Rate (T10YIE) from FRED."""

import os
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series

SERIES_ID = "T10YIE"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "breakeven_10y.json")


def fetch_breakeven_10y():
    # Whole history: daily since 2003-01-02, comfortably under 10000.
    observations = fetch_series(SERIES_ID, limit=10000)

    descriptor = series_meta.load("breakeven_10y")
    fetched_at = datetime.now(timezone.utc)
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=observations[-1]["date"],
        first_observation=observations[0]["date"],
        observation_count=len(observations),
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "observations": observations,
    }

    series_meta.write_json(OUTPUT_PATH, output)

    print(f"Wrote {len(observations)} observations to {OUTPUT_PATH}")
    print(f"Date range: {observations[0]['date']} to {observations[-1]['date']}")


if __name__ == "__main__":
    fetch_breakeven_10y()
