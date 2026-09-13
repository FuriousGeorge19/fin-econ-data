"""Unit tests for scripts/fred_utils.py, no network required.

Mocks urlopen so these run identically with or without FRED_API_KEY set.
"""

import json
from unittest.mock import patch, MagicMock

import fred_utils


def _fake_response(payload):
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


def test_missing_value_sentinel_is_dropped_not_zeroed():
    payload = {
        "observations": [
            {"date": "2024-01-01", "value": "4.5"},
            {"date": "2024-01-02", "value": "."},
            {"date": "2024-01-03", "value": "4.6"},
        ]
    }
    with patch("fred_utils.urlopen", return_value=_fake_response(payload)):
        obs = fred_utils.fetch_series("DGS10", api_key="dummy")

    dates = [o["date"] for o in obs]
    assert "2024-01-02" not in dates
    assert len(obs) == 2
    assert all(isinstance(o["value"], float) for o in obs)


def test_observations_sorted_oldest_first():
    payload = {
        "observations": [
            {"date": "2024-01-03", "value": "4.6"},
            {"date": "2024-01-01", "value": "4.5"},
            {"date": "2024-01-02", "value": "4.55"},
        ]
    }
    with patch("fred_utils.urlopen", return_value=_fake_response(payload)):
        obs = fred_utils.fetch_series("DGS10", api_key="dummy")

    assert [o["date"] for o in obs] == ["2024-01-01", "2024-01-02", "2024-01-03"]


def test_missing_key_required_exits():
    import pytest

    with pytest.raises(SystemExit):
        fred_utils.fetch_series("DGS10", api_key="")


def test_missing_key_not_required_returns_empty():
    obs = fred_utils.fetch_series("DGS10", api_key="", required=False)
    assert obs == []
