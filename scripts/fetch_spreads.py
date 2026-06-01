"""Fetch Treasury yield spreads (10y-2y and 10y-3m) from FRED.

Per the project convention (config.yaml / ARCHITECTURE.md Trigger #3), the
spreads are *computed in Python at fetch time* from the daily constant-maturity
component series (DGS10, DGS2, DGS3MO) rather than pulled from FRED's precomputed
T10Y2Y / T10Y3M, and rather than computed in the browser. A spread is emitted
only for dates where both legs report — no forward-fill, no interpolation — so
each spread spans its own valid date range (10y-2y from ~1976, 10y-3m from ~1982).
"""

import json
import os
from datetime import datetime, timezone

from fred_utils import fetch_series

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "spreads.json")


def as_date_map(series_id):
    """Fetch a component series and return {date: value} over full history."""
    return {o["date"]: o["value"] for o in fetch_series(series_id)}


def compute_spread(long_leg, short_leg):
    """Return [{date, value}] for long_leg − short_leg on shared dates, oldest-first."""
    observations = [
        {"date": d, "value": round(long_leg[d] - short_leg[d], 2)}
        for d in long_leg
        if d in short_leg
    ]
    observations.sort(key=lambda o: o["date"])
    return observations


def main():
    dgs10 = as_date_map("DGS10")
    dgs2 = as_date_map("DGS2")
    dgs3mo = as_date_map("DGS3MO")

    spread_10y2y = compute_spread(dgs10, dgs2)
    spread_10y3m = compute_spread(dgs10, dgs3mo)

    output = {
        "title": "U.S. Treasury Yield Spreads",
        "units": "Percentage points",
        "frequency": "Daily",
        "source": "Federal Reserve Bank of St. Louis (FRED)",
        "methodology": (
            "10y-2y = DGS10 − DGS2; 10y-3m = DGS10 − DGS3MO. Computed per date in Python "
            "from the daily constant-maturity series, only where both legs report (no fill "
            "or interpolation). A negative value indicates an inverted curve segment."
        ),
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "series": {
            "10y2y": {"label": "10Y − 2Y", "observations": spread_10y2y},
            "10y3m": {"label": "10Y − 3M", "observations": spread_10y3m},
        },
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote spreads to {OUTPUT_PATH}")
    for key, s in output["series"].items():
        obs = s["observations"]
        print(f"  {key}: {len(obs)} obs, {obs[0]['date']} → {obs[-1]['date']}, "
              f"latest {obs[-1]['value']:+.2f}")


if __name__ == "__main__":
    main()
