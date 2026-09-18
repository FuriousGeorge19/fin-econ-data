"""Correctness tests for rate_decomposition (S11e, roadmap item 14): the split
of each Treasury yield change into real yield and breakeven inflation.

Structural checks need no network; the cross-check against FRED needs network
+ FRED_API_KEY.
"""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import fetch_rate_decomposition as fetcher  # noqa: E402
from fred_utils import fetch_series  # noqa: E402

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@pytest.fixture
def decomp(load_data):
    return load_data("rate_decomposition")


# ── Pure functions (no data file, no network) ───────────────────────────────

def test_add_months_clamps_the_day():
    assert fetcher.add_months(date(2026, 3, 31), -1) == date(2026, 2, 28)
    assert fetcher.add_months(date(2024, 3, 31), -1) == date(2024, 2, 29)
    assert fetcher.add_months(date(2026, 1, 15), -12) == date(2025, 1, 15)


def test_ytd_target_is_the_prior_year_end():
    assert fetcher.target_date("ytd", date(2026, 9, 17)) == date(2025, 12, 31)


def test_decompose_reconciles_and_rounds_legs_first():
    row = lambda n, r: {t["id"]: {"nominal": n, "real": r} for t in fetcher.TENORS}  # noqa: E731
    out = fetcher.decompose(row(4.87, 2.11), row(4.71, 1.66))
    assert out["10Y"] == {"nominal_bp": 16, "real_bp": 45, "breakeven_bp": -29}


def test_only_dates_where_every_series_reports_are_used():
    ids = [t[k] for t in fetcher.TENORS for k in ("nominal", "real")]
    series = {sid: {"2026-01-02": 4.0, "2026-01-05": 4.1} for sid in ids}
    del series["DFII30"]["2026-01-05"]
    assert list(fetcher.build_rows(series)) == ["2026-01-02"]


# ── Structural invariants on the committed data file ────────────────────────

def test_every_change_reconciles_exactly(decomp):
    for p in decomp["periods"]:
        for t in decomp["tenors"]:
            c = p["changes"][t]
            assert c["nominal_bp"] == c["real_bp"] + c["breakeven_bp"], (p["id"], t)


def test_latest_levels_reconcile(decomp):
    for t, lv in decomp["latest"]["levels"].items():
        assert lv["breakeven"] == pytest.approx(lv["nominal"] - lv["real"], abs=0.005), t


def test_reference_dates_precede_latest_and_are_ordered(decomp):
    latest = decomp["latest"]["date"]
    refs = {p["id"]: p["ref_date"] for p in decomp["periods"]}
    assert all(r < latest for r in refs.values())
    assert refs["1w"] > refs["1m"] > refs["1y"]
    assert refs["ytd"] <= f"{int(latest[:4]) - 1}-12-31"


# ── Cross-check against a direct FRED pull ──────────────────────────────────

@requires_fred_key
@pytest.mark.network
def test_latest_levels_match_direct_fred_pull(decomp):
    latest = decomp["latest"]["date"]
    for t in fetcher.TENORS:
        for key in ("nominal", "real"):
            obs = fetch_series(t[key], extra_params={"observation_start": latest, "observation_end": latest})
            assert obs, f"{t[key]} has no value on {latest}"
            assert decomp["latest"]["levels"][t["id"]][key] == pytest.approx(obs[0]["value"], abs=0.005)
