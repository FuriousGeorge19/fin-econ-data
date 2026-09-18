"""Fetch the Moody's Baa-minus-Aaa corporate credit spread (roadmap chart 8,
rescoped 2026-09-17).

The roadmap originally scoped chart 8 on ICE BofA option-adjusted spreads
(FRED BAMLC0A0CM / BAMLH0A0HYM2). That version is not built here, for two
reasons decided by the project owner: FRED cut those series to a rolling
three-year window in April 2026 (they now start 2023-09-18 and contain no
recession), and ICE Data Indices' terms are restricted, which under the
precedent set by the S&P 500 P/E would force presentation.publish false. Both
facts are recorded in catalog/sources/ice-bofa.json, untouched by this fetcher.

Instead: FRED's AAA and BAA (Moody's seasoned corporate bond yields, monthly
averages, both starting 1919-01) differenced per month, BAA - AAA. This is a
quality spread between two Moody's seasoned-bond indices (both 20+ year
maturities), not an option-adjusted spread over a Treasury curve — see
series/credit_spread_baa_aaa.json's methodology for why that's the right
comparison here. No forward-fill or interpolation: a month is emitted only
when both legs report (in practice always, since both start the same month
and neither has a documented gap).
"""

import os
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "credit_spread_baa_aaa.json")


def compute_spread(aaa, baa):
    """Return [{date, value}] for BAA - AAA on shared dates, oldest-first."""
    aaa_by_date = {o["date"]: o["value"] for o in aaa}
    baa_by_date = {o["date"]: o["value"] for o in baa}
    observations = [
        {"date": d, "value": round(baa_by_date[d] - aaa_by_date[d], 2)}
        for d in baa_by_date
        if d in aaa_by_date
    ]
    observations.sort(key=lambda o: o["date"])
    return observations


def main():
    aaa = fetch_series("AAA")
    baa = fetch_series("BAA")

    observations = compute_spread(aaa, baa)

    descriptor = series_meta.load("credit_spread_baa_aaa")
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

    print(f"Wrote credit_spread_baa_aaa to {OUTPUT_PATH}")
    print(f"  {len(observations)} obs, {observations[0]['date']} → {observations[-1]['date']}, "
          f"latest {observations[-1]['value']:+.2f}")


if __name__ == "__main__":
    main()
