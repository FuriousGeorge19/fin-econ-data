"""Fetch all Treasury yield curve tenors (daily DGS series) from FRED."""

import os
import sys
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series, get_api_key

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


def fetch_tenor(series_id, limit=6300):
    """Return {date: value} for one tenor series. ~6300 = ~25 years of trading days."""
    return {o["date"]: o["value"] for o in fetch_series(series_id, limit=limit)}


def main():
    if not get_api_key():
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Fetch all tenor series
    tenor_data = {}
    for tenor in TENORS:
        print(f"  Fetching {tenor['id']}...", end=" ", flush=True)
        tenor_data[tenor["label"]] = fetch_tenor(tenor["id"])
        print(f"{len(tenor_data[tenor['label']])} observations")

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

    descriptor = series_meta.load("yield_curve")
    fetched_at = datetime.now(timezone.utc)
    series = {
        tenor["label"]: {
            "first_observation": min(tenor_data[tenor["label"]]),
            "last_observation": max(tenor_data[tenor["label"]]),
            "observation_count": len(tenor_data[tenor["label"]]),
        }
        for tenor in TENORS
        if tenor_data[tenor["label"]]
    }
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=all_dates[-1],
        first_observation=all_dates[0],
        observation_count=len(observations),
        series=series,
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "tenors": [t["label"] for t in TENORS],
        "tenor_months": {t["label"]: t["months"] for t in TENORS},
        "observations": observations,
    }

    series_meta.write_json(OUTPUT_PATH, output)

    print(f"\nWrote {len(observations)} dates to {OUTPUT_PATH}")
    print(f"Date range: {all_dates[0]} to {all_dates[-1]}")


if __name__ == "__main__":
    main()
