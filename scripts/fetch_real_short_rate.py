"""Fetch the ex-post real short rate (roadmap chart 5): the 3-month Treasury
bill secondary-market rate (TB3MS, FRED, monthly, 1934-01+) minus the
year-over-year percent change in CPI-U all items, seasonally adjusted
(CPIAUCSL, FRED, monthly, 1947-01+) for the same month.

This is EX-POST: it uses realized inflation over the trailing 12 months, not
survey-based expected inflation, so it is the actual real return a saver
earned holding T-bills over that year, known only after the fact -
never what markets expected in the moment.

    real_short_rate[M] = TB3MS[M] - 100 * (CPIAUCSL[M] / CPIAUCSL[M-12] - 1)

The YoY CPI leg needs twelve months of CPI history behind it, so the earliest
possible output month is CPI's own start (1947-01) plus twelve months =
1948-01, further bounded by wherever TB3MS itself starts (1934-01, well
before that). No forward-fill or interpolation: a month is emitted only when
both TB3MS and the YoY CPI change are computable for it.

Computed at fetch time in Python, the same pattern as fetch_spreads.py -
there is no precomputed "real short rate" FRED series to pull.
"""

import os
import sys
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "real_short_rate.json")


def as_month_map(series_id):
    """Fetch a monthly FRED series and return {date: value}. FRED reports
    monthly observations on the first of the month (e.g. "2026-08-01")."""
    return {o["date"]: o["value"] for o in fetch_series(series_id)}


def shift_month(date_str, n):
    """date_str ("YYYY-MM-01") shifted by n months (n negative moves back)."""
    y, m, d = (int(p) for p in date_str.split("-"))
    total = (y * 12 + (m - 1)) + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}-{d:02d}"


def compute_yoy_cpi(cpi):
    """{date: pct} year-over-year CPI change, only where both this month and
    the same month a year earlier are present in `cpi` - no interpolation
    across a gap."""
    yoy = {}
    for d, value in cpi.items():
        prior = shift_month(d, -12)
        if prior in cpi:
            yoy[d] = 100.0 * (value / cpi[prior] - 1.0)
    return yoy


def compute_real_short_rate(tb3ms, yoy_cpi):
    """[{date, value}], oldest-first, only months where both legs exist."""
    observations = [
        {"date": d, "value": round(tb3ms[d] - yoy_cpi[d], 2)}
        for d in tb3ms
        if d in yoy_cpi
    ]
    observations.sort(key=lambda o: o["date"])
    return observations


def main():
    tb3ms = as_month_map("TB3MS")
    cpi = as_month_map("CPIAUCSL")

    yoy_cpi = compute_yoy_cpi(cpi)
    observations = compute_real_short_rate(tb3ms, yoy_cpi)

    if not observations:
        print("ERROR: no overlapping months between TB3MS and YoY CPI change.", file=sys.stderr)
        sys.exit(1)

    descriptor = series_meta.load("real_short_rate")
    fetched_at = datetime.now(timezone.utc)

    tb3ms_last = max(tb3ms)
    cpi_last = max(cpi)

    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=observations[-1]["date"],
        first_observation=observations[0]["date"],
        observation_count=len(observations),
        inputs={
            "tb3ms": {"last_observation": tb3ms_last},
            "cpi": {"last_observation": cpi_last},
        },
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "observations": observations,
    }

    series_meta.write_json(OUTPUT_PATH, output)

    print(f"Wrote {len(observations)} observations -> {OUTPUT_PATH}")
    print(f"  Range: {observations[0]['date']} -> {observations[-1]['date']}")
    print(f"  TB3MS last observation: {tb3ms_last}; CPIAUCSL last observation: {cpi_last}")
    print(f"  Latest: {observations[-1]['date']} = {observations[-1]['value']:+.2f}pp")


if __name__ == "__main__":
    main()
