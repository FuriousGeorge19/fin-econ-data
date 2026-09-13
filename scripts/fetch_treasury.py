"""Fetch 10-Year Treasury Constant Maturity Rate (DGS10) from FRED."""

import os
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series

SERIES_ID = "DGS10"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dgs10.json")


def fetch_dgs10():
    # ~10 years of trading days; missing "." dropped and sorted oldest-first.
    observations = fetch_series(SERIES_ID, limit=2520)

    descriptor = series_meta.load("dgs10")
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
    fetch_dgs10()
