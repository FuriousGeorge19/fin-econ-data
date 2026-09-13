"""US bond-market business-day calendar, the due_by freshness rule, and the
staleness check built on top of them.

Used by `scripts/series_meta.py` (`compute_due_by`, called from `build_as_of`
at fetch time), `tests/test_staleness.py` (asserts each series is fresh) and
`scripts/dev.sh` (warns, doesn't fail, that local data/ is known to lag
production — see CLAUDE.md's data-flow note). The calendar and due_by rule are
defined once here so fetch-time computation and the staleness check can't
drift on what "on time" means for a given series.
"""

import calendar
import json
import os
from datetime import date, datetime, timedelta
from urllib.request import urlopen
from zoneinfo import ZoneInfo

LIVE_BASE = "https://joemirza.com/data/"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EASTERN = ZoneInfo("America/New_York")

# One-off US bond-market closures not captured by the federal-holiday rules
# below (e.g. the 2025-01-09 National Day of Mourning for President Carter).
EXTRA_CLOSURES = {
    date(2025, 1, 9),
}


# ── Business-day calendar ───────────────────────────────────────────────────

def _nth_weekday(year, month, weekday, n):
    """The date of the nth `weekday` (Monday=0) in `month`/`year`."""
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    d += timedelta(weeks=n - 1)
    return d


def _last_weekday(year, month, weekday):
    """The date of the last `weekday` (Monday=0) in `month`/`year`."""
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    d -= timedelta(days=(d.weekday() - weekday) % 7)
    return d


def _observed(d):
    """Federal in-lieu-of observance: Saturday -> Friday before, Sunday -> Monday after."""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def _easter(year):
    """Date of Easter Sunday (Anonymous Gregorian algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _good_friday(year):
    return _easter(year) - timedelta(days=2)


def _federal_holidays(year):
    """US bond-market holidays for `year`: federal holidays (observed) plus Good
    Friday. Good Friday is treated as closed even in years when Treasury markets
    trade (e.g. 2021, 2023, 2026) — the safe direction, one extra day of slack
    rather than a false badge.
    """
    return {
        _observed(date(year, 1, 1)),        # New Year's Day
        _nth_weekday(year, 1, 0, 3),         # MLK Day
        _nth_weekday(year, 2, 0, 3),         # Washington's Birthday
        _last_weekday(year, 5, 0),           # Memorial Day
        _observed(date(year, 6, 19)),        # Juneteenth
        _observed(date(year, 7, 4)),         # Independence Day
        _nth_weekday(year, 9, 0, 1),         # Labor Day
        _nth_weekday(year, 10, 0, 2),        # Columbus Day
        _observed(date(year, 11, 11)),       # Veterans Day
        _nth_weekday(year, 11, 3, 4),        # Thanksgiving
        _observed(date(year, 12, 25)),       # Christmas
        _good_friday(year),
    }


_holiday_cache = {}


def is_us_bond_holiday(d):
    if d.year not in _holiday_cache:
        _holiday_cache[d.year] = _federal_holidays(d.year)
    return d in _holiday_cache[d.year] or d in EXTRA_CLOSURES


def is_business_day(d):
    return d.weekday() < 5 and not is_us_bond_holiday(d)


def add_business_days(d, n):
    """The date reached by moving forward from `d`, counting `n` business days
    (not including `d` itself), skipping weekends and holidays."""
    current = d
    counted = 0
    while counted < n:
        current += timedelta(days=1)
        if is_business_day(current):
            counted += 1
    return current


# ── Period ends and the due_by rule ─────────────────────────────────────────

def _add_months(year, month, n):
    m = month - 1 + n
    return year + m // 12, m % 12 + 1


def period_end(d, cadence):
    """The end of the cadence period containing `d`: daily -> `d` itself;
    monthly -> the last day of `d`'s month; quarterly -> the last day of `d`'s
    calendar quarter."""
    if cadence == "daily":
        return d
    if cadence == "monthly":
        last_day = calendar.monthrange(d.year, d.month)[1]
        return date(d.year, d.month, last_day)
    if cadence == "quarterly":
        q_last_month = ((d.month - 1) // 3) * 3 + 3
        last_day = calendar.monthrange(d.year, q_last_month)[1]
        return date(d.year, q_last_month, last_day)
    raise ValueError(f"unknown cadence: {cadence!r}")


def next_period_end(d, cadence):
    """`period_end(d, cadence)` advanced one cadence step: daily -> the next
    business day; monthly -> the last day of the next month; quarterly -> the
    last day of the next quarter."""
    pe = period_end(d, cadence)
    if cadence == "daily":
        return add_business_days(pe, 1)
    if cadence == "monthly":
        y, m = _add_months(pe.year, pe.month, 1)
        last_day = calendar.monthrange(y, m)[1]
        return date(y, m, last_day)
    if cadence == "quarterly":
        y, m = _add_months(pe.year, pe.month, 3)
        last_day = calendar.monthrange(y, m)[1]
        return date(y, m, last_day)
    raise ValueError(f"unknown cadence: {cadence!r}")


def compute_due_by(last_observation, cadence, publication_lag_business_days):
    """The date by which the next observation should have been published:
    the next period end, plus the publication lag in business days."""
    npe = next_period_end(last_observation, cadence)
    return add_business_days(npe, publication_lag_business_days)


def today_eastern():
    return datetime.now(EASTERN).date()


# ── Staleness check (per-dataset, per-input, from as_of) ───────────────────

def fetch_live(name):
    with urlopen(LIVE_BASE + name, timeout=30) as resp:
        return json.loads(resp.read().decode())


def load_local(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


def _parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def _judge(due_by_str, today):
    due_by = _parse_date(due_by_str)
    if due_by is None:
        return None, None
    overdue = today > due_by
    days_late = (today - due_by).days if overdue else 0
    return overdue, days_late


def check_series(series_id, source="local", *, today=None):
    """Return one dataset's freshness: `{id, filename, last_observation, due_by,
    overdue, days_late, inputs: [...]}` (or `{id, filename, error}` if the file
    can't be read/reached), read from `as_of` rather than a hard-coded lag
    table. Each input entry also carries `alarms` (required and active per the
    descriptor); a `status: discontinued` or non-required input is reported
    but never marked overdue, per the data-freshness roll-up rule.
    """
    from series_meta import load as load_descriptor  # local import: avoids a module-load cycle

    if today is None:
        today = today_eastern()

    filename = f"{series_id}.json"
    try:
        data = load_local(filename) if source == "local" else fetch_live(filename)
    except Exception as e:
        return {"id": series_id, "filename": filename, "error": str(e)}

    input_descs = {i["id"]: i for i in load_descriptor(series_id).get("inputs", [])}
    as_of = data.get("as_of", {})
    overdue, days_late = _judge(as_of.get("due_by"), today)
    row = {
        "id": series_id,
        "filename": filename,
        "last_observation": as_of.get("last_observation"),
        "due_by": as_of.get("due_by"),
        "overdue": overdue,
        "days_late": days_late,
        "inputs": [],
    }
    for input_id, input_as_of in (as_of.get("inputs") or {}).items():
        input_desc = input_descs.get(input_id, {})
        alarms = input_desc.get("required", True) and input_desc.get("status", "active") == "active"
        if alarms:
            i_overdue, i_days_late = _judge(input_as_of.get("due_by"), today)
        else:
            i_overdue, i_days_late = False, 0
        row["inputs"].append({
            "id": input_id,
            "last_observation": input_as_of.get("last_observation"),
            "due_by": input_as_of.get("due_by"),
            "overdue": i_overdue,
            "days_late": i_days_late,
            "alarms": alarms,
        })
    return row


def check(source="local", *, today=None):
    """Return a list of `check_series()` results, one per `series_meta.ids()`.
    `source="local"` reads committed data/*.json (no network); `source="live"`
    fetches the published site. `today` overrides the US Eastern "today" used
    to judge overdue (for tests)."""
    from series_meta import ids as series_ids  # local import: avoids a module-load cycle

    if today is None:
        today = today_eastern()
    return [check_series(series_id, source, today=today) for series_id in series_ids()]


if __name__ == "__main__":
    import sys

    source = sys.argv[1] if len(sys.argv) > 1 else "local"
    for row in check(source):
        if "error" in row:
            print(f"  ? {row['filename']}: could not check ({row['error']})")
            continue
        if row["overdue"]:
            print(f"  ! {row['filename']}: last observation {row['last_observation']}, "
                  f"due by {row['due_by']} — {row['days_late']} day(s) late")
        else:
            print(f"  . {row['filename']}: last observation {row['last_observation']} "
                  f"(due by {row['due_by']})")
        for input_row in row["inputs"]:
            if input_row["overdue"]:
                print(f"      ! {input_row['id']}: last observation {input_row['last_observation']}, "
                      f"due by {input_row['due_by']} — {input_row['days_late']} day(s) late")
