"""Fetch the TIPS real yield curve snapshot (daily DFII series) from FRED.

Mirrors scripts/fetch_yield_curve.py's shape exactly (same top-level keys:
meta, as_of, tenors, tenor_months, observations) but for the five TIPS
constant-maturity tenors, which do not all start on the same date. A date's
observation carries only the tenors that actually reported that day — no
null, no forward-fill — so a tenor's late start or (if one ever appears) an
interior gap stays visible on the chart rather than being interpolated over.
"""

import os
import sys
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series, get_api_key

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tips_curve.json")

# TIPS constant-maturity tenors this chart covers (5yr, 7yr, 10yr, 20yr, 30yr —
# FRED does not publish 1yr/2yr/3yr TIPS constant-maturity series).
TENORS = [
    {"id": "DFII5",  "label": "5yr",  "months": 60},
    {"id": "DFII7",  "label": "7yr",  "months": 84},
    {"id": "DFII10", "label": "10yr", "months": 120},
    {"id": "DFII20", "label": "20yr", "months": 240},
    {"id": "DFII30", "label": "30yr", "months": 360},
]


def fetch_tenor(series_id, limit=None):
    """Return {date: value} for one tenor series — the full published history.

    limit is None deliberately. fred_utils.fetch_series sorts descending, so a
    numeric limit drops the OLDEST observations once the series exceeds it — the
    chart would silently lose its left edge with no error anywhere. This was a
    6300-row cap (~25 years of trading days) until 2026-09-17; the TIPS curve was
    already at 5931.
    """
    return {o["date"]: o["value"] for o in fetch_series(series_id, limit=limit)}


def main():
    if not get_api_key():
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    tenor_data = {}
    for tenor in TENORS:
        print(f"  Fetching {tenor['id']}...", end=" ", flush=True)
        tenor_data[tenor["label"]] = fetch_tenor(tenor["id"])
        print(f"{len(tenor_data[tenor['label']])} observations")

    all_dates = sorted(set().union(*tenor_data.values()))

    observations = {}
    for date in all_dates:
        yields = {}
        for tenor in TENORS:
            label = tenor["label"]
            if date in tenor_data[label]:
                yields[label] = tenor_data[label][date]
        if yields:
            observations[date] = yields

    descriptor = series_meta.load("tips_curve")
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
    for tenor in TENORS:
        label = tenor["label"]
        if tenor_data[label]:
            print(f"  {label}: {min(tenor_data[label])} to {max(tenor_data[label])}, "
                  f"{len(tenor_data[label])} observations")


if __name__ == "__main__":
    main()
