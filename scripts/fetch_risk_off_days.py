"""Fetch inputs and compute the risk-off-day table (roadmap item 15).

For each calendar year (and the last 120 sessions): how many days the S&P 500
fell at least 1%, its average fall on those days, the average change in the
2, 5, 7 and 10-year Treasury yields and the share of those days each yield
fell, the estimated price move of an intermediate Treasury fund
(-4.9 x change in the 7yr yield), and the year's stock-bond correlation.
The "share of days the yield fell" is the hedge working. Writes
data/risk_off_days.json. See stock_bond.py for the definitions.
"""

import os
import sys
from datetime import date

from fred_utils import get_api_key
import stock_bond as sb

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "risk_off_days.json")
TENORS = ["2yr", "5yr", "7yr", "10yr"]


def main():
    if not get_api_key():
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    sp, yields = sb.fetch_pairs(TENORS)
    pairs = sb.daily_pairs(sp, yields, TENORS)
    if len(pairs) < sb.ROLLING_WINDOW:
        print("ERROR: too few paired sessions", file=sys.stderr)
        sys.exit(1)

    years = sorted({p["date"][:4] for p in pairs})
    current = str(date.fromisoformat(pairs[-1]["date"]).year)
    rows = []
    for y in years:
        row = sb.risk_off_stats([p for p in pairs if p["date"][:4] == y], TENORS)
        first_session = min(p["date"] for p in pairs if p["date"][:4] == y)
        # The first calendar year in the data starts mid-year (FRED's ten-year
        # window); label it so it is not read as a full year.
        partial = y == years[0] and first_session[5:] > "01-10"
        label = y + (" to date" if y == current else " (from " + first_session + ")" if partial else "")
        rows.append({"id": y, "label": label, **row})
    last = pairs[-sb.ROLLING_WINDOW:]
    rows.append({"id": "last120", "label": f"Last {sb.ROLLING_WINDOW} sessions",
                 **sb.risk_off_stats(last, TENORS)})

    sb.write_series(
        "risk_off_days", OUTPUT_PATH,
        {
            "tenors": TENORS,
            "threshold_pct": sb.RISK_OFF_THRESHOLD_PCT,
            "fund": {"duration_years": sb.FUND_DURATION_YEARS, "tenor": sb.FUND_TENOR},
            "rows": rows,
        },
        last_observation=pairs[-1]["date"], first_observation=pairs[0]["date"],
        observation_count=len(pairs),
        inputs={"sp500": {"last_observation": pairs[-1]["date"]},
                "treasury": {"last_observation": pairs[-1]["date"]}},
    )
    print(f"Wrote {len(rows)} rows, {len(pairs)} paired sessions to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
