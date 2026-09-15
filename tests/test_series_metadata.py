"""Tests for series/*.json descriptors and the meta + as_of header contract
they produce. See openspec/changes/s3-series-metadata/specs/series-metadata
and specs/data-freshness.
"""

import os
import sys
from datetime import date, datetime

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import build_site
import series_meta
from staleness import add_business_days, compute_due_by

SERIES_IDS = series_meta.ids()

# ── `presentation` schema (chart-components capability, design.md decision 4) ─

ALLOWED_PRESENTATION_KEYS = {"sections", "publish", "order", "summary", "chart", "stats", "table"}
REQUIRED_PRESENTATION_KEYS = {"sections", "order", "summary", "chart"}
ALLOWED_CHART_KEYS = {
    "type", "y", "presets", "recessions", "zeroline", "overlays", "custom_date", "traces",
}
ALLOWED_TABLE_KEYS = {"kind", "rows", "windows"}
VALID_TABLE_KIND = {"recent", "changes"}
SITE_SECTION_IDS = {s["id"] for s in build_site.load_site(build_site.PAGES_DIR)["sections"]}

REQUIRED_FIELDS = {
    "id", "title", "short_title", "kind", "units", "cadence",
    "publication_lag_business_days", "revisions", "revision_note",
    "source_line", "sources", "inputs", "methodology", "notes",
}
VALID_KIND = {"timeseries", "curve", "intervals"}
VALID_CADENCE = {"daily", "monthly", "quarterly"}
VALID_REVISIONS = {"none", "occasional", "regular", "retroactive"}
VALID_INPUT_STATUS = {"active", "discontinued"}

PIPELINE_OWNED_KEYS = ("id", "kind", "cadence", "publication_lag_business_days")
PIPELINE_OWNED_INPUT_KEYS = ("id", "cadence", "publication_lag_business_days", "required", "status")


def _parse(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


# ── Descriptor structure ────────────────────────────────────────────────────

@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_descriptor_has_required_fields(series_id):
    d = series_meta.load(series_id)
    missing = REQUIRED_FIELDS - d.keys()
    assert not missing, f"{series_id}: missing {missing}"


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_descriptor_enums_valid(series_id):
    d = series_meta.load(series_id)
    assert d["kind"] in VALID_KIND, f"{series_id}: kind {d['kind']!r}"
    assert d["cadence"] in VALID_CADENCE, f"{series_id}: cadence {d['cadence']!r}"
    assert d["revisions"] in VALID_REVISIONS, f"{series_id}: revisions {d['revisions']!r}"
    for inp in d["inputs"]:
        status = inp.get("status", "active")
        assert status in VALID_INPUT_STATUS, f"{series_id}.{inp['id']}: status {status!r}"


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_presentation_schema_valid(series_id):
    d = series_meta.load(series_id)
    presentation = d.get("presentation")
    if presentation is None:
        return  # a data-only dataset (e.g. usrec) has no page

    missing = REQUIRED_PRESENTATION_KEYS - presentation.keys()
    assert not missing, f"{series_id}.presentation: missing {missing}"
    extra = presentation.keys() - ALLOWED_PRESENTATION_KEYS
    assert not extra, f"{series_id}.presentation: unknown keys {extra}"

    unknown_sections = set(presentation["sections"]) - SITE_SECTION_IDS
    assert not unknown_sections, (
        f"{series_id}.presentation.sections: {unknown_sections} not in pages/site.json"
    )

    chart = presentation["chart"]
    assert "type" in chart, f"{series_id}.presentation.chart: missing type"
    extra_chart_keys = chart.keys() - ALLOWED_CHART_KEYS
    assert not extra_chart_keys, f"{series_id}.presentation.chart: unknown keys {extra_chart_keys}"
    for preset in chart.get("presets", []):
        assert build_site.PRESET_RE.match(preset), f"{series_id}.presentation.chart.presets: {preset!r}"

    table = presentation.get("table")
    if isinstance(table, dict):
        extra_table_keys = table.keys() - ALLOWED_TABLE_KEYS
        assert not extra_table_keys, f"{series_id}.presentation.table: unknown keys {extra_table_keys}"
        assert table.get("kind") in VALID_TABLE_KIND, f"{series_id}.presentation.table.kind: {table.get('kind')!r}"
        for window in table.get("windows", []):
            assert build_site.PRESET_RE.match(window), f"{series_id}.presentation.table.windows: {window!r}"
    else:
        assert table in (None, True, False), f"{series_id}.presentation.table: {table!r}"


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_fetcher_exists_when_given(series_id):
    d = series_meta.load(series_id)
    fetcher = d.get("fetcher")
    if fetcher is None:
        return
    path = os.path.join(SCRIPTS_DIR, fetcher)
    assert os.path.isfile(path), f"{series_id}.fetcher: {fetcher!r} not found at {path}"


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_input_sources_exist(series_id):
    d = series_meta.load(series_id)
    slugs = {s["slug"] for s in d["sources"]}
    for inp in d["inputs"]:
        assert inp["source"] in slugs, (
            f"{series_id}: input {inp['id']!r} names source {inp['source']!r}, "
            f"not present in sources ({sorted(slugs)})"
        )


# ── meta/as_of header contract, checked against committed data files ───────

@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_meta_pipeline_owned_keys_match_descriptor(series_id, load_data):
    descriptor = series_meta.load(series_id)
    meta = load_data(series_id)["meta"]

    for key in PIPELINE_OWNED_KEYS:
        assert meta.get(key) == descriptor.get(key), f"{series_id}.meta.{key}"

    desc_inputs = {i["id"]: i for i in descriptor["inputs"]}
    meta_inputs = {i["id"]: i for i in meta["inputs"]}
    assert desc_inputs.keys() == meta_inputs.keys(), series_id

    for input_id, d_input in desc_inputs.items():
        m_input = meta_inputs[input_id]
        for key in PIPELINE_OWNED_INPUT_KEYS:
            default = {"required": True, "status": "active"}.get(key)
            assert m_input.get(key, default) == d_input.get(key, default), (
                f"{series_id}.meta.inputs.{input_id}.{key}"
            )


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_as_of_due_by_recomputes(series_id, load_data):
    descriptor = series_meta.load(series_id)
    as_of = load_data(series_id)["as_of"]

    if "inputs" in as_of:
        for input_id, input_as_of in as_of["inputs"].items():
            input_desc = next(i for i in descriptor["inputs"] if i["id"] == input_id)
            expected = compute_due_by(
                _parse(input_as_of["last_observation"]),
                input_desc.get("cadence", descriptor["cadence"]),
                input_desc["publication_lag_business_days"],
            )
            assert input_as_of["due_by"] == expected.isoformat(), f"{series_id}.inputs.{input_id}"
    else:
        expected = compute_due_by(
            _parse(as_of["last_observation"]),
            descriptor["cadence"],
            descriptor["publication_lag_business_days"],
        )
        assert as_of["due_by"] == expected.isoformat(), series_id


# ── period_label ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cadence,last_obs,expected", [
    ("daily", "2026-09-10", "10 Sep 2026"),
    ("monthly", "2026-08-01", "Aug 2026"),
    ("quarterly", "2025-09-30", "Q3 2025"),
])
def test_period_label(cadence, last_obs, expected):
    assert series_meta.period_label(last_obs, cadence) == expected


# ── Calendar fixtures (design.md decision 4) ────────────────────────────────

def test_thanksgiving_week():
    assert add_business_days(date(2026, 11, 25), 1) == date(2026, 11, 27)


def test_good_friday_2027():
    assert add_business_days(date(2027, 3, 25), 1) == date(2027, 3, 29)


def test_extra_closure_2025_01_09():
    assert add_business_days(date(2025, 1, 8), 1) == date(2025, 1, 10)


@pytest.mark.parametrize("last_observation,cadence,lag,expected", [
    (date(2026, 9, 10), "daily", 1, date(2026, 9, 14)),       # healthy
    (date(2026, 9, 3), "daily", 1, date(2026, 9, 8)),          # Labor Day
    (date(2026, 11, 25), "daily", 1, date(2026, 11, 30)),      # Thanksgiving
    (date(2026, 8, 1), "monthly", 1, date(2026, 10, 1)),       # SP500 monthly, lag 1
    (date(2026, 8, 1), "monthly", 5, date(2026, 10, 7)),       # USREC, lag 5
    (date(2025, 9, 30), "quarterly", 60, date(2026, 3, 30)),   # earnings, lag 60
])
def test_due_by_fixtures(last_observation, cadence, lag, expected):
    assert compute_due_by(last_observation, cadence, lag) == expected
