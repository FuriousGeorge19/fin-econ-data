"""Tests for the source catalogue (`catalog/sources/*.json`), the references
into it from `series/*.json`, and the fetch-time resolution that fills a data
file's `meta.sources[]`. See openspec/specs/source-catalog and the
series-metadata header contract. No network needed.
"""

import copy
import itertools
import json
import os
import shutil
import sys
from datetime import date, timedelta

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import catalog
import series_meta

SLUGS = catalog.slugs()
CATALOG = catalog.load_all()
SERIES_IDS = series_meta.ids()
SEEDS = {"fred", "shiller", "spglobal", "nber"}


# ── Every catalogue file validates ──────────────────────────────────────────

def test_seeds_present():
    assert SEEDS <= set(SLUGS), f"missing seeds: {SEEDS - set(SLUGS)}"


@pytest.mark.parametrize("slug", SLUGS)
def test_entry_validates(slug):
    problems = catalog.validate(CATALOG[slug], slug=slug, known_slugs=set(SLUGS))
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("slug", SLUGS)
def test_entry_is_plain_json_with_trailing_newline(slug):
    with open(catalog.path_for(slug), encoding="utf-8") as f:
        raw = f.read()
    assert raw.endswith("\n"), f"{slug}.json: no trailing newline"
    json.loads(raw)


# ── Descriptor references resolve ───────────────────────────────────────────

def test_descriptor_references_resolve():
    problems = catalog.check_descriptor_refs(CATALOG)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_descriptor_sources_carry_only_reference_keys(series_id):
    d = series_meta.load(series_id)
    for i, ref in enumerate(d["sources"]):
        assert "slug" in ref, f"{series_id}.sources[{i}]: no slug"
        extra = set(ref) - catalog.SOURCE_REF_KEYS
        assert not extra, (
            f"{series_id}.sources[{i}]: {sorted(extra)} — name and licence come from the catalogue"
        )


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_input_datasets_exist_when_given(series_id):
    d = series_meta.load(series_id)
    for inp in d["inputs"]:
        if "dataset" in inp:
            assert catalog.find_dataset(CATALOG[inp["source"]], inp["dataset"]) is not None, (
                f"{series_id}.inputs[{inp['id']}]: {inp['source']!r} has no dataset {inp['dataset']!r}"
            )


def test_used_by_covers_every_series():
    uses = catalog.used_by()
    covered = set(itertools.chain.from_iterable(uses.values()))
    assert covered == set(SERIES_IDS)
    assert uses[("fred", "dgs")] == ["dgs10", "spreads", "yield_curve"]
    assert "sp500_pe" in uses[("spglobal", "sp500-index")]
    assert "usrec" in uses[("nber", "chronology")]


# ── Fetch-time resolution (series_meta.meta_from_descriptor) ────────────────

RESOLVED_REQUIRED = {"slug", "name", "url", "licence", "terms_status"}


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_meta_from_descriptor_resolves_every_source(series_id):
    meta = series_meta.meta_from_descriptor(series_meta.load(series_id))
    assert "presentation" not in meta and "fetcher" not in meta
    assert len(meta["sources"]) == len(series_meta.load(series_id)["sources"])
    for s in meta["sources"]:
        missing = RESOLVED_REQUIRED - s.keys()
        assert not missing, f"{series_id}: resolved source {s.get('slug')} missing {missing}"
        assert "<" not in s["name"] and "<" not in s["licence"]


def test_sp500_pe_resolves_to_three_entries_with_via_and_status():
    meta = series_meta.meta_from_descriptor(series_meta.load("sp500_pe"))
    by_key = {(s["slug"], s.get("dataset")): s for s in meta["sources"]}
    assert set(by_key) == {("shiller", "ie-data"), ("spglobal", "sp-500-eps"), ("spglobal", "sp500-index")}

    index = by_key[("spglobal", "sp500-index")]
    assert index["via"] == "FRED"
    assert index["url"] == "https://fred.stlouisfed.org/series/SP500"
    assert index["terms_status"] == "restricted"
    assert index["dataset_name"]

    eps = by_key[("spglobal", "sp-500-eps")]
    assert "via" not in eps
    assert eps["terms_status"] == "restricted"  # inherits S&P DJI's source-level terms (read 2026-09-15)
    assert eps["note"]

    shiller = by_key[("shiller", "ie-data")]
    assert shiller["url"] == CATALOG["shiller"]["homepage"]  # no per-use url → homepage
    assert shiller["terms_status"] == "unknown"


def test_resolve_source_without_dataset():
    r = catalog.resolve_source_ref({"slug": "fred"}, catalog=CATALOG)
    assert r["name"] == CATALOG["fred"]["name"]
    assert r["url"] == CATALOG["fred"]["homepage"]
    assert r["licence"] == CATALOG["fred"]["terms"]["summary"]
    assert r["terms_status"] == "verified"
    assert "dataset" not in r and "dataset_name" not in r and "via" not in r


def test_resolve_dataset_terms_override_wins():
    nfci = catalog.find_dataset(CATALOG["fred"], "nfci")
    r = catalog.resolve_source_ref({"slug": "fred", "dataset": "nfci"}, catalog=CATALOG)
    assert r["licence"] == nfci["terms"]["summary"]
    assert r["licence"] != CATALOG["fred"]["terms"]["summary"]
    assert r["terms_status"] == "verified"  # status inherited from the file


def test_resolve_bad_references_raise_naming_the_ref():
    with pytest.raises(ValueError, match="'nope'"):
        catalog.resolve_source_ref({"slug": "nope"}, catalog=CATALOG)
    with pytest.raises(ValueError, match="'missing'"):
        catalog.resolve_source_ref({"slug": "fred", "dataset": "missing"}, catalog=CATALOG)


def test_meta_from_descriptor_names_descriptor_on_bad_ref():
    d = copy.deepcopy(series_meta.load("dgs10"))
    d["sources"] = [{"slug": "nope"}]
    with pytest.raises(ValueError, match=r"series/dgs10\.json.*'nope'"):
        series_meta.meta_from_descriptor(d)


@pytest.mark.parametrize("series_id", SERIES_IDS)
def test_committed_data_file_sources_exist_in_catalogue(series_id, load_data):
    # Holds for both the pre-catalogue shape (inline name/licence) and the
    # resolved shape, so fixtures need not be regenerated for this change.
    for s in load_data(series_id)["meta"]["sources"]:
        assert s["slug"] in CATALOG, f"{series_id}: data file names unknown source {s['slug']!r}"


# ── Validation rules (sandbox: mutate a copy of the exemplar) ───────────────

def _exemplar():
    return copy.deepcopy(CATALOG["shiller"])


def _problems(entry, slug="shiller"):
    return catalog.validate(entry, slug=slug, known_slugs=set(SLUGS))


def _set_top(key, value):
    return lambda e: e.__setitem__(key, value)


def _set_ds(key, value):
    return lambda e: e["datasets"][0].__setitem__(key, value)


@pytest.mark.parametrize("mutate,expect", [
    (_set_top("licence", "x"), "unknown keys ['licence']"),
    (_set_ds("used_by", ["sp500_pe"]), "unknown keys ['used_by']"),
    (lambda e: e["access"].__setitem__("via", "nope"), "no catalogue file for 'nope'"),
    (lambda e: e["access"].__setitem__("via", "shiller"), "cannot be reached via itself"),
    (lambda e: e["datasets"].append(copy.deepcopy(e["datasets"][0])), "duplicate dataset id"),
    (lambda e: e["terms"].update({"status": "verified", "url": "https://example.org/terms"}),
     "requires a non-empty verbatim terms.quote"),
    (lambda e: e["terms"].update({"status": "unverified"}), "'unverified' requires terms.url"),
    (_set_ds("status", "discontinued"), 'cannot be "ongoing"'),
    (_set_ds("topics", ["astrology"]), "not in the vocabulary"),
    (_set_ds("topics", []), "non-empty list"),
    (_set_top("role", "reference"), "has no datasets"),
    (lambda e: e["verified"].__setitem__("on", (date.today() + timedelta(days=1)).isoformat()),
     "is in the future"),
    (_set_top("slug", "other"), "does not match the file name"),
    (_set_ds("publication_lag_business_days", -1), "integer >= 0"),
    (_set_ds("publication_lag_business_days", True), "integer >= 0"),
    (lambda e: e["access"].__setitem__("url", "ftp://example.org/x"), "must start with http"),
    (_set_top("name", "<b>x</b>"), "plain text only"),
    (_set_top("schema_version", 2), "schema_version"),
    (_set_ds("cadence", "hourly"), "cadence"),
    (_set_ds("coverage", {"start": "1871", "end": "soon"}), "coverage.end"),
    (lambda e: e["access"].__setitem__("read_from", "not a url"), "read_from"),
    (lambda e: e.pop("verified"), "missing ['verified']"),
])
def test_validation_rule(mutate, expect):
    entry = _exemplar()
    mutate(entry)
    problems = _problems(entry)
    assert any(expect in p for p in problems), f"expected {expect!r} in {problems}"


def test_unknown_string_is_allowed_for_scalar_facts():
    entry = _exemplar()
    entry["datasets"][0]["cadence"] = "unknown"
    entry["datasets"][0]["coverage"] = "unknown"
    entry["datasets"][0]["publication_lag_business_days"] = "unknown"
    entry["access"]["rate_limit"] = "unknown"
    entry["terms"]["url"] = "unknown"
    assert not _problems(entry)


def test_discontinued_with_dated_end_is_valid():
    entry = _exemplar()
    entry["datasets"][0]["status"] = "discontinued"
    entry["datasets"][0]["coverage"] = {"start": "1871-01", "end": "2023-10-01"}
    assert not _problems(entry)


def test_reference_role_with_no_datasets_is_valid():
    entry = _exemplar()
    entry["role"] = "reference"
    entry["datasets"] = []
    assert not _problems(entry)


def test_via_at_source_level_is_inherited_and_dataset_override_wins():
    entry = _exemplar()
    entry["access"]["via"] = "fred"
    entry["datasets"][0]["access"] = {"method": "api"}
    assert not _problems(entry)
    merged = catalog.merge_block(entry["access"], entry["datasets"][0]["access"])
    assert merged["via"] == "fred" and merged["method"] == "api"
    assert merged["url"] == entry["access"]["url"]  # untouched keys inherit
    fake = dict(CATALOG, shiller=entry)
    r = catalog.resolve_source_ref({"slug": "shiller", "dataset": "ie-data"}, catalog=fake)
    assert r["via"] == "FRED"


def test_missing_read_from_count():
    entry = _exemplar()
    assert catalog.missing_read_from(entry) == (0, 3)  # access, terms, one dataset — all cited
    del entry["datasets"][0]["read_from"]
    assert catalog.missing_read_from(entry) == (1, 3)


# ── Command line ────────────────────────────────────────────────────────────

def test_check_cli_all_clean(capsys):
    assert catalog.main(["check"]) == 0
    assert capsys.readouterr().out == ""


def test_check_cli_single_file_ignores_neighbours(tmp_path, capsys):
    good = tmp_path / "shiller.json"
    shutil.copyfile(catalog.path_for("shiller"), good)
    (tmp_path / "broken.json").write_text("{not json")
    assert catalog.main(["check", str(good)]) == 0
    assert capsys.readouterr().out == ""


def test_check_cli_reports_problem_naming_the_file(tmp_path, capsys):
    bad = tmp_path / "shiller.json"
    entry = _exemplar()
    entry["datasets"][0]["topics"] = ["astrology"]
    bad.write_text(json.dumps(entry))
    assert catalog.main(["check", str(bad)]) == 1
    out = capsys.readouterr().out
    assert "shiller.json" in out and "astrology" in out


def test_report_lists_sources_used_by_and_via_index(capsys):
    assert catalog.main(["report"]) == 0
    out = capsys.readouterr().out
    hosts = next(line for line in out.splitlines() if line.startswith("fred hosts: "))
    assert "spglobal/sp500-index" in hosts.split(": ", 1)[1].split(", ")
    assert "used by: dgs10, spreads, yield_curve" in out
    assert "blocks lacking read_from:" in out


def test_report_topic_filter(capsys):
    assert catalog.main(["report", "--topic", "equity-valuation"]) == 0
    out = capsys.readouterr().out
    assert "ie-data" in out and "sp500-index" in out and "sp-500-eps" in out
    assert "  dgs " not in out and "nber" not in out


def test_report_unknown_topic_fails(capsys):
    assert catalog.main(["report", "--topic", "astrology"]) == 1
