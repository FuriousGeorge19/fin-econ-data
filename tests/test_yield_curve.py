"""Cross-check yield-curve tenors against a direct FRED DGS pull on fixed
dates. Requires network + FRED_API_KEY.
"""

import os

import pytest

from fred_utils import fetch_series

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)

# Dates chosen to exist in the committed yield_curve.json regardless of staleness.
SAMPLE_DATES = ["2015-06-15", "2018-01-02", "2022-09-01"]

TENOR_TO_FRED_ID = {
    "1mo": "DGS1MO", "3mo": "DGS3MO", "6mo": "DGS6MO", "1yr": "DGS1",
    "2yr": "DGS2", "3yr": "DGS3", "5yr": "DGS5", "7yr": "DGS7",
    "10yr": "DGS10", "20yr": "DGS20", "30yr": "DGS30",
}


@requires_fred_key
@pytest.mark.network
@pytest.mark.parametrize("date", SAMPLE_DATES)
def test_yield_curve_snapshot_matches_direct_fred_pull(yield_curve, date):
    ours = yield_curve["observations"].get(date)
    assert ours is not None, f"{date} missing from committed yield_curve.json"

    checked = 0
    for tenor, value in ours.items():
        fred_id = TENOR_TO_FRED_ID[tenor]
        # Pull just the observations around the target date rather than full
        # history — one FRED call per tenor per date, so keep the window tight.
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
