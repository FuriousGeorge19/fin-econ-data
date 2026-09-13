"""Fetch the NBER-based recession indicator (USREC) from FRED.

USREC is a monthly 0/1 series (1 = U.S. economy in recession). For charting we
do not need every monthly point — only the recession *intervals* used to draw
shaded bands. This script collapses contiguous runs of 1 into `{start, end}`
intervals and writes `data/usrec.json`, a shared dataset reused by multiple
charts (spreads, Fed Funds, real rate, ERP, credit spreads).
"""

import os
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series

SERIES_ID = "USREC"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "usrec.json")


def collapse_to_intervals(observations):
    """Collapse a monthly 0/1 USREC series into recession intervals.

    Each interval is {"start": first recession month, "end": last recession
    month}, both as 'YYYY-MM-01'. If the most recent observation is still in
    recession, the final interval's end is None (ongoing).
    """
    intervals = []
    start = None
    last_rec_date = None
    for obs in observations:  # ascending by date
        if obs["value"] == 1.0:
            if start is None:
                start = obs["date"]
            last_rec_date = obs["date"]
        elif start is not None:
            intervals.append({"start": start, "end": last_rec_date})
            start = None

    if start is not None:
        # Latest observation is still a recession month → ongoing, open-ended.
        intervals.append({"start": start, "end": None})

    return intervals


def main():
    observations = fetch_series(SERIES_ID)  # FRED-primary: exits if key missing
    last_observation = observations[-1]  # captured before collapsing to intervals
    intervals = collapse_to_intervals(observations)

    descriptor = series_meta.load("usrec")
    fetched_at = datetime.now(timezone.utc)
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=last_observation["date"],
        latest_value=last_observation["value"],
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "recessions": intervals,
    }

    series_meta.write_json(OUTPUT_PATH, output)

    print(f"Wrote {len(intervals)} recession intervals to {OUTPUT_PATH}")
    if intervals:
        print(f"Earliest: {intervals[0]['start']}  |  Latest: {intervals[-1]['start']} "
              f"→ {intervals[-1]['end']}")


if __name__ == "__main__":
    main()
