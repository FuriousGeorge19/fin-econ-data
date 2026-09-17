"""Fetch the ultra-long 10-year Treasury yield (S11a, chart 4): FRED's GS10
monthly average (1953-04 onward, the earliest FRED publishes a 10-year
constant-maturity series) stitched to Shiller/Yale's own long-term interest
rate column ("Rate GS10" in ie_data.xls) for 1871-01 through 1953-03, where
no official Treasury series exists.

The two legs are checked for continuity at the seam rather than assumed:
Shiller's own 1953-03 value should sit close to FRED's first (1953-04)
observation, logged as a warning (never a failure — Shiller could restate
his historical column independently of FRED) if they diverge sharply.

Reuses fetch_sp500_pe.py's Shiller-workbook download/parsing helpers
(resolve_shiller_xls_url, fetch_bytes, detect_excel_format, parse_shiller_date)
rather than duplicating the header-row scan and URL resolution.

Establishes the per-observation source/frequency metadata pattern for
stitched series: every observation carries `source` (the catalog slug that
produced it: "shiller" or "fred") and `frequency` (its native cadence, both
monthly here), so the frontend can show which leg produced a given point
without a chart-type-specific hack. See site/js/charts/timeseries.js.
"""

import os
import sys
import tempfile
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series
from fetch_sp500_pe import (
    resolve_shiller_xls_url,
    fetch_bytes,
    detect_excel_format,
    parse_shiller_date,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gs10_long.json")

# FRED GS10's first published observation (checked 2026-09-17 via FRED's public
# fredgraph.csv). If FRED's coverage ever changes, main() warns rather than
# silently drawing the seam somewhere else.
CUTOVER = "1953-04-01"

SEAM_TOLERANCE = 0.10  # percentage points; Shiller's 1953-03 vs FRED's 1953-04


def fetch_shiller_long_rate():
    """Every monthly row of Shiller's "Rate GS10" column, oldest-first —
    the full history, not just the pre-cutover leg, so main() can use the
    tail of this list for the seam-continuity check."""
    import pandas as pd

    url = resolve_shiller_xls_url()
    data = fetch_bytes(url)
    suffix, engine = detect_excel_format(data)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
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

    for req in ("Date", "Rate GS10"):
        if req not in df.columns:
            print(f"ERROR: Column {req!r} missing from Shiller workbook. Got: {list(df.columns)}",
                  file=sys.stderr)
            sys.exit(1)

    df = df[pd.to_numeric(df["Date"], errors="coerce").notna()].copy()
    df["Date"] = pd.to_numeric(df["Date"])
    df["Rate GS10"] = pd.to_numeric(df["Rate GS10"], errors="coerce")
    df = df[df["Rate GS10"].notna()]

    rows = []
    for _, row in df.iterrows():
        date_str = parse_shiller_date(row["Date"])
        if date_str is None:
            continue
        rows.append({
            "date": date_str,
            "value": round(float(row["Rate GS10"]), 2),
            "source": "shiller",
            "frequency": "monthly",
        })
    rows.sort(key=lambda r: r["date"])
    return rows


def fetch_fred_gs10():
    """FRED's GS10, monthly average, full history (starts 1953-04-01 — no
    partial-current-month risk: the H.15 monthly average is only published
    once a month closes, unlike Shiller's own current-month placeholder
    row, so no month_is_complete() gate is needed here)."""
    observations = fetch_series("GS10")
    return [
        {"date": o["date"], "value": o["value"], "source": "fred", "frequency": "monthly"}
        for o in observations
    ]


def check_seam(shiller_rows, fred_rows):
    """Log (never fail) how closely the two legs agree at the handoff."""
    before_cutover = [r for r in shiller_rows if r["date"] < CUTOVER]
    if not before_cutover or not fred_rows:
        return
    shiller_last, fred_first = before_cutover[-1], fred_rows[0]
    diff = abs(shiller_last["value"] - fred_first["value"])
    status = "OK" if diff <= SEAM_TOLERANCE else "DIVERGED"
    print(f"Seam check: Shiller {shiller_last['date']} = {shiller_last['value']:.2f} vs "
          f"FRED {fred_first['date']} = {fred_first['value']:.2f} (diff {diff:.2f}) [{status}]")


def main():
    print("Fetching Shiller's long-term interest rate column...")
    shiller_all = fetch_shiller_long_rate()
    print(f"  {len(shiller_all)} months, {shiller_all[0]['date']} -> {shiller_all[-1]['date']}")

    print("Fetching FRED GS10 (monthly average)...")
    fred_rows = fetch_fred_gs10()
    print(f"  {len(fred_rows)} months, {fred_rows[0]['date']} -> {fred_rows[-1]['date']}")

    if fred_rows[0]["date"] != CUTOVER:
        print(f"WARNING: FRED GS10's first observation is {fred_rows[0]['date']}, "
              f"expected {CUTOVER} — CUTOVER in this script may need updating.",
              file=sys.stderr)

    check_seam(shiller_all, fred_rows)

    shiller_rows = [r for r in shiller_all if r["date"] < CUTOVER]
    if not shiller_rows:
        print("ERROR: No Shiller observations before the cutover.", file=sys.stderr)
        sys.exit(1)

    observations = shiller_rows + fred_rows

    fetched_at = datetime.now(timezone.utc)
    descriptor = series_meta.load("gs10_long")
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=observations[-1]["date"],
        first_observation=observations[0]["date"],
        observation_count=len(observations),
        inputs={
            "shiller": {"last_observation": shiller_rows[-1]["date"]},
            "fred": {"last_observation": fred_rows[-1]["date"]},
        },
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "observations": observations,
    }
    series_meta.write_json(OUTPUT_PATH, output)

    print(f"\nWrote {len(observations)} observations -> {OUTPUT_PATH}")
    print(f"  Shiller leg: {len(shiller_rows)} months, {shiller_rows[0]['date']} -> {shiller_rows[-1]['date']}")
    print(f"  FRED leg:    {len(fred_rows)} months, {fred_rows[0]['date']} -> {fred_rows[-1]['date']}")
    print(f"  Latest: {observations[-1]['date']} = {observations[-1]['value']:.2f}%")


if __name__ == "__main__":
    main()
