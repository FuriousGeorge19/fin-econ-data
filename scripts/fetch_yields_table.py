"""Fetch the "what can I earn" yields grid (roadmap item 11) from FRED.

One number per cell: instrument type down, maturity across, the latest
published value of each cell's FRED series. Rows update on different
schedules — Treasury and TIPS daily, the Treasury's corporate curve monthly —
so every row carries its own as-of date and the descriptor lists one input per
row, which is what makes `as_of.inputs` (and the staleness check) judge each
row on its own clock.

A cell with no series stays absent from its row. Nothing is interpolated to
fill the grid: the 9-month column Fidelity shows has no constant-maturity
equivalent here, and a blank is the honest answer.
"""

import os
import sys
from datetime import datetime, timezone

import series_meta
from fred_utils import fetch_series, get_api_key

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "yields_table.json")

COLUMNS = [
    {"id": "ON",  "label": "Overnight", "months": 0},
    {"id": "3M",  "label": "3 month",   "months": 3},
    {"id": "6M",  "label": "6 month",   "months": 6},
    {"id": "1Y",  "label": "1 year",    "months": 12},
    {"id": "2Y",  "label": "2 year",    "months": 24},
    {"id": "3Y",  "label": "3 year",    "months": 36},
    {"id": "5Y",  "label": "5 year",    "months": 60},
    {"id": "7Y",  "label": "7 year",    "months": 84},
    {"id": "10Y", "label": "10 year",   "months": 120},
    {"id": "20Y", "label": "20 year",   "months": 240},
    {"id": "30Y", "label": "30 year",   "months": 360},
]

# `input` is the descriptor input id the row's freshness is judged under.
ROWS = [
    {"id": "fedfunds", "input": "fedfunds", "label": "Effective federal funds rate",
     "cells": {"ON": "DFF"}},
    {"id": "sofr", "input": "sofr", "label": "SOFR (overnight repo)",
     "cells": {"ON": "SOFR"}},
    {"id": "treasury", "input": "treasury", "label": "US Treasury",
     "cells": {"3M": "DGS3MO", "6M": "DGS6MO", "1Y": "DGS1", "2Y": "DGS2",
               "3Y": "DGS3", "5Y": "DGS5", "7Y": "DGS7", "10Y": "DGS10",
               "20Y": "DGS20", "30Y": "DGS30"}},
    {"id": "tips", "input": "tips", "label": "TIPS real yield",
     "cells": {"5Y": "DFII5", "7Y": "DFII7", "10Y": "DFII10",
               "20Y": "DFII20", "30Y": "DFII30"}},
    {"id": "corporate_hqm", "input": "hqm", "label": "Corporate, high quality (AAA–A blend)",
     "cells": {"6M": "HQMCB6MT", "1Y": "HQMCB1YR", "2Y": "HQMCB2YR", "3Y": "HQMCB3YR",
               "5Y": "HQMCB5YR", "7Y": "HQMCB7YR", "10Y": "HQMCB10YR",
               "20Y": "HQMCB20YR", "30Y": "HQMCB30YR"}},
]


def latest(series_id):
    """Most recent published observation for one FRED series, or None."""
    obs = fetch_series(series_id, limit=5)
    return obs[-1] if obs else None


def main():
    if not get_api_key():
        print("ERROR: FRED_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    rows = []
    for spec in ROWS:
        cells = {}
        for col, sid in spec["cells"].items():
            print(f"  {spec['id']:14s} {col:4s} {sid}...", end=" ", flush=True)
            obs = latest(sid)
            if obs is None:
                print("no data")
                continue
            print(f"{obs['value']} ({obs['date']})")
            cells[col] = {"value": obs["value"], "date": obs["date"], "series_id": sid}
        if not cells:
            print(f"ERROR: row {spec['id']} has no data at all", file=sys.stderr)
            sys.exit(1)
        rows.append({
            "id": spec["id"],
            "input": spec["input"],
            "label": spec["label"],
            "as_of": max(c["date"] for c in cells.values()),
            "cells": cells,
        })

    descriptor = series_meta.load("yields_table")
    input_last = {}
    for row in rows:
        entry = input_last.setdefault(row["input"], {"last_observation": row["as_of"]})
        entry["last_observation"] = max(entry["last_observation"], row["as_of"])

    fetched_at = datetime.now(timezone.utc)
    as_of = series_meta.build_as_of(
        descriptor,
        last_observation=max(r["as_of"] for r in rows),
        inputs=input_last,
        fetched_at=fetched_at,
    )

    output = {
        "meta": series_meta.meta_from_descriptor(descriptor),
        "as_of": as_of,
        "columns": COLUMNS,
        "rows": rows,
    }
    series_meta.write_json(OUTPUT_PATH, output)
    print(f"\nWrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
