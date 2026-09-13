"""Cross-check computed spreads against FRED's own precomputed T10Y2Y / T10Y3M
on sampled dates. Requires network + FRED_API_KEY.
"""

import os

import pytest

from fred_utils import fetch_series

# Dates chosen to fall inside the committed spreads.json range (10y2y from
# 1976, 10y3m from 1982) regardless of how stale that file is.
SAMPLE_DATES = ["2015-06-15", "2020-01-15", "2023-03-01"]

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@requires_fred_key
@pytest.mark.network
@pytest.mark.parametrize("our_key,fred_series_id", [("10y2y", "T10Y2Y"), ("10y3m", "T10Y3M")])
def test_spread_matches_fred_precomputed_series(spreads, our_key, fred_series_id):
    ours = {o["date"]: o["value"] for o in spreads["series"][our_key]["observations"]}
    fred = {o["date"]: o["value"] for o in fetch_series(fred_series_id)}

    checked = 0
    for date in SAMPLE_DATES:
        if date not in ours or date not in fred:
            continue
        assert ours[date] == pytest.approx(fred[date], abs=0.01), (
            f"{our_key} {date}: ours={ours[date]} fred={fred[date]}"
        )
        checked += 1
    assert checked > 0, "none of the sample dates were present in both series"
