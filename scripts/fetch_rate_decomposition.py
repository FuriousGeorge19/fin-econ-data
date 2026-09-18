"""Fetch the real-vs-breakeven decomposition of Treasury yield changes
(roadmap item 14) from FRED.

Every nominal yield move splits in two: change in nominal = change in real
(TIPS) yield + change in breakeven inflation, where breakeven is nominal minus
real at the same tenor. This pulls the five tenors that have both a nominal
(DGS5, 7, 10, 20, 30) and a TIPS (DFII5, 7, 10, 20, 30) constant-maturity
series, for a window long enough to cover a year back, and computes the split
for four periods: 1 week, 1 month, year to date, 1 year.

Everything is computed here, in whole basis points, from legs rounded to the
published two decimals, so nominal = real + breakeven reconciles exactly in
every cell. A date counts only if all ten series report on it. Reference dates
are the nearest such date on or before the target, the same rule the yield
curve page uses. Writes data/rate_decomposition.json.
"""

import calendar
import os
import sys
from datetime import date, datetime, timedelta, timezone

import series_meta
from fred_utils import fetch_series, get_api_key

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rate_decomposition.json")

TENORS = [
    {"id": "5Y",  "nominal": "DGS5",  "real": "DFII5"},
    {"id": "7Y",  "nominal": "DGS7",  "real": "DFII7"},
    {"id": "10Y", "nominal": "DGS10", "real": "DFII10"},
    {"id": "20Y", "nominal": "DGS20", "real": "DFII20"},
    {"id": "30Y", "nominal": "DGS30", "real": "DFII30"},
]

PERIODS = [
    {"id": "1w",  "label": "1 week"},
    {"id": "1m",  "label": "1 month"},
    {"id": "ytd", "label": "Year to date"},
    {"id": "1y",  "label": "1 year"},
]

WINDOW_DAYS = 400  # 1 year back plus slack for holidays


def add_months(d, months):
    """d shifted by whole months, clamping the day (31 Mar - 1 month = 28/29 Feb)."""
    total = d.year * 12 + (d.month - 1) + months
    year, month = divmod(total, 12)
    return date(year, month + 1, min(d.day, calendar.monthrange(year, month + 1)[1]))


def target_date(period_id, latest):
    if period_id == "1w":
        return latest - timedelta(days=7)
    if period_id == "1m":
        return add_months(latest, -1)
    if period_id == "ytd":
        return date(latest.year - 1, 12, 31)
    if period_id == "1y":
        return add_months(latest, -12)
    raise ValueError(period_id)


def nearest_on_or_before(sorted_dates, target):
    found = None
    for d in sorted_dates:
        if d <= target:
            found = d
        else:
            break
    return found


def bp(x):
    return int(round(x * 100))


def decompose(latest_row, then_row):
    """Per-tenor bp change of nominal, real and breakeven; breakeven = nominal - real."""
    out = {}
    for t in TENORS:
        k = t["id"]
        dn = bp(latest_row[k]["nominal"] - then_row[k]["nominal"])
        dr = bp(latest_row[k]["real"] - then_row[k]["real"])
        out[k] = {"nominal_bp": dn, "real_bp": dr, "breakeven_bp": dn - dr}
    return out


def build_rows(series_by_id):
    """{date_str: {tenor: {nominal, real, breakeven}}} for dates where all ten report."""
    common = None
    for t in TENORS:
        for key in ("nominal", "real"):
            dates = set(series_by_id[t[key]])
            common = dates if common is None else common & dates
    rows = {}
    for d in sorted(common):
        rows[d] = {}
        for t in TENORS:
            n = series_by_id[t["nominal"]][d]
            r = series_by_id[t["real"]][d]
            rows[d][t["id"]] = {"nominal": n, "real": r, "breakeven": round(n - r, 2)}
    return rows


def main():
    if not get_api_key():
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    start = (datetime.now(timezone.utc).date() - timedelta(days=WINDOW_DAYS)).isoformat()
    series_by_id = {}
    for t in TENORS:
        for key in ("nominal", "real"):
            sid = t[key]
            print(f"  Fetching {sid}...", end=" ", flush=True)
            obs = fetch_series(sid, extra_params={"observation_start": start})
            series_by_id[sid] = {o["date"]: o["value"] for o in obs}
            print(f"{len(obs)} observations")

    rows = build_rows(series_by_id)
    if not rows:
        print("ERROR: no date on which every series reports", file=sys.stderr)
        sys.exit(1)
    dates = sorted(rows)
    latest_str = dates[-1]
    latest = date.fromisoformat(latest_str)
    parsed = [date.fromisoformat(d) for d in dates]

    periods = []
    for p in PERIODS:
        ref = nearest_on_or_before(parsed, target_date(p["id"], latest))
        if ref is None:
            print(f"ERROR: window too short for period {p['id']}", file=sys.stderr)
            sys.exit(1)
        ref_str = ref.isoformat()
        periods.append({
            "id": p["id"],
            "label": p["label"],
            "ref_date": ref_str,
            "changes": decompose(rows[latest_str], rows[ref_str]),
        })

    descriptor = series_meta.load("rate_decomposition")
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=latest_str,
        inputs={"nominal": {"last_observation": latest_str}, "real": {"last_observation": latest_str}},
        fetched_at=datetime.now(timezone.utc),
    )
    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "tenors": [t["id"] for t in TENORS],
        "series_ids": {t["id"]: {"nominal": t["nominal"], "real": t["real"]} for t in TENORS},
        "latest": {"date": latest_str, "levels": rows[latest_str]},
        "periods": periods,
    }
    series_meta.write_json(OUTPUT_PATH, output)
    print(f"\nWrote {len(periods)} periods, latest {latest_str}, to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
