"""Runs every series' fetcher, catching failures per series so one broken
fetch never stops the others. Replaces the workflow's five per-series fetch
steps (design.md decision 7): where those were a three-place edit per series
(the fetch step, its `OUTCOME_<id>` env line, and the id list in the summary
step), adding a series here needs nothing — `series_meta.ids()` already
drives the loop.

Writes `data/fetch_status.json` (`{id: {ok, returncode, seconds}}`) and always
exits 0; the workflow's final `if: always()` step reads that file to decide
whether the job should go red, after the deploy has already run.
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import series_meta

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
STATUS_PATH = os.path.join(REPO_ROOT, "data", "fetch_status.json")


def fetcher_path(descriptor):
    name = descriptor.get("fetcher", f"fetch_{descriptor['id']}.py")
    return os.path.join(SCRIPTS_DIR, name)


def run_one(series_id, descriptor):
    script = fetcher_path(descriptor)
    print(f"::group::{series_id}")
    start = time.monotonic()
    try:
        result = subprocess.run([sys.executable, script])
        returncode = result.returncode
    except OSError as e:
        print(f"could not run {script}: {e}")
        returncode = None
    seconds = time.monotonic() - start
    print(f"{series_id}: {seconds:.1f}s, returncode {returncode}")
    print("::endgroup::")
    return {"ok": returncode == 0, "returncode": returncode, "seconds": round(seconds, 1)}


def main():
    status = {}
    for series_id in series_meta.ids():
        # Views (presentation.data) draw an existing series' data file and own
        # no fetcher; running fetch_<id>.py for one would fail every night.
        if series_meta.is_view(series_id):
            continue
        descriptor = series_meta.load(series_id)
        status[series_id] = run_one(series_id, descriptor)

    series_meta.write_json(STATUS_PATH, status)

    failed = [series_id for series_id, r in status.items() if not r["ok"]]
    if failed:
        print(f"fetch_all.py: {len(failed)} series failed: {', '.join(sorted(failed))}")


if __name__ == "__main__":
    main()
