"""Check each fetcher's last observation against its expected publication lag.

Source defaults to the *live* published data (https://joemirza.com/data/*.json)
rather than the locally committed data/*.json. The workflow deploys
data/ -> site/data/ -> gh-pages but never commits fetched data back to main
(see CLAUDE.md's data-flow note), so a local checkout's data/*.json is known to
lag what's actually live — checking it here in a dev/local run would just
re-report that known gap every time instead of catching a real fetch
failure. The bigger question of whether to commit data back to main is left
open for a later session.

Set STALENESS_SOURCE=local to check the local data/ directory instead — this
is what the CI workflow does, running this check right after the day's fetch
and before deploy, when local data/ is the freshest copy that exists (the live
site still has yesterday's data at that point in the job).

Business-day lag, not calendar days, so a Saturday check on a weekday-only
series doesn't false-positive. This is a provisional, hardcoded per-series
tolerance — S3 of the Session Plan formalizes cadence + publication lag as
part of the metadata design; this test should be updated to read from that
metadata once it exists instead of the EXPECTED_LAG_DAYS table below.
"""

import json
import os
from datetime import date, datetime, timedelta
from urllib.request import urlopen

import pytest

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


def _business_days_between(start, end):
    days = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days += 1
    return days


def _fetch_live(name):
    with urlopen(LIVE_BASE + name, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _load_local(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


@pytest.mark.network
@pytest.mark.parametrize("filename,extract_date,max_business_days", SERIES)
def test_series_within_expected_lag(filename, extract_date, max_business_days):
    use_local = os.environ.get("STALENESS_SOURCE") == "local"
    if use_local:
        current = _load_local(filename)
    else:
        try:
            current = _fetch_live(filename)
        except Exception as e:
            pytest.skip(f"could not reach live site: {e}")

    last_date = datetime.strptime(extract_date(current)[:10], "%Y-%m-%d").date()
    lag = _business_days_between(last_date, date.today())
    assert lag <= max_business_days, (
        f"{filename}: last observation {last_date} is {lag} business days old "
        f"(expected <= {max_business_days})"
    )
