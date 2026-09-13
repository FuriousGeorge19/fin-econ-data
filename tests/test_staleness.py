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
metadata once it exists instead of the SERIES table in scripts/staleness.py.

The lag table and business-day math live in scripts/staleness.py, shared with
scripts/dev.sh, so the two call sites can't drift on what "stale" means.
"""

import os
from datetime import date, datetime

import pytest

from staleness import SERIES, business_days_between, fetch_live, load_local


@pytest.mark.network
@pytest.mark.parametrize("filename,extract_date,max_business_days", SERIES)
def test_series_within_expected_lag(filename, extract_date, max_business_days):
    use_local = os.environ.get("STALENESS_SOURCE") == "local"
    if use_local:
        current = load_local(filename)
    else:
        try:
            current = fetch_live(filename)
        except Exception as e:
            pytest.skip(f"could not reach live site: {e}")

    last_date = datetime.strptime(extract_date(current)[:10], "%Y-%m-%d").date()
    lag = business_days_between(last_date, date.today())
    assert lag <= max_business_days, (
        f"{filename}: last observation {last_date} is {lag} business days old "
        f"(expected <= {max_business_days})"
    )
