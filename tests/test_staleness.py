"""Check each dataset's freshness against its data file's as_of.due_by.

Source defaults to the *live* published data (https://joemirza.com/data/*.json)
rather than the locally committed data/*.json — see CLAUDE.md's data-flow
note: the workflow deploys data/ -> site/data/ -> gh-pages but never commits
fetched data back to main, so a local checkout's data/*.json is known to lag
what's actually live; checking it here in a dev/local run would just
re-report that known gap every time instead of catching a real fetch failure.

Set STALENESS_SOURCE=local to check the local data/ directory instead — this
is what the CI workflow does, running this check right after the day's fetch
and before deploy, when local data/ is the freshest copy that exists.

due_by is computed in Python at fetch time (scripts/series_meta.py,
scripts/staleness.py) from each series' cadence and publication lag; this
test only compares it to today's US Eastern date, per the data-freshness
capability — no business-day or holiday arithmetic happens here. A
`status: discontinued` or non-required input (e.g. sp500_pe's earnings) is
reported but never asserted overdue, matching the roll-up rule.

Carries the `staleness` marker so CI can run it as its own non-gating step,
separate from the correctness tests that gate the deploy (see
.github/workflows/update-data.yml).
"""

import json
import os
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import series_meta
from staleness import check_series

SOURCE = "local" if os.environ.get("STALENESS_SOURCE") == "local" else "live"

SERIES_DIR = os.path.join(os.path.dirname(__file__), "..", "series")


def _published(series_id):
    """Whether the deployed site carries this series' data file. A descriptor
    marked `presentation.publish: false` is built locally only (see
    scripts/build_site.py), so the live site has no data/<id>.json to check."""
    with open(os.path.join(SERIES_DIR, f"{series_id}.json")) as f:
        presentation = json.load(f).get("presentation") or {}
    return presentation.get("publish", True)


@pytest.mark.network
@pytest.mark.staleness
@pytest.mark.parametrize("series_id", series_meta.ids())
def test_series_on_time(series_id):
    if SOURCE == "live" and not _published(series_id):
        pytest.skip(f"{series_id} is not published to the live site; check it with STALENESS_SOURCE=local")
    row = check_series(series_id, source=SOURCE)
    if "error" in row:
        pytest.skip(f"could not reach {row['filename']}: {row['error']}")

    assert not row["overdue"], (
        f"{row['filename']}: last observation {row['last_observation']}, "
        f"due by {row['due_by']} — {row['days_late']} day(s) late"
    )
    for input_row in row["inputs"]:
        if not input_row["alarms"]:
            continue  # discontinued or non-required input: reported, never alarmed
        assert not input_row["overdue"], (
            f"{row['filename']}.{input_row['id']}: last observation "
            f"{input_row['last_observation']}, due by {input_row['due_by']} — "
            f"{input_row['days_late']} day(s) late"
        )
