"""Correctness tests for gs10_long (S11a): the stitched Shiller pre-1953 /
FRED GS10 post-1953 series, and the per-observation source/frequency
metadata pattern it establishes.

Structural checks need no network. The two cross-checks against fresh pulls
(Shiller's own workbook, FRED's own GS10) need network; the FRED one also
needs FRED_API_KEY.
"""

import os

import pytest

from fetch_gs10_long import CUTOVER, SEAM_TOLERANCE, fetch_fred_gs10, fetch_shiller_long_rate
from fred_utils import fetch_series

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@pytest.fixture
def gs10_long(load_data):
    return load_data("gs10_long")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_dates_unique_and_ascending(gs10_long):
    dates = [o["date"] for o in gs10_long["observations"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))


def test_no_missing_value_became_zero(gs10_long):
    # FRED's "." missing-value sentinel, if it ever slipped through, would
    # show up as an implausible 0% long-term rate.
    assert all(o["value"] > 0 for o in gs10_long["observations"])


def test_every_observation_has_source_and_frequency(gs10_long):
    for o in gs10_long["observations"]:
        assert o["source"] in ("shiller", "fred"), o
        assert o["frequency"] == "monthly", o


def test_source_splits_exactly_at_cutover(gs10_long):
    # The per-observation source pattern this chart establishes: no
    # interleaving, no observation on the wrong side of its own leg's range.
    for o in gs10_long["observations"]:
        if o["date"] < CUTOVER:
            assert o["source"] == "shiller", o
        else:
            assert o["source"] == "fred", o


def test_seam_continuity(gs10_long):
    obs = gs10_long["observations"]
    shiller_leg = [o for o in obs if o["source"] == "shiller"]
    fred_leg = [o for o in obs if o["source"] == "fred"]
    assert shiller_leg and fred_leg
    diff = abs(shiller_leg[-1]["value"] - fred_leg[0]["value"])
    assert diff <= SEAM_TOLERANCE * 3, (
        f"Shiller {shiller_leg[-1]} vs FRED {fred_leg[0]}: diff {diff} — "
        f"a much larger gap than fetch time's own {SEAM_TOLERANCE}pp warning threshold "
        f"would suggest a genuine break in the series, not just a stale fixture"
    )


# ── Cross-checks against fresh pulls (network) ──────────────────────────────

@pytest.mark.network
def test_shiller_leg_matches_fresh_shiller_pull(gs10_long):
    fresh = {r["date"]: r["value"] for r in fetch_shiller_long_rate() if r["date"] < CUTOVER}
    ours = {o["date"]: o["value"] for o in gs10_long["observations"] if o["source"] == "shiller"}

    checked = 0
    for date, value in ours.items():
        if date not in fresh:
            continue
        assert value == pytest.approx(fresh[date], abs=0.01), date
        checked += 1
    assert checked > 0


@requires_fred_key
@pytest.mark.network
def test_fred_leg_matches_fresh_fred_pull(gs10_long):
    fresh = {o["date"]: o["value"] for o in fetch_series("GS10")}
    ours = {o["date"]: o["value"] for o in gs10_long["observations"] if o["source"] == "fred"}

    # Sample the oldest, middle and newest FRED-leg dates rather than every
    # one of ~880 months.
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
def test_fetch_fred_gs10_starts_at_cutover():
    fred_rows = fetch_fred_gs10()
    assert fred_rows[0]["date"] == CUTOVER, (
        f"FRED GS10 now starts {fred_rows[0]['date']}, not {CUTOVER} — "
        f"fetch_gs10_long.py's CUTOVER constant needs updating"
    )
