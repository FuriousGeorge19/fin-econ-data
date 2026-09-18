"""Fetch the Effective Federal Funds Rate (FEDFUNDS) from FRED.

Monthly average, not the daily DFF series: the point of this chart is the
full history back to 1954, and the site convention forbids upsampling a
monthly series to daily.
"""

import os
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series

SERIES_ID = "FEDFUNDS"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fedfunds.json")


def fetch_fedfunds():
    # Full monthly history back to 1954-07; "." missing-value sentinel
    # dropped, sorted oldest-first, by fetch_series().
    observations = fetch_series(SERIES_ID, limit=None)

    descriptor = series_meta.load("fedfunds")
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
    fetch_fedfunds()
