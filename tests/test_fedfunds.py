"""Correctness tests for fedfunds: the effective federal funds rate, monthly
average, from FRED (FEDFUNDS).

Structural checks need no network. The cross-check against a fresh FRED pull
needs network and FRED_API_KEY. The canary fails by name if FRED's FEDFUNDS
series ever starts earlier than 1954-07-01.
"""

import os

import pytest

from fred_utils import fetch_series

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)

EXPECTED_START = "1954-07-01"


@pytest.fixture
def fedfunds(load_data):
    return load_data("fedfunds")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_dates_unique_and_ascending(fedfunds):
    dates = [o["date"] for o in fedfunds["observations"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))


def test_no_missing_value_became_zero(fedfunds):
    # FRED's "." missing-value sentinel, if it ever slipped through, would show
    # up as an implausible fed funds rate. A range guard rather than `> 0`: the
    # observed minimum is 0.05 (ZIRP), and a monthly average printing exactly
    # 0.00 in a future deep-ZIRP month is a legitimate value, not a sentinel.
    # The 1981 peak of 19.10 bounds the top.
    values = [o["value"] for o in fedfunds["observations"]]
    assert 0 <= min(values) < 1, min(values)
    assert 15 < max(values) < 25, max(values)


def test_dates_are_first_of_month(fedfunds):
    # Monthly cadence: every observation is dated the first of its month, and
    # no daily-cadence source ever got upsampled/interleaved in here.
    for o in fedfunds["observations"]:
        assert o["date"][8:10] == "01", o


def test_starts_1954_07(fedfunds):
    assert fedfunds["observations"][0]["date"] == EXPECTED_START


def test_meta_and_as_of_present(fedfunds):
    assert fedfunds["meta"]["id"] == "fedfunds"
    assert fedfunds["meta"]["cadence"] == "monthly"
    assert "as_of" in fedfunds
    assert fedfunds["as_of"]["last_observation"] == fedfunds["observations"][-1]["date"]
    assert fedfunds["as_of"]["first_observation"] == fedfunds["observations"][0]["date"]
    assert fedfunds["as_of"]["observation_count"] == len(fedfunds["observations"])


# ── Cross-check against a fresh pull (network) ──────────────────────────────

@requires_fred_key
@pytest.mark.network
def test_matches_fresh_fred_pull(fedfunds):
    fresh = {o["date"]: o["value"] for o in fetch_series("FEDFUNDS")}
    ours = {o["date"]: o["value"] for o in fedfunds["observations"]}

    # Sample the oldest, a middle date, and the newest rather than every
    # observation of a 70+ year monthly history.
    dates = sorted(ours)
    sample = {dates[0], dates[len(dates) // 2], dates[-1]}

    checked = 0
    for date in sample:
        if date not in fresh:
            continue
        assert ours[date] == pytest.approx(fresh[date], abs=0.01), date
        checked += 1
    assert checked > 0


@requires_fred_key
@pytest.mark.network
def test_fedfunds_starts_at_expected_date():
    # Canary: fails by name if FRED's FEDFUNDS ever starts earlier than
    # 1954-07-01, the assumption this chart's history/coverage is built on.
    fresh = fetch_series("FEDFUNDS")
    assert fresh[0]["date"] == EXPECTED_START, (
        f"FRED FEDFUNDS now starts {fresh[0]['date']}, not {EXPECTED_START} — "
        f"fedfunds's expected coverage start needs updating"
    )
