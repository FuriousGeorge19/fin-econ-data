"""Equity risk premium: the CAPE earnings yield minus an ex-ante real 10-year Treasury yield.

Roadmap chart 7, rescoped by S10 (2026-09-16) and built in S11c.

    ERP = (100 / CAPE)  −  (GS10 − EXPINF10YR)

Why each leg is what it is:

* **CAPE yield, not trailing P/E.** The roadmap originally scoped this on the
  S&P 500 trailing earnings yield. That series (`sp500_pe`) is unpublished and
  its confirmed/estimated boundary moves around with S&P's reporting calendar;
  CAPE's ten-year average denominator is stable and is the measure the
  literature actually uses for a long-horizon premium.

* **GS10 − EXPINF10YR, not DFII10.** A real yield is what the ERP has to be
  measured against, and TIPS give one directly — but `DFII10` starts 2003-01,
  which throws away the 1980s and 1990s. The Cleveland Fed's 10-year expected
  inflation (`EXPINF10YR`) starts 1982-01, so the nominal-minus-expected
  construction reaches back two more decades. This is an **ex-ante** real rate:
  what investors expected, not what they got. `real_short_rate` (chart 5) is
  the ex-post counterpart, and the two are not comparable.

Monthly. Starts 1982-01, the first month all three legs exist.

**This series is not published** (`presentation.publish: false`). The CAPE yield
is 1/CAPE, and CAPE is built from S&P's price and earnings columns in Shiller's
workbook. S&P DJI declined free permission on 2026-09-15 with "not the P/E
values" excluded even from the paid licence, and Shiller's side deferred to S&P
on 2026-09-17. Settled, not pending — see CLAUDE.md's Licence Notes.

CAPE is re-read from Shiller's workbook here rather than from
`data/sp500_cape.json`: `scripts/fetch_all.py` runs fetchers as independent
subprocesses in no guaranteed order, so reading a sibling's output would make
this series silently depend on whether that fetch had already run and
succeeded. Reusing `fetch_sp500_pe.py`'s download and parse helpers (rather
than duplicating them) is the pattern `fetch_gs10_long.py` established in S11a.
"""

import os
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series
from fetch_sp500_pe import (
    fetch_bytes,
    resolve_shiller_xls_url,
    detect_excel_format,
    parse_shiller,
)

SERIES_ID = "equity_risk_premium"
NOMINAL_ID = "GS10"
EXPECTED_INFLATION_ID = "EXPINF10YR"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", f"{SERIES_ID}.json")

# EXPINF10YR's first observation. The output can start no earlier; asserted by
# tests/test_equity_risk_premium.py, which fails by name if FRED moves it.
EXPINF_START = "1982-01-01"


def fetch_cape():
    """Return {date: CAPE} from Shiller's maintained workbook.

    Reuses fetch_sp500_pe.py's helpers so the URL resolution (shillerdata.com's
    download link carries a changing ?ver= tag), the xls/xlsx format sniff and
    the header-row scan all live in exactly one place.
    """
    url = resolve_shiller_xls_url()
    data_bytes = fetch_bytes(url)
    detect_excel_format(data_bytes)
    rows = parse_shiller(data_bytes)
    return {r["date"]: r["cape"] for r in rows if r["cape"]}


def fetch_monthly(series_id):
    """Return {date: value} for a monthly FRED series, full history."""
    return {o["date"]: o["value"] for o in fetch_series(series_id)}


def build_observations(cape, nominal, expected_inflation):
    """Compute the ERP for every month where all three legs report.

    No forward-fill and no interpolation: a month missing any leg is simply
    absent, the same rule fetch_spreads.py and fetch_real_short_rate.py use.
    """
    observations = []
    for date in sorted(set(cape) & set(nominal) & set(expected_inflation)):
        cape_value = cape[date]
        if cape_value <= 0:  # never seen; a zero would make the yield infinite
            continue
        # Round each leg FIRST, then subtract, so the two legs a reader sees in
        # the tooltip actually subtract to the headline they see. Rounding the
        # difference independently lets double rounding put them 0.01 apart —
        # small, but it makes the tooltip contradict itself, and the only
        # reason to carry the legs at all is so the arithmetic is checkable.
        cape_yield = round(100.0 / cape_value, 2)
        real_yield = round(nominal[date] - expected_inflation[date], 2)
        observations.append({
            "date": date,
            "value": round(cape_yield - real_yield, 2),
            "cape_yield": cape_yield,
            "real_yield": real_yield,
        })
    return observations


def main():
    print("Fetching CAPE from Shiller's workbook...")
    cape = fetch_cape()
    print(f"  {len(cape)} months with CAPE")

    print(f"Fetching {NOMINAL_ID} and {EXPECTED_INFLATION_ID} from FRED...")
    nominal = fetch_monthly(NOMINAL_ID)
    expected_inflation = fetch_monthly(EXPECTED_INFLATION_ID)
    print(f"  {len(nominal)} months of {NOMINAL_ID}, "
          f"{len(expected_inflation)} months of {EXPECTED_INFLATION_ID}")

    observations = build_observations(cape, nominal, expected_inflation)
    if not observations:
        raise SystemExit("ERROR: no month had all three legs; refusing to write an empty series")

    descriptor = series_meta.load(SERIES_ID)
    fetched_at = datetime.now(timezone.utc)
    last = observations[-1]

    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=last["date"],
        first_observation=observations[0]["date"],
        observation_count=len(observations),
        inputs={
            "cape": {"last_observation": max(cape)},
            "nominal": {"last_observation": max(nominal)},
            "expected_inflation": {"last_observation": max(expected_inflation)},
        },
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "observations": observations,
    }
    series_meta.write_json(OUTPUT_PATH, output)

    print(f"\nWrote {len(observations)} observations to data/{SERIES_ID}.json")
    print(f"  Range: {observations[0]['date']} → {last['date']}")
    print(f"  Latest: CAPE yield {last['cape_yield']}% − real 10y {last['real_yield']}% "
          f"= {last['value']:+.2f}pp")


if __name__ == "__main__":
    main()
