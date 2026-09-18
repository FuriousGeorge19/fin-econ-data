"""Shared computation for the three "is the bond hedge working?" series
(roadmap items 15-17): the risk-off-day table, the rolling stock-bond
correlation and the drawdown-window curve shift.

All three read daily S&P 500 closes (FRED SP500, a rolling ten years) and
daily Treasury constant-maturity yields (FRED DGS*), and pair them on dates
where both report. Everything is computed here at fetch time, in whole basis
points for yield changes, never in JS.

Sign convention, printed on the correlation chart: the correlation is between
the S&P's daily percentage return and the daily change in a Treasury *yield*.
Yields move opposite to bond prices, so a POSITIVE value means stocks and
yields fall together and bond prices rise on bad stock days (the hedge works);
a NEGATIVE value means bond prices fall with stocks. Most published
"stock-bond correlation" charts use bond returns, which reverses the sign.
"""

import math
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series

SP500_ID = "SP500"

# Treasury tenors (label -> FRED id). 1mo is left out: it is too short to
# stand in for a bond hedge, and DGS1MO starts in 2001 with sparse early data.
DGS = {
    "3mo": "DGS3MO", "6mo": "DGS6MO", "1yr": "DGS1", "2yr": "DGS2", "3yr": "DGS3",
    "5yr": "DGS5", "7yr": "DGS7", "10yr": "DGS10", "20yr": "DGS20", "30yr": "DGS30",
}

RISK_OFF_THRESHOLD_PCT = -1.0     # a "risk-off day": S&P fell at least 1%
FUND_DURATION_YEARS = 4.9         # VGIT (3-10yr Treasuries), used with the 7yr yield
FUND_TENOR = "7yr"
ROLLING_WINDOW = 120              # sessions
DRAWDOWN_MIN_PCT = 5.0            # smallest S&P peak-to-trough fall listed


def fetch_pairs(tenors):
    """Fetch SP500 and the given DGS tenors; return (sp, yields) where sp is
    {date: close} and yields is {tenor: {date: value}}, restricted to no
    common-date filtering yet (see returns_and_changes)."""
    sp = {o["date"]: o["value"] for o in fetch_series(SP500_ID)}
    yields = {t: {o["date"]: o["value"] for o in fetch_series(DGS[t])} for t in tenors}
    return sp, yields


def common_dates(sp, yields, tenors):
    """Dates on which the S&P and every named tenor all report, sorted."""
    dates = set(sp)
    for t in tenors:
        dates &= set(yields[t])
    return sorted(dates)


def daily_pairs(sp, yields, tenors):
    """One record per consecutive pair of common dates:
    {date, ret_pct, dy_bp: {tenor: bp}}. ret_pct is the S&P's percentage change
    from the previous common date; dy_bp the whole-bp yield change."""
    dates = common_dates(sp, yields, tenors)
    out = []
    for prev, cur in zip(dates, dates[1:]):
        out.append({
            "date": cur,
            "ret_pct": (sp[cur] / sp[prev] - 1) * 100,
            "dy_bp": {t: int(round((yields[t][cur] - yields[t][prev]) * 100)) for t in tenors},
        })
    return out


def pearson(xs, ys):
    """Pearson correlation, or None when either side has no variance."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def rolling_correlation(pairs, tenor, window=ROLLING_WINDOW):
    """[{date, value}] — correlation of S&P return with the tenor's yield change
    over the trailing `window` sessions, dated at the window's last session."""
    out = []
    for i in range(window, len(pairs) + 1):
        w = pairs[i - window:i]
        c = pearson([p["ret_pct"] for p in w], [p["dy_bp"][tenor] for p in w])
        if c is not None:
            out.append({"date": w[-1]["date"], "value": round(c, 4)})
    return out


def risk_off_stats(pairs, tenors):
    """Risk-off-day summary for a set of pairs: count, average S&P fall, per-tenor
    average yield change and share of days the yield fell, the estimated price
    move of an intermediate Treasury fund (-duration x change in the 7yr yield),
    and the stock-bond correlation over all the pairs (per tenor; 10yr also kept
    as correlation_10yr)."""
    days = [p for p in pairs if p["ret_pct"] <= RISK_OFF_THRESHOLD_PCT]
    row = {"sessions": len(pairs), "days": len(days)}
    corr = pearson([p["ret_pct"] for p in pairs], [p["dy_bp"]["10yr"] for p in pairs])
    row["correlation_10yr"] = None if corr is None else round(corr, 2)
    # Per tenor, over ALL sessions in the period (not only bad days).
    row["correlation"] = {
        t: (None if c is None else round(c, 2))
        for t in tenors
        for c in [pearson([p["ret_pct"] for p in pairs], [p["dy_bp"][t] for p in pairs])]
    }
    if not days:
        row.update({"avg_sp_fall_pct": None, "fund_move_pct": None, "by_tenor": {}})
        return row
    row["avg_sp_fall_pct"] = round(sum(p["ret_pct"] for p in days) / len(days), 2)
    row["fund_move_pct"] = round(
        -FUND_DURATION_YEARS * sum(p["dy_bp"][FUND_TENOR] for p in days) / len(days) / 100, 2)
    row["by_tenor"] = {
        t: {
            "avg_change_bp": round(sum(p["dy_bp"][t] for p in days) / len(days), 1),
            "share_fell_pct": round(100 * sum(1 for p in days if p["dy_bp"][t] < 0) / len(days)),
        }
        for t in tenors
    }
    return row


def drawdowns(sp, dates, min_pct=DRAWDOWN_MIN_PCT):
    """Peak-to-trough S&P falls of at least min_pct on the given (sorted) dates.
    A window runs from the running peak to the lowest close before the index
    regains that peak (or to the end of the data, marked `ongoing`)."""
    out = []
    peak_date = dates[0]
    trough_date = dates[0]
    for d in dates[1:]:
        if sp[d] >= sp[peak_date]:
            _close_window(out, sp, peak_date, trough_date, min_pct, ongoing=False)
            peak_date = trough_date = d
        elif sp[d] < sp[trough_date]:
            trough_date = d
    _close_window(out, sp, peak_date, trough_date, min_pct, ongoing=True)
    return out


def _close_window(out, sp, peak_date, trough_date, min_pct, ongoing):
    fall = (sp[trough_date] / sp[peak_date] - 1) * 100
    if fall <= -min_pct:
        out.append({"peak_date": peak_date, "trough_date": trough_date,
                    "sp_change_pct": round(fall, 1), "ongoing": ongoing})


def write_series(series_id, output_path, payload, *, last_observation, first_observation,
                 observation_count=None, inputs=None):
    """Assemble meta + as_of + payload and write the data file."""
    descriptor = series_meta.load(series_id)
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=last_observation,
        first_observation=first_observation,
        observation_count=observation_count,
        inputs=inputs,
        fetched_at=datetime.now(timezone.utc),
    )
    output = {"meta": series_meta.meta_from_descriptor(descriptor), "as_of": as_of, **payload}
    series_meta.write_json(output_path, output)
