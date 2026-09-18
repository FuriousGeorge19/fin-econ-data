"""Fetch S&P 500 Trailing P/E Ratio, CAPE, dividend yield and earnings yield,
all derived from one Shiller/Yale workbook download.

Data pipeline for sp500_pe (two sources, stitched together):

  1. CONFIRMED (1871 - Shiller's last confirmed quarter):
     Robert Shiller's ie_data.xls, read from the maintained shillerdata.com
     copy (not the frozen Yale mirror - see catalog/sources/shiller.json).
     Shiller interpolates monthly TTM price/dividends/earnings between
     quarter-end anchors, so every month through his last confirmed quarter
     is treated as confirmed, matching his own construction.

  2. ESTIMATED, one calendar quarter only (the month after that quarter -
     +3 months): TTM earnings held flat at the last confirmed quarter's
     value (Shiller hasn't anchored the next quarter yet), paired with
     Shiller's own price where he already has it, else FRED's SP500 monthly
     average. Beyond that one-quarter grace window the series stops rather
     than forward-filling an increasingly stale earnings figure indefinitely
     (data/earnings_overrides.json's mistake through 2026-09: an eleven-month
     forward-fill overstated the P/E by 26%).

data/earnings_overrides.json (S&P Global's quarterly scorecard, discontinued
by its publisher 31 Jan 2026) is no longer used to compute the series -
Shiller's own earnings column reaches nearly as current and updates itself.
It is kept only as a cross-check, logged at fetch time.

sp500_cape, sp500_dividend_yield and sp500_earnings_yield read straight off
Shiller's own CAPE/D/E columns with no forward-fill of any kind: a month
appears once Shiller publishes it, and not before. All three, like sp500_pe,
are unpublished (presentation.publish: false) - see catalog/CLAUDE.md
on Shiller's `unknown` terms.

Update cadence: this script runs daily via GitHub Actions. shillerdata.com's
`ie_data.xls` download link carries a `?ver=` cache-busting tag that changes,
so it is read from the page's HTML on every run rather than hard-coded.
"""

import calendar
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

import series_meta
from fred_utils import fetch_series
from staleness import today_eastern

SHILLER_PAGE_URL = "https://shillerdata.com/"
OVERRIDES_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "earnings_overrides.json")
DATA_DIR         = os.path.join(os.path.dirname(__file__), "..", "data")

SIMPLE_SERIES_IDS = ("sp500_cape", "sp500_dividend_yield", "sp500_earnings_yield")


# ── Utilities ─────────────────────────────────────────────────────────────────

def fetch_bytes(url):
    req = Request(url, headers={"User-Agent": "joemirza-site/1.0"})
    try:
        with urlopen(req, timeout=60) as resp:
            return resp.read()
    except URLError as e:
        print(f"ERROR: {url}: {e}", file=sys.stderr)
        sys.exit(1)


def resolve_shiller_xls_url(page_url=SHILLER_PAGE_URL):
    """Find the current ie_data.xls download link on shillerdata.com. The
    link's `?ver=<timestamp>` cache-busting tag changes over time (observed
    changing between S9 and S9b), so it must be read from the page's HTML -
    catalog/sources/shiller.json's access notes name the anchor
    (`data-aid="DOWNLOAD_DOCUMENT_LINK_RENDERED"`) to look for if this regex
    ever stops matching."""
    html = fetch_bytes(page_url).decode("utf-8", errors="replace")
    m = re.search(r'href="([^"]*ie_data\.xls\?ver=\d+)"', html)
    if not m:
        print(f"ERROR: could not find an ie_data.xls download link on {page_url}", file=sys.stderr)
        sys.exit(1)
    url = m.group(1)
    return f"https:{url}" if url.startswith("//") else url


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
    return add_months_str(date_str, 1)


def add_months_str(date_str, n):
    """'2023-06-01' + 3 → '2023-09-01'"""
    y, m, _ = date_str.split("-")
    y, m = int(y), int(m) + n
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y}-{m:02d}-01"


def month_end_str(date_str):
    """'2026-06-01' → '2026-06-30'"""
    y, m, _ = date_str.split("-")
    y, m = int(y), int(m)
    return f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"


def month_is_complete(date_str, today):
    """A month "counts" once `today` (US Eastern) is past its last day -
    Shiller's own current-month row is a placeholder (e.g. "Sept price is
    Sept 1st close"), not a full-month figure, same reasoning FRED's monthly
    average needs downstream in fetch_fred_prices()."""
    y, m, _ = date_str.split("-")
    return today > date(int(y), int(m), calendar.monthrange(int(y), int(m))[1])


# ── Shiller workbook ────────────────────────────────────────────────────────

def parse_shiller(data_bytes):
    """One row per month: date, price (P), dividend (D), earnings (E) and
    cape (CAPE) - the last three are None wherever Shiller hasn't populated
    that column yet (each lags price by a different amount; CAPE, driven by
    a 10-year real-earnings average, is usually the freshest of the three)."""
    import pandas as pd

    suffix, engine = detect_excel_format(data_bytes)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data_bytes)
        tmp = f.name

    try:
        raw = pd.read_excel(tmp, sheet_name="Data", header=None, engine=engine)
    finally:
        os.unlink(tmp)

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

    for req in ("Date", "P", "D", "E", "CAPE"):
        if req not in df.columns:
            print(f"ERROR: Column '{req}' missing. Got: {list(df.columns)}", file=sys.stderr)
            sys.exit(1)

    df = df[pd.to_numeric(df["Date"], errors="coerce").notna()].copy()
    df["Date"] = pd.to_numeric(df["Date"])
    for col in ("P", "D", "E", "CAPE"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["P"].notna() & (df["P"] > 0)].copy()

    rows = []
    for _, row in df.iterrows():
        date_str = parse_shiller_date(row["Date"])
        if date_str is None:
            continue
        rows.append({
            "date":     date_str,
            "price":    round(float(row["P"]), 2),
            "dividend": round(float(row["D"]), 2) if pd.notna(row["D"]) else None,
            "earnings": round(float(row["E"]), 2) if pd.notna(row["E"]) and row["E"] > 0 else None,
            "cape":     round(float(row["CAPE"]), 2) if pd.notna(row["CAPE"]) else None,
        })
    return rows


# ── Earnings overrides: cross-check only, no longer an input ─────────────────

def load_overrides():
    if not os.path.exists(OVERRIDES_PATH):
        return []
    with open(OVERRIDES_PATH) as f:
        data = json.load(f)
    return sorted(data.get("entries", []), key=lambda e: e["effective_from"])


def cross_check_overrides(confirmed_rows, overrides):
    """data/earnings_overrides.json (S&P Global's discontinued quarterly
    scorecard) is no longer used to compute sp500_pe - Shiller's own earnings
    column, now the operational source, reaches nearly as current and
    updates on its own. Kept only as a sanity check: log a warning if the
    last override quarter disagrees with Shiller's own figure for the same
    quarter by more than a rounding-sized amount. Never fails the fetch."""
    if not overrides:
        return
    by_month = {r["date"]: r["earnings"] for r in confirmed_rows}
    last_override = overrides[-1]
    quarter_end_month = f"{last_override['quarter_end'][:7]}-01"
    shiller_value = by_month.get(quarter_end_month)
    if shiller_value is None:
        print(f"Cross-check: no Shiller anchor for {quarter_end_month}; skipping.")
        return
    diff_pct = abs(shiller_value - last_override["ttm_eps"]) / last_override["ttm_eps"] * 100
    status = "OK" if diff_pct < 2 else "DIVERGED"
    print(f"Cross-check vs data/earnings_overrides.json: {last_override['quarter_end']} "
          f"TTM {last_override['ttm_eps']:.2f} vs Shiller {shiller_value:.2f} "
          f"({diff_pct:.2f}% diff) [{status}]")


# ── FRED SP500 monthly prices (extension beyond Shiller's own price) ────────

def fetch_fred_prices(start_date):
    """FRED is a secondary source here (the primary is Shiller), so this
    degrades gracefully via fetch_series(required=False): a missing key or
    failed request yields no prices and the extension falls back to
    whatever Shiller himself already has for that month."""
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

    today = today_eastern()
    prices = {}
    for o in obs:
        y, m, _ = o["date"].split("-")
        month_str = f"{int(y)}-{int(m):02d}-01"
        if not month_is_complete(month_str, today):
            continue
        prices[month_str] = o["value"]

    return prices


# ── Simple Shiller-derived series (cape, dividend yield, earnings yield) ────

def build_simple_series(rows, field, transform):
    return [
        {"date": r["date"], "value": transform(r[field], r)}
        for r in rows
        if r[field] is not None
    ]


def write_simple_output(series_id, observations, fetched_at):
    descriptor = series_meta.load(series_id)
    input_id = descriptor["inputs"][0]["id"]
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=observations[-1]["date"],
        first_observation=observations[0]["date"],
        observation_count=len(observations),
        inputs={input_id: {"last_observation": observations[-1]["date"]}},
        fetched_at=fetched_at,
    )
    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "observations": observations,
    }
    path = os.path.join(DATA_DIR, f"{series_id}.json")
    series_meta.write_json(path, output)
    print(f"Wrote {len(observations)} observations → data/{series_id}.json "
          f"({observations[0]['date']} → {observations[-1]['date']})")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Resolving current ie_data.xls link from shillerdata.com...")
    xls_url = resolve_shiller_xls_url()
    print(f"  {xls_url}")

    print("Fetching Shiller data...")
    shiller_bytes = fetch_bytes(xls_url)
    print(f"  Downloaded {len(shiller_bytes):,} bytes")

    parsed = parse_shiller(shiller_bytes)
    if not parsed:
        print("ERROR: No Shiller observations parsed.", file=sys.stderr)
        sys.exit(1)

    today = today_eastern()
    shiller_rows = [r for r in parsed if month_is_complete(r["date"], today)]
    if not shiller_rows:
        print("ERROR: No complete-month Shiller observations.", file=sys.stderr)
        sys.exit(1)

    confirmed = [r for r in shiller_rows if r["earnings"] is not None]
    if not confirmed:
        print("ERROR: No Shiller rows with confirmed earnings.", file=sys.stderr)
        sys.exit(1)
    last_earnings_date = confirmed[-1]["date"]
    print(f"  Shiller price through {shiller_rows[-1]['date']}, "
          f"earnings through {last_earnings_date} ({len(shiller_rows)} months)")

    overrides = load_overrides()
    cross_check_overrides(confirmed, overrides)

    # ── sp500_pe: confirmed months, plus a one-calendar-quarter forward-fill
    #    grace window, then the earnings leg terminates ───────────────────────
    pe_observations = [
        {
            "date":      r["date"],
            "price":     r["price"],
            "earnings":  r["earnings"],
            "pe":        round(r["price"] / r["earnings"], 2),
            "estimated": False,
        }
        for r in confirmed
    ]

    grace_cutoff = add_months_str(last_earnings_date, 3)
    shiller_by_date = {r["date"]: r for r in shiller_rows}
    fred_start = next_month_str(shiller_rows[-1]["date"])
    fred_prices = {}
    if fred_start <= grace_cutoff:
        print(f"Fetching FRED SP500 monthly prices from {fred_start}...")
        fred_prices = fetch_fred_prices(fred_start)
        if fred_prices:
            print(f"  FRED prices: {min(fred_prices)} → {max(fred_prices)} ({len(fred_prices)} months)")

    last_confirmed_earnings = confirmed[-1]["earnings"]
    cursor = next_month_str(last_earnings_date)
    while cursor <= grace_cutoff:
        row = shiller_by_date.get(cursor)
        price = row["price"] if row else fred_prices.get(cursor)
        if price is None:
            break  # neither source has this month yet
        pe_observations.append({
            "date":      cursor,
            "price":     round(price, 2),
            "earnings":  round(last_confirmed_earnings, 2),
            "pe":        round(price / last_confirmed_earnings, 2),
            "estimated": True,
        })
        cursor = next_month_str(cursor)

    fetched_at = datetime.now(timezone.utc)
    descriptor = series_meta.load("sp500_pe")
    earnings_last_observation = month_end_str(last_earnings_date)
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=pe_observations[-1]["date"],
        first_observation=pe_observations[0]["date"],
        observation_count=len(pe_observations),
        inputs={
            "price": {"last_observation": pe_observations[-1]["date"]},
            "earnings": {
                "last_observation": earnings_last_observation,
                "confirmed_through": earnings_last_observation,
                "value": last_confirmed_earnings,
            },
        },
        fetched_at=fetched_at,
    )
    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "observations": pe_observations,
    }
    series_meta.write_json(os.path.join(DATA_DIR, "sp500_pe.json"), output)

    confirmed_n = sum(1 for o in pe_observations if not o["estimated"])
    estimated_n = len(pe_observations) - confirmed_n
    print(f"\nWrote {len(pe_observations)} observations → data/sp500_pe.json")
    print(f"  Confirmed: {confirmed_n}  |  Estimated: {estimated_n}")
    print(f"  Full range: {pe_observations[0]['date']} → {pe_observations[-1]['date']}")
    print(f"  Latest P/E: {pe_observations[-1]['pe']:.2f}x (price {pe_observations[-1]['price']:,.2f})")

    # ── The Shiller-derived series: no forward-fill, straight off his own
    #    columns, terminating wherever he hasn't published that field yet ────
    write_simple_output(
        "sp500_cape",
        build_simple_series(shiller_rows, "cape", lambda v, r: v),
        fetched_at,
    )
    write_simple_output(
        "sp500_dividend_yield",
        build_simple_series(shiller_rows, "dividend", lambda v, r: round(v / r["price"] * 100, 2)),
        fetched_at,
    )
    write_simple_output(
        "sp500_earnings_yield",
        build_simple_series(shiller_rows, "earnings", lambda v, r: round(v / r["price"] * 100, 2)),
        fetched_at,
    )


if __name__ == "__main__":
    main()
