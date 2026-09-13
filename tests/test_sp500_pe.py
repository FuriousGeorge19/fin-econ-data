"""Cross-check the Shiller-only era of the P/E series against Shiller's own
P and E columns, pulled fresh from Yale. Requires network.
"""

import pytest

from fetch_sp500_pe import fetch_bytes, parse_shiller, SHILLER_URL


@pytest.mark.network
def test_shiller_era_matches_shiller_source(sp500_pe):
    shiller_obs = {o["date"]: o for o in parse_shiller(fetch_bytes(SHILLER_URL))}
    assert shiller_obs, "Shiller parse returned no observations"

    last_shiller_date = max(shiller_obs)
    ours = {o["date"]: o for o in sp500_pe["observations"] if o["date"] <= last_shiller_date}
    assert ours, "no committed observations fall inside the Shiller-only era"

    checked = 0
    for date, our_obs in ours.items():
        shiller = shiller_obs.get(date)
        if shiller is None:
            continue
        assert our_obs["price"] == pytest.approx(shiller["price"], abs=0.01), date
        assert our_obs["earnings"] == pytest.approx(shiller["earnings"], abs=0.01), date
        assert our_obs["pe"] == pytest.approx(shiller["pe"], abs=0.01), date
        checked += 1
    assert checked > 0
