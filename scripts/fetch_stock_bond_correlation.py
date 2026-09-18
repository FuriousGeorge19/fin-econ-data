"""Fetch inputs and compute the rolling stock-bond correlation (roadmap item 16).

Trailing 120-session correlation between the S&P 500's daily percentage return
and the daily change in the 10-year Treasury yield, one point per session from
the 120th onward. Positive = stocks and yields fall together, so bond prices
rise on bad stock days (the hedge works); negative = no hedge. Writes
data/stock_bond_correlation.json as a timeseries payload. See stock_bond.py.
"""

import os
import sys

from fred_utils import get_api_key
import stock_bond as sb

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stock_bond_correlation.json")


def main():
    if not get_api_key():
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    sp, yields = sb.fetch_pairs(["10yr"])
    pairs = sb.daily_pairs(sp, yields, ["10yr"])
    observations = sb.rolling_correlation(pairs, "10yr")
    if not observations:
        print("ERROR: too few paired sessions for a rolling correlation", file=sys.stderr)
        sys.exit(1)
    sb.write_series(
        "stock_bond_correlation", OUTPUT_PATH,
        {"window_sessions": sb.ROLLING_WINDOW, "observations": observations},
        last_observation=observations[-1]["date"], first_observation=observations[0]["date"],
        observation_count=len(observations),
        inputs={"sp500": {"last_observation": pairs[-1]["date"]},
                "treasury": {"last_observation": pairs[-1]["date"]}},
    )
    print(f"Wrote {len(observations)} observations to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
