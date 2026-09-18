"""Correctness tests for the three stock-bond series (S11e, roadmap items
15-17): risk_off_days, stock_bond_correlation, drawdown_curve_shift.

The pure-function tests need no data or network. The story tests read the
committed fixtures. The cross-check needs network + FRED_API_KEY.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import stock_bond as sb  # noqa: E402
from fred_utils import fetch_series  # noqa: E402

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


# ── Pure functions ──────────────────────────────────────────────────────────

def test_pearson_perfect_inverse_and_no_variance():
    assert sb.pearson([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert sb.pearson([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0)
    assert sb.pearson([1, 1, 1, 1], [1, 2, 3, 4]) is None


def test_daily_pairs_pairs_consecutive_common_dates_only():
    sp = {"2026-01-02": 100.0, "2026-01-05": 99.0, "2026-01-06": 101.0}
    yields = {"10yr": {"2026-01-02": 4.00, "2026-01-06": 4.10}}  # no yield on the 5th
    pairs = sb.daily_pairs(sp, yields, ["10yr"])
    assert len(pairs) == 1
    assert pairs[0]["date"] == "2026-01-06"
    assert pairs[0]["ret_pct"] == pytest.approx(1.0)   # 100 -> 101, skipping the 5th
    assert pairs[0]["dy_bp"] == {"10yr": 10}


def _pair(date, ret, dy10, dy7=0):
    return {"date": date, "ret_pct": ret, "dy_bp": {"7yr": dy7, "10yr": dy10}}


def test_risk_off_stats_counts_only_days_at_or_below_the_threshold():
    pairs = [_pair("d1", -1.0, -6, -4), _pair("d2", -2.0, 4, 2), _pair("d3", 0.5, 9, 9),
             _pair("d4", -0.99, 5, 5)]
    row = sb.risk_off_stats(pairs, ["7yr", "10yr"])
    assert row["days"] == 2 and row["sessions"] == 4
    assert row["avg_sp_fall_pct"] == pytest.approx(-1.5)
    assert row["by_tenor"]["10yr"]["share_fell_pct"] == 50
    assert row["by_tenor"]["10yr"]["avg_change_bp"] == pytest.approx(-1.0)
    # fund move = -4.9 x the average 7yr change (-1 bp) = +0.049 -> 0.05
    assert row["fund_move_pct"] == pytest.approx(0.05)


def test_risk_off_stats_with_no_bad_days_reports_none_not_zero():
    row = sb.risk_off_stats([_pair("d1", 0.3, 1), _pair("d2", -0.2, -1), _pair("d3", 0.1, 0)], ["7yr", "10yr"])
    assert row["days"] == 0 and row["avg_sp_fall_pct"] is None and row["by_tenor"] == {}


def test_drawdowns_run_peak_to_lowest_close_before_recovery():
    sp = {"d1": 100, "d2": 90, "d3": 85, "d4": 95, "d5": 101, "d6": 99, "d7": 98}
    found = sb.drawdowns(sp, sorted(sp), min_pct=5)
    assert found == [{"peak_date": "d1", "trough_date": "d3", "sp_change_pct": -15.0, "ongoing": False}]


def test_drawdowns_marks_an_unrecovered_fall_ongoing_and_skips_shallow_ones():
    sp = {"d1": 100, "d2": 97, "d3": 100.5, "d4": 90}
    found = sb.drawdowns(sp, sorted(sp), min_pct=5)
    assert len(found) == 1 and found[0]["ongoing"] is True and found[0]["peak_date"] == "d3"


# ── Committed fixtures: the story the handoff told ──────────────────────────

def _row(risk_off, year):
    return next(r for r in risk_off["rows"] if r["id"] == year)


def test_bonds_hedged_in_2019_and_stopped_in_2022(load_data):
    risk_off = load_data("risk_off_days")
    assert _row(risk_off, "2019")["correlation_10yr"] > 0.3
    assert _row(risk_off, "2019")["by_tenor"]["10yr"]["share_fell_pct"] == 100
    # The sign convention: the correlation is stock returns against yield CHANGES,
    # so 2022 (bonds fell with stocks) is negative.
    assert _row(risk_off, "2022")["correlation_10yr"] == pytest.approx(-0.18, abs=0.03)
    assert _row(risk_off, "2022")["by_tenor"]["10yr"]["share_fell_pct"] < 50


def test_rolling_correlation_ends_negative_and_stays_in_range(load_data):
    corr = load_data("stock_bond_correlation")
    values = [o["value"] for o in corr["observations"]]
    assert all(-1 <= v <= 1 for v in values)
    dates = [o["date"] for o in corr["observations"]]
    assert dates == sorted(dates) and len(set(dates)) == len(dates)
    assert values[-1] < 0


def test_drawdown_windows_are_ordered_and_deep_enough(load_data):
    shift = load_data("drawdown_curve_shift")
    for w in shift["windows"]:
        assert w["peak_date"] < w["trough_date"]
        assert w["sp_change_pct"] <= -shift["min_drawdown_pct"]
    peaks = [w["peak_date"] for w in shift["windows"]]
    assert peaks == sorted(peaks, reverse=True)


# ── Cross-check against a direct FRED pull ──────────────────────────────────

@requires_fred_key
@pytest.mark.network
def test_2022_bad_day_count_matches_an_independent_pull(load_data):
    sp = {o["date"]: o["value"] for o in fetch_series("SP500")}
    y10 = {o["date"]: o["value"] for o in fetch_series("DGS10")}
    common = sorted(d for d in sp if d in y10)
    bad = sum(
        1 for prev, cur in zip(common, common[1:])
        if cur.startswith("2022") and sp[cur] / sp[prev] - 1 <= -0.01
    )
    row = next(r for r in load_data("risk_off_days")["rows"] if r["id"] == "2022")
    assert row["days"] == bad
