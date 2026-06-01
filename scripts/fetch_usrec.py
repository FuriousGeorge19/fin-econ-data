"""Fetch the NBER-based recession indicator (USREC) from FRED.

USREC is a monthly 0/1 series (1 = U.S. economy in recession). For charting we
do not need every monthly point — only the recession *intervals* used to draw
shaded bands. This script collapses contiguous runs of 1 into `{start, end}`
intervals and writes `data/usrec.json`, a shared dataset reused by multiple
charts (spreads, Fed Funds, real rate, ERP, credit spreads).
"""

import json
import os
from datetime import datetime, timezone

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
    intervals = collapse_to_intervals(observations)

    output = {
        "title": "NBER-based U.S. Recession Indicators",
        "series_id": SERIES_ID,
        "units": "Recession interval (start/end month)",
        "frequency": "Monthly",
        "source": "Federal Reserve Bank of St. Louis (FRED) / NBER",
        "description": (
            "Recession intervals derived from the monthly USREC indicator (1 = recession). "
            "Reflects only officially NBER-dated recessions, which are announced with a lag, "
            "so a current downturn may not yet appear. Months are assigned to the 1st; an "
            "ongoing recession has end = null."
        ),
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "recessions": intervals,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(intervals)} recession intervals to {OUTPUT_PATH}")
    if intervals:
        print(f"Earliest: {intervals[0]['start']}  |  Latest: {intervals[-1]['start']} "
              f"→ {intervals[-1]['end']}")


if __name__ == "__main__":
    main()
