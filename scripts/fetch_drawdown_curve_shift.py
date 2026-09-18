"""Fetch inputs and compute the drawdown-window curve shift (roadmap item 17).

Finds every peak-to-trough S&P 500 fall of at least 5% in the available ten
years and, for each, the change in every Treasury yield (3mo-30yr) between the
peak date and the trough date, in whole basis points. Yields that rose while
stocks fell are the hedge failing. Writes data/drawdown_curve_shift.json.
See stock_bond.py.
"""

import os
import sys

from fred_utils import get_api_key
import stock_bond as sb

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "drawdown_curve_shift.json")
TENORS = list(sb.DGS)


def main():
    if not get_api_key():
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    sp, yields = sb.fetch_pairs(TENORS)
    # Dates where the S&P and the 10yr both report (the bond market is shut on
    # some days stocks trade). A tenor missing on a window's end date is left
    # out of that window, never interpolated.
    sp_dates = sb.common_dates(sp, yields, ["10yr"])
    windows = []
    for w in sb.drawdowns(sp, sp_dates):
        changes = {}
        for t in TENORS:
            a, b = yields[t].get(w["peak_date"]), yields[t].get(w["trough_date"])
            if a is not None and b is not None:
                changes[t] = int(round((b - a) * 100))
        windows.append({**w, "changes_bp": changes})
    windows.sort(key=lambda w: w["peak_date"], reverse=True)
    if not windows:
        print("ERROR: no drawdown of at least 5% found", file=sys.stderr)
        sys.exit(1)
    sb.write_series(
        "drawdown_curve_shift", OUTPUT_PATH,
        {"tenors": TENORS, "min_drawdown_pct": sb.DRAWDOWN_MIN_PCT, "windows": windows},
        last_observation=sp_dates[-1], first_observation=sp_dates[0],
        observation_count=len(windows),
        inputs={"sp500": {"last_observation": sp_dates[-1]},
                "treasury": {"last_observation": sp_dates[-1]}},
    )
    print(f"Wrote {len(windows)} drawdown windows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
