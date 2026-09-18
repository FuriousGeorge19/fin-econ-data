"""Correctness tests for breakeven_10y (S11b, roadmap chart 6): the 10-Year
Breakeven Inflation Rate (FRED T10YIE).

Structural checks need no network. The cross-check against a fresh FRED pull
needs network and FRED_API_KEY.
"""

import os

import pytest

from fred_utils import fetch_series

SERIES_START = "2003-01-02"

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@pytest.fixture
def breakeven_10y(load_data):
    return load_data("breakeven_10y")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_dates_unique_and_ascending(breakeven_10y):
    dates = [o["date"] for o in breakeven_10y["observations"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))


def test_no_missing_value_became_zero(breakeven_10y):
    # FRED's "." missing-value sentinel, if it ever slipped through, would
    # show up as an implausible 0% breakeven rate. A genuine 0.00% reading is
    # not impossible in principle, but T10YIE has never printed exactly zero;
    # this guards fred_utils's sentinel-dropping behavior, not the economics.
    assert all(o["value"] != 0 for o in breakeven_10y["observations"])


def test_values_are_plausible_percent(breakeven_10y):
    # Breakevens have ranged roughly -0.5% (deflation scare, 2008/2020) to
    # ~3.5% (2022 inflation spike); a much wider range would suggest a units
    # or parsing bug rather than genuine market pricing.
    for o in breakeven_10y["observations"]:
        assert -2.0 < o["value"] < 6.0, o


def test_starts_at_series_start(breakeven_10y):
    # Canary: fails BY NAME if FRED's T10YIE history start ever changes,
    # rather than silently truncating or extending the series.
    dates = [o["date"] for o in breakeven_10y["observations"]]
    assert dates[0] == SERIES_START, (
        f"breakeven_10y now starts {dates[0]}, not {SERIES_START} — "
        f"FRED's T10YIE history start has changed; check the fetcher and "
        f"this test's SERIES_START constant"
    )


def test_meta_and_presentation(breakeven_10y):
    meta = breakeven_10y["meta"]
    assert meta["id"] == "breakeven_10y"
    assert meta["cadence"] == "daily"
    assert meta["kind"] == "timeseries"
    # presentation/fetcher are build-time config, stripped before writing.
    assert "presentation" not in meta
    assert "fetcher" not in meta


def test_sources_resolved_from_catalogue(breakeven_10y):
    sources = breakeven_10y["meta"]["sources"]
    assert len(sources) == 1
    src = sources[0]
    assert src["slug"] == "fred"
    assert src["dataset"] == "breakevens"
    # Resolved fields come from the catalogue, never hand-written here.
    assert "name" in src
    assert "licence" in src
    assert "terms_status" in src


# ── Cross-check against a fresh pull (network) ──────────────────────────────

@requires_fred_key
@pytest.mark.network
def test_matches_fresh_fred_pull(breakeven_10y):
    fresh = {o["date"]: o["value"] for o in fetch_series("T10YIE")}
    ours = {o["date"]: o["value"] for o in breakeven_10y["observations"]}

    # Sample the oldest, middle and newest dates rather than the whole
    # ~6000-observation history.
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
def test_fetch_starts_at_series_start():
    fresh = fetch_series("T10YIE")
    assert fresh[0]["date"] == SERIES_START, (
        f"FRED T10YIE now starts {fresh[0]['date']}, not {SERIES_START} — "
        f"this test's SERIES_START constant needs updating"
    )
