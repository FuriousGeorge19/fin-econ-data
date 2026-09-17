"""Cross-check the Shiller-derived series against Shiller's own columns,
pulled fresh from shillerdata.com. Requires network.
"""

import pytest

from fetch_sp500_pe import (
    fetch_bytes,
    parse_shiller,
    resolve_shiller_xls_url,
    month_is_complete,
)
from staleness import today_eastern


@pytest.fixture(scope="module")
def fresh_shiller_rows():
    url = resolve_shiller_xls_url()
    rows = parse_shiller(fetch_bytes(url))
    today = today_eastern()
    return [r for r in rows if month_is_complete(r["date"], today)]


@pytest.mark.network
def test_confirmed_pe_matches_shiller_source(sp500_pe, fresh_shiller_rows):
    shiller_by_date = {r["date"]: r for r in fresh_shiller_rows}
    confirmed = {o["date"]: o for o in sp500_pe["observations"] if not o["estimated"]}
    assert confirmed, "no confirmed observations in sp500_pe.json"

    checked = 0
    for date, our_obs in confirmed.items():
        shiller = shiller_by_date.get(date)
        if shiller is None or shiller["earnings"] is None:
            continue
        assert our_obs["price"] == pytest.approx(shiller["price"], abs=0.01), date
        assert our_obs["earnings"] == pytest.approx(shiller["earnings"], abs=0.01), date
        assert our_obs["pe"] == pytest.approx(shiller["price"] / shiller["earnings"], abs=0.01), date
        checked += 1
    assert checked > 0


@pytest.mark.network
def test_cape_matches_shiller_source(load_data, fresh_shiller_rows):
    cape = load_data("sp500_cape")
    shiller_by_date = {r["date"]: r["cape"] for r in fresh_shiller_rows}

    checked = 0
    for o in cape["observations"]:
        shiller_value = shiller_by_date.get(o["date"])
        if shiller_value is None:
            continue
        assert o["value"] == pytest.approx(shiller_value, abs=0.01), o["date"]
        checked += 1
    assert checked > 0


@pytest.mark.network
def test_dividend_and_earnings_yield_match_shiller_source(load_data, fresh_shiller_rows):
    shiller_by_date = {r["date"]: r for r in fresh_shiller_rows}

    div_yield = load_data("sp500_dividend_yield")
    checked = 0
    for o in div_yield["observations"]:
        row = shiller_by_date.get(o["date"])
        if row is None or row["dividend"] is None:
            continue
        assert o["value"] == pytest.approx(row["dividend"] / row["price"] * 100, abs=0.01), o["date"]
        checked += 1
    assert checked > 0

    earn_yield = load_data("sp500_earnings_yield")
    checked = 0
    for o in earn_yield["observations"]:
        row = shiller_by_date.get(o["date"])
        if row is None or row["earnings"] is None:
            continue
        assert o["value"] == pytest.approx(row["earnings"] / row["price"] * 100, abs=0.01), o["date"]
        checked += 1
    assert checked > 0
