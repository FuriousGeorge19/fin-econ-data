"""Correctness tests for tenor_history (S11c, roadmap chart 9).

tenor_history is the repo's first VIEW: a descriptor that draws another
series' data file (`presentation.data: "yield_curve"`) instead of owning one.
It has no fetcher and no `data/tenor_history.json`, so these tests assert the
view wiring and the facts its user-facing prose claims — read from
`data/yield_curve.json`, which is what the page actually fetches.

The gap facts here exist because the descriptor and CLAUDE.md both carried a
wrong one until 2026-09-17 (see test_the_only_long_gap_is_the_20_year_one).
"""

import os

import pytest

import series_meta

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)

VIEW_ID = "tenor_history"
SOURCE_ID = "yield_curve"

# Verified against a fresh FRED pull on 2026-09-17. The descriptor's
# methodology states these to the reader, so they are assertions, not notes.
TENOR_STARTS = {
    "1yr": "1962-01-02", "3yr": "1962-01-02", "5yr": "1962-01-02",
    "10yr": "1962-01-02", "20yr": "1962-01-02",
    "7yr": "1969-07-01", "2yr": "1976-06-01", "30yr": "1977-02-15",
    "3mo": "1981-09-01", "6mo": "1981-09-01", "1mo": "2001-07-31",
}
# DGS20's real suspension: last value before it, first value after it.
DGS20_GAP = ("1986-12-31", "1993-10-01")


@pytest.fixture
def source(load_data):
    return load_data(SOURCE_ID)


# ── The view wiring ─────────────────────────────────────────────────────────

def test_is_a_view_of_yield_curve():
    assert series_meta.is_view(VIEW_ID)
    assert series_meta.data_id(VIEW_ID) == SOURCE_ID


def test_owns_no_data_file_or_fetcher():
    # The whole point: no second multi-megabyte copy of the same numbers.
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert not os.path.exists(os.path.join(repo, "data", f"{VIEW_ID}.json"))
    assert not os.path.exists(os.path.join(repo, "scripts", f"fetch_{VIEW_ID}.py"))
    assert "fetcher" not in series_meta.load(VIEW_ID)


def test_source_series_owns_its_data():
    # A view of a view would leave the fetch chain unresolvable at build time;
    # build_site rejects it, and this asserts the real pair is not one.
    assert not series_meta.is_view(SOURCE_ID)


def test_configured_tenors_all_exist_in_the_payload(source):
    chart = series_meta.load(VIEW_ID)["presentation"]["chart"]
    for key in ("tenors", "default_tenors", "stat_tenors"):
        for tenor in chart[key]:
            assert tenor in source["tenors"], f"{key}: {tenor!r} not in {SOURCE_ID}"


# ── The facts the descriptor's prose asserts to the reader ──────────────────

@pytest.mark.parametrize("tenor,expected", sorted(TENOR_STARTS.items()))
def test_tenor_start_dates_match_the_methodology(tenor, expected, source):
    dates = sorted(source["observations"])
    first = next(d for d in dates if tenor in source["observations"][d])
    assert first == expected, (
        f"{tenor} now starts {first}, not {expected} — series/tenor_history.json's "
        "methodology names these start dates to the reader and needs updating"
    )


def test_the_only_long_gap_is_the_20_year_one(source):
    """Regression guard on a claim that was wrong for months.

    Both series/yield_curve.json and CLAUDE.md's chart conventions recorded a
    "2002-2006 tenor gap" in DGS20. That is the 30-YEAR bond's suspension
    period attached to the 20-YEAR tenor, and neither series actually has a gap
    there. It survived because a 6300-row fetch cap held this series' history
    back to roughly 2002, putting the real 1987-1993 gap outside the window
    entirely. Corrected 2026-09-17.
    """
    dates = sorted(source["observations"])
    gaps = {}
    for tenor in source["tenors"]:
        present = [d for d in dates if tenor in source["observations"][d]]
        found = []
        for a, b in zip(present, present[1:]):
            ya, ma = int(a[:4]), int(a[5:7])
            yb, mb = int(b[:4]), int(b[5:7])
            if (yb - ya) * 12 + (mb - ma) >= 6:
                found.append((a, b))
        if found:
            gaps[tenor] = found

    assert gaps == {"20yr": [list(DGS20_GAP)]} or gaps == {"20yr": [DGS20_GAP]}, (
        f"interior gaps changed: {gaps}. The descriptor and CLAUDE.md both describe "
        "exactly one long gap (DGS20, 1987-01 to 1993-09); update them together."
    )


def test_thirty_year_has_no_gap_across_the_2002_2006_suspension(source):
    """Treasury suspended 30-year issuance Feb 2002 - Feb 2006, but FRED's
    DGS30 reports continuously through it. This is the specific fact the old
    wrong note got backwards, so it is asserted directly."""
    obs = source["observations"]
    for date in ("2002-03-15", "2003-06-16", "2004-06-15", "2005-06-15"):
        assert "30yr" in obs.get(date, {}), f"DGS30 missing on {date}"


def test_history_reaches_1962(source):
    # The view's title says "(1962-Present)". If the fetch cap ever comes back,
    # the title becomes a lie and this fails first.
    assert sorted(source["observations"])[0] == "1962-01-02"
