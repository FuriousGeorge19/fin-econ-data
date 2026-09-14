"""Series-descriptor and as-of metadata helpers shared by all fetchers.

`series/<id>.json` is the single hand-maintained descriptor per dataset. A
fetcher loads its descriptor with `load(id)`, embeds it verbatim (minus
`presentation`) under `meta`, calls `build_as_of()` to compute the runtime
freshness block, and writes the result with `write_json()`. `staleness.py`,
`scripts/dev.sh` and the workflow all derive their file lists from `ids()`, so
the list of site data files is defined exactly once.
"""

import copy
import json
import os
from datetime import date, datetime, timezone

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
SERIES_DIR = os.path.join(REPO_ROOT, "series")


def ids():
    """Dataset ids (data-file stems), one per `series/<id>.json`, sorted."""
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(SERIES_DIR)
        if f.endswith(".json")
    )


def load(series_id):
    """The parsed descriptor for `series_id`."""
    path = os.path.join(SERIES_DIR, f"{series_id}.json")
    with open(path) as f:
        return json.load(f)


def meta_from_descriptor(descriptor):
    """The descriptor as embedded into a data file's `meta`: a verbatim copy
    minus `presentation` (chart configuration) and `fetcher` (build-time
    config naming the fetch script) — neither is written to the data file."""
    meta = copy.deepcopy(descriptor)
    meta.pop("presentation", None)
    meta.pop("fetcher", None)
    return meta


def write_json(path, obj):
    """Write `obj` as JSON to `path` atomically: serialize to `<path>.tmp`,
    then `os.replace` it over `path`, so an interrupted write never leaves a
    truncated file."""
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def period_label(d, cadence):
    """A human label for `d` under `cadence`: daily -> '10 Sep 2026'; monthly
    -> 'Aug 2026'; quarterly -> 'Q3 2025'."""
    d = _to_date(d)
    if cadence == "daily":
        return d.strftime("%-d %b %Y")
    if cadence == "monthly":
        return d.strftime("%b %Y")
    if cadence == "quarterly":
        return f"Q{(d.month - 1) // 3 + 1} {d.year}"
    raise ValueError(f"unknown cadence: {cadence!r}")


def _to_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    return d


def _to_str(d):
    return d.isoformat() if isinstance(d, date) else d


def _input_descriptor(descriptor, input_id):
    for entry in descriptor.get("inputs", []):
        if entry["id"] == input_id:
            return entry
    raise ValueError(f"{descriptor.get('id')!r} has no input {input_id!r}")


def build_as_of(descriptor, last_observation, *, first_observation=None,
                 observation_count=None, inputs=None, series=None,
                 latest_value=None, fetched_at=None):
    """Build the runtime `as_of` block for a data file.

    `last_observation` / `first_observation` are the dataset-level observation
    dates (str `YYYY-MM-DD` or `date`). `inputs`, when the descriptor lists
    more than one input (e.g. sp500_pe's price/earnings), is a dict of
    `{input_id: {"last_observation": ..., **extra}}`; extra keys (e.g.
    `confirmed_through`, `value`) pass through onto that input's as-of entry.
    `series`, when the payload holds more than one series (spreads legs,
    yield-curve tenors), is a dict of `{series_key: {"last_observation": ...,
    "first_observation": ..., "observation_count": ...}}`.

    `as_of.due_by` is the earliest `due_by` among the descriptor's inputs that
    are `required` (default true) and `active` (default status); a
    single-input dataset's due_by is computed directly from its dataset-level
    cadence and lag.
    """
    from staleness import compute_due_by  # local import: avoids a module-load cycle

    fetched_at = fetched_at or datetime.now(timezone.utc)
    cadence = descriptor["cadence"]
    last_obs_date = _to_date(last_observation)

    as_of = {
        "fetched_at": fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_observation": _to_str(last_obs_date),
        "period_label": period_label(last_obs_date, cadence),
    }
    if first_observation is not None:
        as_of["first_observation"] = _to_str(_to_date(first_observation))
    if observation_count is not None:
        as_of["observation_count"] = observation_count
    if latest_value is not None:
        as_of["latest_value"] = latest_value

    due_by_candidates = []

    if inputs:
        as_of["inputs"] = {}
        for input_id, extra in inputs.items():
            input_desc = _input_descriptor(descriptor, input_id)
            i_last_obs = _to_date(extra["last_observation"])
            i_cadence = input_desc.get("cadence", cadence)
            i_lag = input_desc["publication_lag_business_days"]
            i_due_by = compute_due_by(i_last_obs, i_cadence, i_lag)

            entry = {
                "last_observation": _to_str(i_last_obs),
                "period_label": period_label(i_last_obs, i_cadence),
                "due_by": _to_str(i_due_by),
            }
            for k, v in extra.items():
                if k != "last_observation":
                    entry[k] = _to_str(v) if isinstance(v, date) else v
            as_of["inputs"][input_id] = entry

            required = input_desc.get("required", True)
            status = input_desc.get("status", "active")
            if required and status == "active":
                due_by_candidates.append(i_due_by)
    else:
        lag = descriptor["publication_lag_business_days"]
        due_by_candidates.append(compute_due_by(last_obs_date, cadence, lag))

    as_of["due_by"] = _to_str(min(due_by_candidates))

    if series:
        as_of["series"] = {}
        for key, s in series.items():
            s_last_obs = _to_date(s["last_observation"])
            s_cadence = s.get("cadence", cadence)
            s_lag = s.get("publication_lag_business_days",
                          descriptor["publication_lag_business_days"])
            s_due_by = compute_due_by(s_last_obs, s_cadence, s_lag)

            entry = {
                "last_observation": _to_str(s_last_obs),
                "period_label": period_label(s_last_obs, s_cadence),
                "due_by": _to_str(s_due_by),
            }
            if "first_observation" in s:
                entry["first_observation"] = _to_str(_to_date(s["first_observation"]))
            if "observation_count" in s:
                entry["observation_count"] = s["observation_count"]
            as_of["series"][key] = entry

    return as_of
