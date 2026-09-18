"""Correctness tests for equity_risk_premium (S11c, roadmap chart 7).

ERP = (100 / CAPE) − (GS10 − EXPINF10YR), monthly from 1982-01.

Structural checks need no network. The cross-checks recompute sampled months
from fresh upstream pulls — Shiller's workbook for CAPE (no key needed) and
FRED for the two rate legs (needs FRED_API_KEY).
"""

import os

import pytest

from fetch_equity_risk_premium import (
    EXPINF_START,
    EXPECTED_INFLATION_ID,
    NOMINAL_ID,
    build_observations,
    fetch_cape,
)
from fred_utils import fetch_series

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@pytest.fixture
def erp(load_data):
    return load_data("equity_risk_premium")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_dates_unique_and_ascending(erp):
    dates = [o["date"] for o in erp["observations"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))


def test_monthly_first_of_month(erp):
    # Monthly cadence, and no daily-cadence leg ever got interleaved in.
    for o in erp["observations"]:
        assert o["date"][8:10] == "01", o


def test_starts_no_earlier_than_expinf(erp):
    # The Cleveland Fed model is the binding constraint on how far back this
    # series can reach; CAPE goes to 1881 and GS10 to 1953.
    assert erp["observations"][0]["date"] >= EXPINF_START


def test_legs_reconcile_to_the_headline(erp):
    # Each observation carries its own two legs so a reader can see which side
    # moved. They must actually add up, or the chart and its tooltip disagree.
    for o in erp["observations"]:
        assert abs((o["cape_yield"] - o["real_yield"]) - o["value"]) <= 0.01, o


def test_cape_yield_is_plausible(erp):
    # 1/CAPE over this period runs roughly 2% (dot-com and 2021 peaks) to 15%
    # (August 1982). A leg dropped or a percent/fraction mix-up lands outside.
    ys = [o["cape_yield"] for o in erp["observations"]]
    assert 1.5 < min(ys) < 3.5, min(ys)
    assert 10 < max(ys) < 20, max(ys)


def test_values_are_plausible_percentage_points(erp):
    # A dropped CAPE leg would leave the negated real yield; a dropped rate leg
    # would leave the raw CAPE yield. Both fall outside realized history.
    vs = [o["value"] for o in erp["observations"]]
    assert -4 < min(vs) < 0, min(vs)
    assert 5 < max(vs) < 12, max(vs)


def test_premium_went_negative_at_the_dot_com_peak(erp):
    # The defining feature of this chart: around the 2000 peak the CAPE yield
    # fell below the expected real bond yield. If no month is negative, the
    # sign convention has been inverted somewhere.
    by_date = {o["date"]: o["value"] for o in erp["observations"]}
    assert by_date["2000-01-01"] < 0
    assert min(by_date, key=by_date.get).startswith("2000-")


def test_premium_peaked_in_the_1982_trough(erp):
    # The other end: the highest premium in the series belongs to 1982, the
    # year the bull market began, not to a later date.
    by_date = {o["date"]: o["value"] for o in erp["observations"]}
    assert max(by_date, key=by_date.get).startswith("1982-")


# ── Cross-checks against fresh upstream pulls (network) ─────────────────────

@pytest.mark.network
def test_cape_leg_matches_fresh_shiller_pull(erp):
    """Recompute the CAPE yield for sampled months from Shiller's own file."""
    cape = fetch_cape()
    obs = erp["observations"]
    for o in (obs[0], obs[len(obs) // 2], obs[-1]):
        assert o["date"] in cape, f"{o['date']} missing from Shiller's workbook"
        assert abs((100.0 / cape[o["date"]]) - o["cape_yield"]) <= 0.02, o


@pytest.mark.network
@requires_fred_key
def test_real_yield_leg_matches_fresh_fred_pull(erp):
    """Recompute GS10 − EXPINF10YR for sampled months from FRED directly."""
    nominal = {x["date"]: x["value"] for x in fetch_series(NOMINAL_ID)}
    expected = {x["date"]: x["value"] for x in fetch_series(EXPECTED_INFLATION_ID)}
    obs = erp["observations"]
    for o in (obs[0], obs[len(obs) // 2], obs[-1]):
        assert abs((nominal[o["date"]] - expected[o["date"]]) - o["real_yield"]) <= 0.02, o


@pytest.mark.network
@requires_fred_key
def test_expinf_start_date_has_not_moved():
    """Canary. This series' own start date is derived from EXPINF10YR's, not
    asserted independently. If the Cleveland Fed ever backfills the model,
    EXPINF_START and the docstrings in scripts/fetch_equity_risk_premium.py
    and series/equity_risk_premium.json's methodology all need updating.
    """
    first = fetch_series(EXPECTED_INFLATION_ID, limit=1, sort_order="asc")[0]["date"]
    assert first == EXPINF_START, (
        f"{EXPECTED_INFLATION_ID} now starts {first}, not {EXPINF_START} — update "
        "EXPINF_START and the methodology text that explains the 1982 start"
    )


# ── The arithmetic itself, on synthetic input (no network) ──────────────────

def test_build_observations_drops_months_missing_a_leg():
    cape = {"2020-01-01": 25.0, "2020-02-01": 25.0, "2020-03-01": 25.0}
    nominal = {"2020-01-01": 2.0, "2020-02-01": 2.0}           # March missing
    expected = {"2020-01-01": 1.5, "2020-02-01": 1.5, "2020-03-01": 1.5}
    out = build_observations(cape, nominal, expected)
    assert [o["date"] for o in out] == ["2020-01-01", "2020-02-01"]
    # 100/25 = 4.00 CAPE yield; 2.0 - 1.5 = 0.50 real; premium 3.50
    assert out[0] == {
        "date": "2020-01-01", "value": 3.5, "cape_yield": 4.0, "real_yield": 0.5,
    }


def test_build_observations_never_forward_fills():
    # A gap stays a gap: the month after a missing one must not inherit it.
    cape = {"2020-01-01": 20.0, "2020-03-01": 20.0}
    nominal = {"2020-01-01": 3.0, "2020-02-01": 3.0, "2020-03-01": 3.0}
    expected = {"2020-01-01": 2.0, "2020-02-01": 2.0, "2020-03-01": 2.0}
    out = build_observations(cape, nominal, expected)
    assert [o["date"] for o in out] == ["2020-01-01", "2020-03-01"]
