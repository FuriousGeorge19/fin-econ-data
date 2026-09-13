"""Fetch Treasury yield spreads (10y-2y and 10y-3m) from FRED.

Per the project convention (config.yaml / ARCHITECTURE.md Trigger #3), the
spreads are *computed in Python at fetch time* from the daily constant-maturity
component series (DGS10, DGS2, DGS3MO) rather than pulled from FRED's precomputed
T10Y2Y / T10Y3M, and rather than computed in the browser. A spread is emitted
only for dates where both legs report — no forward-fill, no interpolation — so
each spread spans its own valid date range (10y-2y from ~1976, 10y-3m from ~1982).
"""

import os
from datetime import datetime, timezone

import series_meta
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

    descriptor = series_meta.load("spreads")
    fetched_at = datetime.now(timezone.utc)
    last_observation = max(spread_10y2y[-1]["date"], spread_10y3m[-1]["date"])
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=last_observation,
        series={
            "10y2y": {
                "first_observation": spread_10y2y[0]["date"],
                "last_observation": spread_10y2y[-1]["date"],
                "observation_count": len(spread_10y2y),
            },
            "10y3m": {
                "first_observation": spread_10y3m[0]["date"],
                "last_observation": spread_10y3m[-1]["date"],
                "observation_count": len(spread_10y3m),
            },
        },
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "last_updated": series_meta.last_updated_alias(fetched_at),
        "series": {
            "10y2y": {"label": "10Y − 2Y", "observations": spread_10y2y},
            "10y3m": {"label": "10Y − 3M", "observations": spread_10y3m},
        },
    }

    series_meta.write_json(OUTPUT_PATH, output)

    print(f"Wrote spreads to {OUTPUT_PATH}")
    for key, s in output["series"].items():
        obs = s["observations"]
        print(f"  {key}: {len(obs)} obs, {obs[0]['date']} → {obs[-1]['date']}, "
              f"latest {obs[-1]['value']:+.2f}")


if __name__ == "__main__":
    main()
