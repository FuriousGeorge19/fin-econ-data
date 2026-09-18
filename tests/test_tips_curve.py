"""Correctness tests for tips_curve (S11b, roadmap chart 10): the TIPS real
yield curve snapshot.

Structural checks need no network. The cross-check against a fresh FRED pull
needs network + FRED_API_KEY. A canary fails by name if any tenor's start
date on FRED ever moves earlier than what this fetcher was built against.
"""

import os

import pytest

from fred_utils import fetch_series

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)

TENORS = ["5yr", "7yr", "10yr", "20yr", "30yr"]

TENOR_TO_FRED_ID = {
    "5yr": "DFII5", "7yr": "DFII7", "10yr": "DFII10",
    "20yr": "DFII20", "30yr": "DFII30",
}

# Observed start dates as of 2026-09-17 (checked live against FRED at fetch
# time, not assumed) — see this series' methodology/notes in
# series/tips_curve.json for the full finding.
EXPECTED_START_DATES = {
    "5yr": "2003-01-02",
    "7yr": "2003-01-02",
    "10yr": "2003-01-02",
    "20yr": "2004-07-27",
    "30yr": "2010-02-22",
}

# Dates chosen to exist in the committed tips_curve.json regardless of
# staleness, and to sit after every tenor (including 30yr) has started.
SAMPLE_DATES = ["2015-06-15", "2018-01-02", "2022-09-01"]


@pytest.fixture
def tips_curve(load_data):
    return load_data("tips_curve")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_shape_matches_yield_curve_convention(tips_curve):
    for key in ("meta", "as_of", "tenors", "tenor_months", "observations"):
        assert key in tips_curve
    assert tips_curve["tenors"] == TENORS
    assert tips_curve["tenor_months"] == {
        "5yr": 60, "7yr": 84, "10yr": 120, "20yr": 240, "30yr": 360,
    }


def test_dates_ascending_and_unique(tips_curve):
    dates = list(tips_curve["observations"].keys())
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))


def test_values_are_plausible_real_yields(tips_curve):
    # Unlike nominal rates, a TIPS real yield legitimately crosses zero (it
    # did across most of the curve in 2020-2021), so "value == 0" is not
    # itself a sign of a dropped FRED "." sentinel here — fred_utils already
    # strips that sentinel before a value ever reaches this file, since a
    # "." row is omitted from fetch_series's output entirely rather than
    # converted to 0. This checks a plausible range instead.
    for obs in tips_curve["observations"].values():
        for tenor, value in obs.items():
            assert -5 < value < 15, (tenor, obs)


def test_every_observation_has_at_least_one_tenor(tips_curve):
    for date, obs in tips_curve["observations"].items():
        assert obs, f"{date} has an empty observation — should be absent entirely"
        assert set(obs.keys()) <= set(TENORS)


def test_no_tenor_reports_before_its_own_start_date(tips_curve):
    # The core "make the gap visible, don't interpolate" invariant: a tenor
    # never appears in an observation dated before its own first_observation.
    starts = {t: tips_curve["as_of"]["series"][t]["first_observation"] for t in TENORS}
    for date, obs in tips_curve["observations"].items():
        for tenor in obs:
            assert date >= starts[tenor], (
                f"{tenor} reported on {date}, before its own start {starts[tenor]}"
            )


def test_tenor_start_dates_not_later_than_observed(tips_curve):
    # A tenor's *first* observation should be no later than what's recorded
    # here at test-writing time; earlier is fine (more history since), later
    # would mean the fixture is stale in a way that hides a real gap.
    starts = {t: tips_curve["as_of"]["series"][t]["first_observation"] for t in TENORS}
    for tenor, expected in EXPECTED_START_DATES.items():
        assert starts[tenor] <= expected, (
            f"{tenor} now starts {starts[tenor]}, later than the {expected} this "
            f"fetcher was built against — investigate before trusting the chart's gap"
        )


def test_30yr_starts_later_than_5yr_and_10yr(tips_curve):
    # The specific finding this chart's notes call out: 30yr TIPS were
    # reintroduced well after 5yr/7yr/10yr existed.
    starts = {t: tips_curve["as_of"]["series"][t]["first_observation"] for t in TENORS}
    assert starts["30yr"] > starts["10yr"]
    assert starts["30yr"] > starts["5yr"]


# ── Cross-check against a fresh pull (network) ──────────────────────────────

@requires_fred_key
@pytest.mark.network
@pytest.mark.parametrize("date", SAMPLE_DATES)
def test_tips_curve_snapshot_matches_direct_fred_pull(tips_curve, date):
    ours = tips_curve["observations"].get(date)
    assert ours is not None, f"{date} missing from committed tips_curve.json"

    checked = 0
    for tenor, value in ours.items():
        fred_id = TENOR_TO_FRED_ID[tenor]
        window = fetch_series(
            fred_id,
            sort_order=None,
            extra_params={"observation_start": date, "observation_end": date},
        )
        if not window:
            continue  # e.g. weekend/holiday gap already reflected in fixture
        assert window[0]["value"] == pytest.approx(value, abs=0.01), (
            f"{date} {tenor}: ours={value} fred={window[0]['value']}"
        )
        checked += 1
    assert checked > 0, f"no tenors for {date} could be verified against FRED"


@requires_fred_key
@pytest.mark.network
def test_fred_tenor_start_dates_have_not_moved_earlier():
    # Canary: fails by name if FRED ever backfills history earlier than what
    # this series' notes and EXPECTED_START_DATES record, which would mean
    # the "make gaps visible" logic above is now hiding real history.
    for tenor, fred_id in TENOR_TO_FRED_ID.items():
        rows = fetch_series(fred_id, sort_order="asc", limit=1)
        assert rows, f"{fred_id} returned no observations at all"
        actual_start = rows[0]["date"]
        expected = EXPECTED_START_DATES[tenor]
        assert actual_start >= expected, (
            f"{fred_id} ({tenor}) now starts {actual_start}, earlier than the "
            f"{expected} recorded in tests/test_tips_curve.py's "
            f"EXPECTED_START_DATES — update the constant and check series/"
            f"tips_curve.json's notes for the same claim"
        )
