"""Structural invariants that must hold for every committed data file,
independent of whether the data is fresh: unique/monotone dates, no missing
value silently became zero, and internally consistent header fields.
"""

import math
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from fetch_sp500_pe import add_months_str
from staleness import today_eastern


def _dates_unique_and_ascending(dates):
    return list(dates) == sorted(set(dates)) and len(dates) == len(set(dates))


def test_dgs10_dates_unique_and_ascending(dgs10):
    dates = [o["date"] for o in dgs10["observations"]]
    assert _dates_unique_and_ascending(dates)


def test_sp500_pe_dates_unique_and_ascending(sp500_pe):
    dates = [o["date"] for o in sp500_pe["observations"]]
    assert _dates_unique_and_ascending(dates)


def test_yield_curve_dates_ascending(yield_curve):
    # observations is a date-keyed dict; JSON preserves insertion order, and the
    # fetcher writes it from `sorted(all_dates)`, so file order should already
    # be ascending — this catches a future regression in that write order.
    dates = list(yield_curve["observations"].keys())
    assert _dates_unique_and_ascending(dates)


def test_spreads_dates_unique_and_ascending(spreads):
    for key, series in spreads["series"].items():
        dates = [o["date"] for o in series["observations"]]
        assert _dates_unique_and_ascending(dates), f"series {key}"


def test_usrec_intervals_ordered_and_non_overlapping(usrec):
    intervals = usrec["recessions"]
    starts = [i["start"] for i in intervals]
    assert starts == sorted(starts)
    for i, interval in enumerate(intervals):
        if interval["end"] is not None:
            assert interval["end"] >= interval["start"]
        if i + 1 < len(intervals) and interval["end"] is not None:
            assert intervals[i + 1]["start"] > interval["end"]


def test_dgs10_no_missing_value_became_zero(dgs10):
    # FRED's "." sentinel for missing days is dropped by fred_utils, never
    # coerced to float — a stray 0.0 here would mean that guard broke, since a
    # 10Y yield of exactly 0.00% has never occurred.
    assert all(o["value"] != 0.0 for o in dgs10["observations"])


def test_yield_curve_values_are_finite_percentages(yield_curve):
    for date, tenors in yield_curve["observations"].items():
        for label, value in tenors.items():
            assert math.isfinite(value), f"{date} {label}"
            assert -1.0 < value < 25.0, f"{date} {label} = {value}"


def test_sp500_pe_internal_consistency(sp500_pe):
    # price / earnings should reproduce the stored pe. pe is computed from
    # Shiller's unrounded inputs, while the stored price/earnings are each
    # independently rounded to 2 decimals — for the earliest, sub-$0.50
    # earnings era that rounding is a big fraction of the value (e.g. an
    # earnings of 0.175 rounds to 0.17 or 0.18), so this needs a relative,
    # not absolute, tolerance. 3.5% covers every observation in the current
    # file with margin (worst case observed: 2.95%, 1895-02-01).
    for o in sp500_pe["observations"]:
        expected = o["price"] / o["earnings"]
        assert expected == pytest.approx(o["pe"], rel=0.035), o


def test_sp500_pe_confirmed_estimated_boundary(sp500_pe, earnings_overrides):
    """Structural invariants from design decision 10 (openspec change
    s3-series-metadata), replacing the S1 xfail: the header's earnings value
    is the last override's TTM, confirmed_through is exactly two months after
    that override's effective_from, and every observation splits cleanly
    across that boundary. The old header-vs-last-observation check would pass
    tautologically under forward-fill, which is why it's structural now."""
    last = sorted(earnings_overrides["entries"], key=lambda e: e["effective_from"])[-1]
    earnings_as_of = sp500_pe["as_of"]["inputs"]["earnings"]

    assert earnings_as_of["value"] == last["ttm_eps"]

    confirmed_through = add_months_str(last["effective_from"], 2)
    assert earnings_as_of["confirmed_through"] == confirmed_through

    confirmed_dates = [o["date"] for o in sp500_pe["observations"] if not o["estimated"]]
    estimated_dates = [o["date"] for o in sp500_pe["observations"] if o["estimated"]]

    assert confirmed_dates, "expected at least one confirmed observation"
    assert max(confirmed_dates) == confirmed_through
    assert all(d <= confirmed_through for d in confirmed_dates)
    assert all(d > confirmed_through for d in estimated_dates)


def test_sp500_pe_no_observation_in_current_or_future_month(sp500_pe):
    """FRED's monthly average of a month in progress moves daily; the fetcher
    drops it (design decision 10), so the last observation is always dated
    before the current US Eastern month."""
    current_month_start = today_eastern().replace(day=1)
    latest = date.fromisoformat(sp500_pe["observations"][-1]["date"])
    assert latest < current_month_start
