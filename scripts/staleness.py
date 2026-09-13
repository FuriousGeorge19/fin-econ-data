"""Shared staleness-check logic: series lag table + business-day math.

Used by tests/test_staleness.py (assert each series is fresh) and
scripts/dev.sh (warn, don't fail, that local data/ is known to lag production
- see CLAUDE.md's data-flow note). Keeping one copy of the table means the two
call sites can't drift apart on what "stale" means for a given series.
"""

import json
import os
from datetime import date, datetime, timedelta
from urllib.request import urlopen

LIVE_BASE = "https://joemirza.com/data/"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# (file, date_path, expected max staleness in business days)
# Generous on purpose (site conventions target same-day-or-next, this table is
# only meant to catch a fetch that's been silently failing for a while).
SERIES = [
    ("dgs10.json", lambda d: d["observations"][-1]["date"], 5),
    ("yield_curve.json", lambda d: max(d["observations"].keys()), 5),
    ("spreads.json", lambda d: max(o["date"] for o in d["series"]["10y2y"]["observations"]), 5),
    ("sp500_pe.json", lambda d: d["observations"][-1]["date"], 45),  # monthly
    # usrec.json collapses USREC to recession intervals only, so the latest
    # interval's start date reflects when a recession last began, not when
    # the fetch last ran (during an expansion that could be years back). Use
    # the header's last_updated timestamp instead to check the fetch itself.
    ("usrec.json", lambda d: d["last_updated"][:10], 10),
]


def business_days_between(start, end):
    days = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days += 1
    return days


def fetch_live(name):
    with urlopen(LIVE_BASE + name, timeout=30) as resp:
        return json.loads(resp.read().decode())


def load_local(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


def check(source="local"):
    """Return a list of (filename, last_date, lag_days, max_lag_days, stale) per series.

    source="local" reads committed data/*.json (no network). source="live" fetches
    the published site instead. A series that can't be read/reached is returned
    with lag_days=None.
    """
    results = []
    for filename, extract_date, max_business_days in SERIES:
        try:
            current = load_local(filename) if source == "local" else fetch_live(filename)
            last_date = datetime.strptime(extract_date(current)[:10], "%Y-%m-%d").date()
            lag = business_days_between(last_date, date.today())
            results.append((filename, last_date, lag, max_business_days, lag > max_business_days))
        except Exception as e:
            results.append((filename, None, None, max_business_days, None, str(e)))
    return results


if __name__ == "__main__":
    import sys

    source = sys.argv[1] if len(sys.argv) > 1 else "local"
    for row in check(source):
        filename, last_date, lag, max_lag, stale = row[:5]
        if lag is None:
            print(f"  ? {filename}: could not check ({row[5]})")
        elif stale:
            print(f"  ! {filename}: last observation {last_date} is {lag} business days old (expected <= {max_lag})")
        else:
            print(f"  . {filename}: last observation {last_date} ({lag}/{max_lag} business days)")
