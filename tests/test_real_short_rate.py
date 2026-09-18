"""Correctness tests for real_short_rate (S11b, roadmap chart 5): the ex-post
real short rate, TB3MS minus the trailing year-over-year change in CPIAUCSL.

Structural checks need no network. The cross-check against a fresh FRED pull
needs network and FRED_API_KEY.
"""

import os

import pytest

from fetch_real_short_rate import compute_real_short_rate, compute_yoy_cpi, shift_month
from fred_utils import fetch_series

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@pytest.fixture
def real_short_rate(load_data):
    return load_data("real_short_rate")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_dates_unique_and_ascending(real_short_rate):
    dates = [o["date"] for o in real_short_rate["observations"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))


def test_monthly_spacing(real_short_rate):
    # Consecutive observations must be whole months apart, strictly
    # increasing - but not necessarily exactly one month, since a real
    # upstream gap (e.g. CPIAUCSL has no October 2025 observation, the
    # month BLS's data collection was disrupted by the government shutdown)
    # correctly produces a skipped month here rather than an interpolated
    # one. This asserts no interpolation slipped in, not that history has
    # no gaps.
    dates = [o["date"] for o in real_short_rate["observations"]]
    for prior, current in zip(dates, dates[1:]):
        gap = 1
        while shift_month(prior, gap) != current and gap <= 3:
            gap += 1
        assert shift_month(prior, gap) == current, (prior, current)


def test_first_observation_no_earlier_than_1948_01(real_short_rate):
    # The YoY CPI leg needs twelve months of CPI history behind it (CPI starts
    # 1947-01), so 1948-01 is the earliest possible month, regardless of
    # TB3MS's own much earlier 1934-01 start.
    assert real_short_rate["observations"][0]["date"] >= "1948-01-01"


def test_values_are_plausible_percentage_points(real_short_rate):
    # A real 0.00pp reading is legitimate, so "value != 0" is the wrong guard
    # here. What a dropped leg would actually look like is a value equal to
    # the negated CPI YoY change (TB3MS lost) or to the raw bill rate (CPI
    # lost) - both land far outside the range realized history has occupied.
    # Observed 1948-2026: min -9.27 (Jan 1948), max +6.88 (Aug 1983).
    values = [o["value"] for o in real_short_rate["observations"]]
    assert values, "no observations at all"
    assert -15.0 < min(values) < -5.0, f"implausible minimum {min(values)}"
    assert 3.0 < max(values) < 15.0, f"implausible maximum {max(values)}"


def test_shift_month_helper():
    assert shift_month("2026-08-01", -12) == "2025-08-01"
    assert shift_month("2026-01-01", -12) == "2025-01-01"
    assert shift_month("2020-01-01", -1) == "2019-12-01"
    assert shift_month("2020-01-01", 12) == "2021-01-01"


def test_compute_yoy_cpi_skips_gaps():
    cpi = {"2000-01-01": 100.0, "2001-01-01": 105.0, "2001-02-01": 106.0}
    yoy = compute_yoy_cpi(cpi)
    # 2000-01 has no month 12 back -> excluded; 2001-01 has 2000-01 -> included;
    # 2001-02 has no 2000-02 -> excluded (no interpolation across the gap).
    assert set(yoy) == {"2001-01-01"}
    assert yoy["2001-01-01"] == pytest.approx(5.0)


def test_compute_real_short_rate_only_where_both_legs_exist():
    tb3ms = {"2001-01-01": 5.0, "2001-02-01": 5.1}
    yoy_cpi = {"2001-01-01": 3.0}
    obs = compute_real_short_rate(tb3ms, yoy_cpi)
    assert obs == [{"date": "2001-01-01", "value": 2.0}]


# ── Known historical episodes (no network) ──────────────────────────────────
# The chart's stated reason for existing: these three episodes must actually
# show up as the loud outliers the descriptor's notes describe.

def test_late_1940s_financial_repression_is_deeply_negative(real_short_rate):
    by_date = {o["date"]: o["value"] for o in real_short_rate["observations"]}
    assert by_date["1948-01-01"] < -5.0


def test_mid_1970s_real_rate_is_negative(real_short_rate):
    by_date = {o["date"]: o["value"] for o in real_short_rate["observations"]}
    assert by_date["1975-01-01"] < 0


def test_early_1980s_volcker_shock_swings_sharply_positive(real_short_rate):
    by_date = {o["date"]: o["value"] for o in real_short_rate["observations"]}
    # The real rate should be markedly higher in 1982 (post-shock) than in
    # 1979 (pre-shock) - the disinflation-driven swing this chart is meant
    # to make visible, without pinning to one exact reading either side.
    assert by_date["1982-06-01"] - by_date["1979-06-01"] > 5.0


# ── Cross-check against a fresh pull (network) ──────────────────────────────

@requires_fred_key
@pytest.mark.network
def test_matches_fresh_fred_pull(real_short_rate):
    tb3ms = {o["date"]: o["value"] for o in fetch_series("TB3MS")}
    cpi = {o["date"]: o["value"] for o in fetch_series("CPIAUCSL")}
    yoy_cpi = compute_yoy_cpi(cpi)
    fresh = {o["date"]: o["value"] for o in compute_real_short_rate(tb3ms, yoy_cpi)}

    ours = {o["date"]: o["value"] for o in real_short_rate["observations"]}
    dates = sorted(ours)
    sample = {dates[0], dates[len(dates) // 2], dates[-1]}

    checked = 0
    for date in sample:
        if date not in fresh:
            continue
        assert ours[date] == pytest.approx(fresh[date], abs=0.02), date
        checked += 1
    assert checked > 0


@requires_fred_key
@pytest.mark.network
def test_input_series_start_dates_have_not_moved():
    """Canary: this series' own 1948-01 start is DERIVED from CPIAUCSL's
    1947-01 start plus the twelve months the year-over-year leg needs. If
    FRED ever extends CPIAUCSL earlier (or TB3MS later), the descriptor's
    methodology text and test_first_observation_no_earlier_than_1948_01
    both need updating - this fails by name when that happens."""
    cpi_start = fetch_series("CPIAUCSL", sort_order="asc", limit=1)[0]["date"]
    tb_start = fetch_series("TB3MS", sort_order="asc", limit=1)[0]["date"]
    assert cpi_start == "1947-01-01", (
        f"CPIAUCSL now starts {cpi_start}, not 1947-01-01 - the derived "
        "1948-01 start of real_short_rate needs updating in "
        "series/real_short_rate.json's methodology and in this test file."
    )
    assert tb_start == "1934-01-01", (
        f"TB3MS now starts {tb_start}, not 1934-01-01 - check whether it, "
        "rather than CPI, now binds this series' start date."
    )
