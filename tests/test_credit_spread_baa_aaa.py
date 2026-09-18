"""Correctness tests for credit_spread_baa_aaa: Moody's Baa-minus-Aaa monthly
corporate credit spread (roadmap chart 8, rescoped 2026-09-17 — see
scripts/fetch_credit_spread_baa_aaa.py and series/credit_spread_baa_aaa.json
for why this replaces the originally-scoped ICE BofA OAS version).

Structural checks need no network. The cross-check against a fresh FRED pull
needs network + FRED_API_KEY.
"""

import os

import pytest

from fetch_credit_spread_baa_aaa import compute_spread
from fred_utils import fetch_series

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)

# Both AAA and BAA (FRED's monthly Moody's series) are documented to start
# 1919-01 (checked via the FRED API /fred/series endpoint, 2026-09-17). If
# either series' start ever changes, this canary should fail by name rather
# than the structural tests below just quietly passing on a shorter history.
EXPECTED_START = "1919-01-01"


@pytest.fixture
def credit_spread(load_data):
    return load_data("credit_spread_baa_aaa")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_dates_unique_and_ascending(credit_spread):
    dates = [o["date"] for o in credit_spread["observations"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))


def test_dates_are_monthly(credit_spread):
    # Every date should be the first of its month (FRED's monthly-average
    # convention for AAA/BAA), and consecutive months should never repeat.
    for o in credit_spread["observations"]:
        assert o["date"].endswith("-01"), o


def test_no_missing_value_became_zero(credit_spread):
    # FRED's "." missing-value sentinel, if it ever slipped through, would
    # show up as an implausible 0pp spread (fred_utils already drops "." —
    # this guards against a future regression in that path).
    assert all(o["value"] != 0 for o in credit_spread["observations"])


def test_spread_strictly_positive_across_full_history(credit_spread):
    # Checked directly against the committed fixture (2026-09-17): the
    # minimum observed spread is +0.32pp (1966-01), never non-positive.
    # This is an empirical fact about this history, not a definitional
    # guarantee of the instrument — if a future fetch ever produces a
    # non-positive spread, that is real news (Baa yielding at or below
    # Aaa), and this test should fail loudly rather than be loosened.
    negative_or_zero = [o for o in credit_spread["observations"] if o["value"] <= 0]
    assert not negative_or_zero, (
        f"{len(negative_or_zero)} non-positive spread observation(s) found — "
        f"this is a genuine data event (Baa yield at or below Aaa), not a bug; "
        f"first: {negative_or_zero[0] if negative_or_zero else None}"
    )


def test_compute_spread_differences_correctly():
    aaa = [{"date": "2020-01-01", "value": 2.50}, {"date": "2020-02-01", "value": 2.60}]
    baa = [{"date": "2020-01-01", "value": 3.10}, {"date": "2020-02-01", "value": 3.30}]
    result = compute_spread(aaa, baa)
    assert result == [
        {"date": "2020-01-01", "value": 0.60},
        {"date": "2020-02-01", "value": 0.70},
    ]


def test_compute_spread_emits_only_shared_dates():
    aaa = [{"date": "2020-01-01", "value": 2.50}]
    baa = [{"date": "2020-01-01", "value": 3.10}, {"date": "2020-02-01", "value": 3.30}]
    result = compute_spread(aaa, baa)
    assert [o["date"] for o in result] == ["2020-01-01"]


# ── Cross-check against a fresh pull (network) ──────────────────────────────

@requires_fred_key
@pytest.mark.network
def test_spread_matches_fresh_fred_pull(credit_spread):
    fresh_aaa = {o["date"]: o["value"] for o in fetch_series("AAA")}
    fresh_baa = {o["date"]: o["value"] for o in fetch_series("BAA")}
    ours = {o["date"]: o["value"] for o in credit_spread["observations"]}

    dates = sorted(ours)
    sample = {dates[0], dates[len(dates) // 2], dates[-1]}

    checked = 0
    for date in sample:
        if date not in fresh_aaa or date not in fresh_baa:
            continue
        expected = round(fresh_baa[date] - fresh_aaa[date], 2)
        assert ours[date] == pytest.approx(expected, abs=0.01), date
        checked += 1
    assert checked > 0


@requires_fred_key
@pytest.mark.network
def test_aaa_and_baa_start_at_expected_date():
    aaa = fetch_series("AAA")
    baa = fetch_series("BAA")
    assert aaa[0]["date"] == EXPECTED_START, (
        f"FRED AAA now starts {aaa[0]['date']}, not {EXPECTED_START} — "
        f"credit_spread_baa_aaa's documented coverage needs updating"
    )
    assert baa[0]["date"] == EXPECTED_START, (
        f"FRED BAA now starts {baa[0]['date']}, not {EXPECTED_START} — "
        f"credit_spread_baa_aaa's documented coverage needs updating"
    )
