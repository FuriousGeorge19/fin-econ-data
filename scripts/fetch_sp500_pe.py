"""Fetch S&P 500 Trailing P/E Ratio, replicating multpl.com methodology.

Data pipeline (three sources, stitched together):

  1. HISTORICAL (1871 – last Shiller confirmed month):
     Robert Shiller / Yale ie_data.xls — confirmed monthly P and TTM E.
     Shiller's Excel is not always current; it often lags 1-2+ years.

  2. RECENT (first month after Shiller cutoff – last confirmed quarter):
     FRED SP500 monthly-average prices  +  TTM earnings from
     data/earnings_overrides.json (sourced from S&P Global quarterly
     scorecard). Marked estimated=False because the quarterly earnings
     are confirmed; only the monthly price is a rolling average.

  3. CURRENT (months after the last confirmed quarter in overrides):
     FRED SP500 monthly prices + forward-filled TTM from the most recent
     confirmed quarter. Marked estimated=True (earnings not yet reported).

Update cadence:
  - This script runs daily via GitHub Actions (prices always current).
  - earnings_overrides.json must be updated manually each earnings season
    (~4x/year) by refreshing data/earnings_overrides.json from the
    S&P Global quarterly scorecard (reference_resources/sp-500-eps-est.xlsx).
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

from fred_utils import fetch_series

SHILLER_URL   = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
OVERRIDES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "earnings_overrides.json")
OUTPUT_PATH    = os.path.join(os.path.dirname(__file__), "..", "data", "sp500_pe.json")


# ── Utilities ─────────────────────────────────────────────────────────────────

def fetch_bytes(url):
    req = Request(url, headers={"User-Agent": "joemirza-site/1.0"})
    try:
        with urlopen(req, timeout=60) as resp:
            return resp.read()
    except URLError as e:
        print(f"ERROR: {url}: {e}", file=sys.stderr)
        sys.exit(1)


def detect_excel_format(data_bytes):
    if data_bytes[:4] == b'\xd0\xcf\x11\xe0':
        return ".xls", "xlrd"
    elif data_bytes[:4] == b'PK\x03\x04':
        return ".xlsx", "openpyxl"
    return ".xls", "xlrd"


def parse_shiller_date(val):
    """1871.01 → '1871-01-01'"""
    try:
        year  = int(val)
        month = round((float(val) - year) * 100)
        month = max(1, min(12, month if month >= 1 else 1))
        return f"{year}-{month:02d}-01"
    except (ValueError, TypeError):
        return None


def next_month_str(date_str):
    """'2023-06-01' → '2023-07-01'"""
    y, m, _ = date_str.split("-")
    m = int(m) + 1
    y = int(y)
    if m > 12:
        m = 1
        y += 1
    return f"{y}-{m:02d}-01"


# ── Source 1: Shiller ─────────────────────────────────────────────────────────

def parse_shiller(data_bytes):
    import pandas as pd

    suffix, engine = detect_excel_format(data_bytes)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data_bytes)
        tmp = f.name

    try:
        raw = pd.read_excel(tmp, sheet_name="Data", header=None, engine=engine)
    finally:
        os.unlink(tmp)

    # Find header row (col 0 == "Date")
    header_row = None
    for i, row in raw.iterrows():
        if str(row.iloc[0]).strip().lower() == "date":
            header_row = i
            break
    if header_row is None:
        print("ERROR: 'Date' header not found in Shiller Excel.", file=sys.stderr)
        sys.exit(1)

    cols = [str(c).strip() if str(c) != "nan" else f"_col{i}"
            for i, c in enumerate(raw.iloc[header_row])]
    df = raw.iloc[header_row + 1:].copy()
    df.columns = cols
    df = df.reset_index(drop=True)

    for req in ("Date", "P", "E"):
        if req not in df.columns:
            print(f"ERROR: Column '{req}' missing. Got: {list(df.columns)}", file=sys.stderr)
            sys.exit(1)

    df = df[pd.to_numeric(df["Date"], errors="coerce").notna()].copy()
    df["Date"] = pd.to_numeric(df["Date"])
    df["P"]    = pd.to_numeric(df["P"], errors="coerce")
    df["E"]    = pd.to_numeric(df["E"], errors="coerce")
    df = df[df["P"].notna() & (df["P"] > 0)].copy()

    # Keep only confirmed rows (Shiller has actual TTM earnings)
    observations = []
    for _, row in df.iterrows():
        date_str = parse_shiller_date(row["Date"])
        if date_str is None:
            continue
        if not (pd.notna(row["E"]) and float(row["E"]) > 0):
            continue  # skip estimated/blank earnings — we'll fill from overrides

        price    = float(row["P"])
        earnings = float(row["E"])
        observations.append({
            "date":      date_str,
            "price":     round(price, 2),
            "earnings":  round(earnings, 2),
            "pe":        round(price / earnings, 2),
            "estimated": False,
        })

    return observations


# ── Source 2: Earnings overrides (S&P Global quarterly) ──────────────────────

def load_overrides():
    """
    Returns a sorted list of dicts:
      [{"effective_from": "YYYY-MM-01", "ttm_eps": float, "quarter_end": str}, ...]
    sorted oldest → newest by effective_from.
    """
    if not os.path.exists(OVERRIDES_PATH):
        print(f"WARNING: {OVERRIDES_PATH} not found — skipping overrides.", file=sys.stderr)
        return []
    with open(OVERRIDES_PATH) as f:
        data = json.load(f)
    entries = sorted(data.get("entries", []), key=lambda e: e["effective_from"])
    return entries


def get_ttm_for_month(date_str, overrides):
    """
    Return (ttm_eps, is_estimated) for a given month date string.
    Finds the most recent override whose effective_from <= date_str.
    is_estimated = True if date_str >= the effective_from of the NEXT quarter
    that hasn't been confirmed yet (i.e., beyond the last entry).
    """
    applicable = None
    for entry in overrides:
        if entry["effective_from"] <= date_str:
            applicable = entry
        else:
            break
    if applicable is None:
        return None, True

    # If date_str is at or after the effective_from of the last entry,
    # the earnings are confirmed (the quarter is fully reported); the P/E
    # is "estimated" only if there's no confirmed quarter covering this month.
    # Since overrides only contain confirmed quarters, any month reachable by
    # an override is using confirmed earnings → estimated=False.
    # Months PAST the last override's effective_from but with no newer override
    # are also covered by the last override → estimated=True (forward-filled).
    last_entry = overrides[-1]
    is_estimated = date_str >= last_entry["effective_from"]
    # Actually: if applicable IS the last entry, we're forward-filling → estimated
    # If applicable is NOT the last entry, earnings are confirmed for this month
    if applicable["effective_from"] == last_entry["effective_from"]:
        is_estimated = True
    else:
        is_estimated = False

    return applicable["ttm_eps"], is_estimated


# ── Source 3: FRED SP500 monthly prices ──────────────────────────────────────

def fetch_fred_prices(start_date):
    """Fetch FRED SP500 monthly average prices from start_date onward.

    FRED is a secondary source here (the primary is Shiller), so this degrades
    gracefully via fetch_series(required=False): a missing key or failed request
    yields no prices and the series falls back to Shiller-only.
    """
    obs = fetch_series(
        "SP500",
        sort_order=None,
        extra_params={
            "frequency": "m",
            "aggregation_method": "avg",
            "observation_start": start_date,
        },
        required=False,
    )

    prices = {}
    for o in obs:
        y, m, _ = o["date"].split("-")
        prices[f"{y}-{m}-01"] = o["value"]  # {month_str: avg_price}

    return prices


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # ── 1. Shiller historical ─────────────────────────────────────────────────
    print("Fetching Shiller data from Yale University...")
    shiller_bytes = fetch_bytes(SHILLER_URL)
    print(f"  Downloaded {len(shiller_bytes):,} bytes")

    shiller_obs = parse_shiller(shiller_bytes)
    if not shiller_obs:
        print("ERROR: No Shiller observations parsed.", file=sys.stderr)
        sys.exit(1)

    last_shiller_date = shiller_obs[-1]["date"]
    print(f"  Shiller confirmed: {shiller_obs[0]['date']} → {last_shiller_date} ({len(shiller_obs)} months)")

    # ── 2. Load earnings overrides ────────────────────────────────────────────
    overrides = load_overrides()
    if overrides:
        print(f"  Overrides loaded: {overrides[0]['quarter_end']} → {overrides[-1]['quarter_end']} ({len(overrides)} quarters)")
    last_override_eff = overrides[-1]["effective_from"] if overrides else None

    # ── 3. Fetch FRED prices for everything after Shiller ─────────────────────
    fred_start = next_month_str(last_shiller_date)
    print(f"Fetching FRED SP500 monthly prices from {fred_start}...")
    fred_prices = fetch_fred_prices(fred_start)
    if fred_prices:
        sorted_dates = sorted(fred_prices)
        print(f"  FRED prices: {sorted_dates[0]} → {sorted_dates[-1]} ({len(fred_prices)} months)")

    # ── 4. Build observations for post-Shiller months ─────────────────────────
    extension = []
    if overrides and fred_prices:
        for month_str in sorted(fred_prices):
            price = fred_prices[month_str]
            ttm, estimated = get_ttm_for_month(month_str, overrides)
            if ttm is None:
                # No override covers this month at all — use last Shiller earnings
                ttm = shiller_obs[-1]["earnings"]
                estimated = True

            extension.append({
                "date":      month_str,
                "price":     round(price, 2),
                "earnings":  round(ttm, 2),
                "pe":        round(price / ttm, 2),
                "estimated": estimated,
            })

    observations = shiller_obs + extension

    # ── 5. Summary ────────────────────────────────────────────────────────────
    confirmed = [o for o in observations if not o["estimated"]]
    estimated = [o for o in observations if o["estimated"]]
    last_confirmed_ttm = confirmed[-1]["earnings"] if confirmed else None

    output = {
        "series_id":   "SP500_PE",
        "title":       "S&P 500 P/E Ratio (Trailing Twelve Months, As-Reported)",
        "units":       "Ratio",
        "frequency":   "Monthly",
        "source":      "Robert Shiller / Yale (ie_data.xls) + S&P Global quarterly EPS + FRED SP500",
        "methodology": (
            "P/E = monthly average S&P 500 price / trailing 12-month as-reported (GAAP) EPS. "
            "Historical data from Shiller/Yale (confirmed). "
            "Recent months use S&P Global quarterly earnings (data/earnings_overrides.json) "
            "with FRED SP500 monthly-average prices. "
            "Months after the last confirmed quarterly report use forward-filled earnings "
            "and are marked estimated=true."
        ),
        "last_updated":     datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "last_ttm_earnings": last_confirmed_ttm,
        "observations":     observations,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(observations)} total observations → {OUTPUT_PATH}")
    print(f"  Confirmed: {len(confirmed)}  |  Estimated: {len(estimated)}")
    print(f"  Full range: {observations[0]['date']} → {observations[-1]['date']}")
    print(f"  Latest P/E:       {observations[-1]['pe']:.1f}x  (price: {observations[-1]['price']:,.2f})")
    print(f"  Current TTM EPS:  {observations[-1]['earnings']:.2f}  (last confirmed: {last_confirmed_ttm})")


if __name__ == "__main__":
    main()
