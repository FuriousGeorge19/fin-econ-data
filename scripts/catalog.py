"""Source catalogue: loader, validator, resolver and report for
`catalog/sources/<slug>.json` (openspec/specs/source-catalog).

One file per rights holder — a source is one set of terms and one way in.
This module is the schema's authority: `catalog/README.md`'s field table is a
rendering of what `validate()` enforces. Standard library only.

Command line:

    python3 scripts/catalog.py check                      # every file + every series/*.json reference
    python3 scripts/catalog.py check catalog/sources/x.json   # that file alone (an agent's done-check)
    python3 scripts/catalog.py report [--topic T]         # sources x datasets x used-by, via reverse index

`series_meta.meta_from_descriptor()` calls `resolve_source_ref()` at fetch time
to turn a descriptor's `{slug, dataset?, url?, note?}` reference into the
`meta.sources[]` entry the About tab renders.
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
CATALOG_DIR = os.path.join(REPO_ROOT, "catalog", "sources")
SERIES_DIR = os.path.join(REPO_ROOT, "series")

SCHEMA_VERSION = 1
UNKNOWN = "unknown"

# The controlled vocabulary for datasets[].topics. Extend here; the README
# renders this list. Keep values kebab-case.
TOPICS = (
    "rates",
    "credit",
    "inflation",
    "equity-valuation",
    "equity-returns",
    "macro",
    "recession-dating",
    "real-estate",
    "global",
    "expectations",
)

ROLES = ("data", "reference")
ACCESS_METHODS = ("api", "file-download", "manual-download", "web-page", "none")
AUTH_KINDS = ("none", "free-key", "paid-key", "login", "manual")
TERMS_STATUS = ("verified", "restricted", "unverified", "unknown")
CADENCES = ("daily", "weekly", "monthly", "quarterly", "annual", "irregular")
DATASET_STATUS = ("active", "discontinued")

TOP_REQUIRED = {
    "schema_version", "slug", "role", "name", "short_name", "homepage",
    "description", "access", "terms", "datasets", "verified",
}
TOP_OPTIONAL = {"notes"}
ACCESS_REQUIRED = {"method", "url", "format", "auth"}
ACCESS_OPTIONAL = {"rate_limit", "via", "notes", "read_from"}
TERMS_REQUIRED = {"summary", "status"}
TERMS_OPTIONAL = {"url", "quote", "read_from"}
VERIFIED_REQUIRED = {"on", "by"}
DATASET_REQUIRED = {
    "id", "name", "gives", "ids", "topics", "cadence", "coverage",
    "publication_lag_business_days", "status",
}
DATASET_OPTIONAL = {
    "units", "access", "terms", "roadmap", "verified_on", "read_from", "notes",
}

# What a descriptor's sources[] entry may carry (series-metadata spec).
SOURCE_REF_KEYS = {"slug", "dataset", "url", "note"}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
URL_RE = re.compile(r"^https?://\S+$")
FULL_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PARTIAL_DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


# ── Loading ──────────────────────────────────────────────────────────────────

def slugs(catalog_dir=CATALOG_DIR):
    """Catalogue slugs (file stems), sorted."""
    if not os.path.isdir(catalog_dir):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(catalog_dir)
        if f.endswith(".json")
    )


def path_for(slug, catalog_dir=CATALOG_DIR):
    return os.path.join(catalog_dir, f"{slug}.json")


def load(slug, catalog_dir=CATALOG_DIR):
    """The parsed catalogue entry for `slug`."""
    with open(path_for(slug, catalog_dir)) as f:
        return json.load(f)


def load_all(catalog_dir=CATALOG_DIR):
    """{slug: entry} for every file in the catalogue."""
    return {s: load(s, catalog_dir) for s in slugs(catalog_dir)}


def merge_block(base, override):
    """A dataset's `access`/`terms` merged over its source's: key by key,
    the override wins. The one merge rule, used by the validator and the
    resolver alike."""
    merged = dict(base or {})
    merged.update(override or {})
    return merged


def find_dataset(entry, dataset_id):
    for ds in entry.get("datasets", []):
        if isinstance(ds, dict) and ds.get("id") == dataset_id:
            return ds
    return None


# ── Validation ───────────────────────────────────────────────────────────────

def _is_str(v):
    return isinstance(v, str) and v.strip() != ""


def _is_url(v):
    return isinstance(v, str) and bool(URL_RE.match(v))


def _is_str_list(v):
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _parse_full_date(v):
    if not isinstance(v, str) or not FULL_DATE_RE.match(v):
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except ValueError:
        return None


def _check_read_from(value, where, problems):
    if value is None:
        return
    values = value if isinstance(value, list) else [value]
    if not values or not all(_is_url(v) for v in values):
        problems.append(f"{where}.read_from: must be a URL or a list of URLs")


def _check_keys(block, required, optional, where, problems):
    if not isinstance(block, dict):
        problems.append(f"{where}: must be an object")
        return False
    missing = required - block.keys()
    if missing:
        problems.append(f"{where}: missing {sorted(missing)}")
    unknown = block.keys() - required - optional
    if unknown:
        problems.append(f"{where}: unknown keys {sorted(unknown)}")
    return True


def _check_access(block, where, problems, *, own_slug, known_slugs, partial=False):
    """`partial=True` for a dataset override, where any subset of keys is allowed."""
    required = set() if partial else ACCESS_REQUIRED
    if not _check_keys(block, required, ACCESS_REQUIRED | ACCESS_OPTIONAL, where, problems):
        return
    if "method" in block and block["method"] not in ACCESS_METHODS:
        problems.append(f"{where}.method: {block['method']!r} not in {list(ACCESS_METHODS)}")
    if "auth" in block and block["auth"] not in AUTH_KINDS:
        problems.append(f"{where}.auth: {block['auth']!r} not in {list(AUTH_KINDS)}")
    if "url" in block and not (_is_url(block["url"]) or block["url"] == UNKNOWN):
        problems.append(f"{where}.url: must start with http:// or https:// (or be \"unknown\")")
    if "format" in block and not _is_str(block["format"]):
        problems.append(f"{where}.format: must be a non-empty string")
    if "rate_limit" in block and not _is_str(block["rate_limit"]):
        problems.append(f"{where}.rate_limit: must be a non-empty string (or \"unknown\")")
    if "via" in block:
        via = block["via"]
        if not (_is_str(via) and SLUG_RE.match(via)):
            problems.append(f"{where}.via: must be a catalogue slug")
        elif via == own_slug:
            problems.append(f"{where}.via: a source cannot be reached via itself")
        elif known_slugs is not None and via not in known_slugs:
            problems.append(f"{where}.via: no catalogue file for {via!r}")
    if "notes" in block and not _is_str_list(block["notes"]):
        problems.append(f"{where}.notes: must be a list of strings")
    _check_read_from(block.get("read_from"), where, problems)


def _check_terms(block, where, problems, *, partial=False):
    required = set() if partial else TERMS_REQUIRED
    if not _check_keys(block, required, TERMS_REQUIRED | TERMS_OPTIONAL, where, problems):
        return
    if "summary" in block and not _is_str(block["summary"]):
        problems.append(f"{where}.summary: must be a non-empty string")
    if "summary" in block and isinstance(block["summary"], str) and "<" in block["summary"]:
        problems.append(f"{where}.summary: plain text only (no HTML)")
    if "status" in block and block["status"] not in TERMS_STATUS:
        problems.append(f"{where}.status: {block['status']!r} not in {list(TERMS_STATUS)}")
    if "url" in block and not (_is_url(block["url"]) or block["url"] == UNKNOWN):
        problems.append(f"{where}.url: must start with http:// or https:// (or be \"unknown\")")
    if "quote" in block and not isinstance(block["quote"], str):
        problems.append(f"{where}.quote: must be a string")
    _check_read_from(block.get("read_from"), where, problems)


def _check_terms_evidence(merged, where, problems):
    """The status definitions (design decision 3): verified/restricted need a
    terms URL and a verbatim quote; unverified needs the URL."""
    status = merged.get("status")
    url_ok = _is_url(merged.get("url"))
    quote_ok = _is_str(merged.get("quote"))
    if status in ("verified", "restricted"):
        if not url_ok:
            problems.append(f"{where}.status: {status!r} requires terms.url")
        if not quote_ok:
            problems.append(f"{where}.status: {status!r} requires a non-empty verbatim terms.quote")
    elif status == "unverified" and not url_ok:
        problems.append(f"{where}.status: 'unverified' requires terms.url (the page that was found)")


def _check_coverage(cov, where, problems, *, discontinued):
    if cov == UNKNOWN:
        if discontinued:
            problems.append(f"{where}.coverage: a discontinued dataset needs a dated coverage.end")
        return
    if not isinstance(cov, dict) or set(cov.keys()) != {"start", "end"}:
        problems.append(f"{where}.coverage: must be {{start, end}} or \"unknown\"")
        return
    start, end = cov["start"], cov["end"]
    if not (start == UNKNOWN or (isinstance(start, str) and PARTIAL_DATE_RE.match(start))):
        problems.append(f"{where}.coverage.start: YYYY, YYYY-MM, YYYY-MM-DD or \"unknown\"")
    if not (end in ("ongoing", UNKNOWN) or (isinstance(end, str) and PARTIAL_DATE_RE.match(end))):
        problems.append(f"{where}.coverage.end: a date, \"ongoing\" or \"unknown\"")
    if discontinued and end == "ongoing":
        problems.append(f"{where}.coverage.end: a discontinued dataset cannot be \"ongoing\"")


def _check_dataset(ds, entry, where, problems, *, own_slug, known_slugs, today):
    if not _check_keys(ds, DATASET_REQUIRED, DATASET_OPTIONAL, where, problems):
        return
    if "id" in ds and not (_is_str(ds["id"]) and SLUG_RE.match(ds["id"])):
        problems.append(f"{where}.id: must match {SLUG_RE.pattern}")
    for key in ("name", "gives"):
        if key in ds and not _is_str(ds[key]):
            problems.append(f"{where}.{key}: must be a non-empty string")
    if "name" in ds and isinstance(ds["name"], str) and "<" in ds["name"]:
        problems.append(f"{where}.name: plain text only (no HTML)")
    if "ids" in ds and not _is_str_list(ds["ids"]):
        problems.append(f"{where}.ids: must be a list of strings (may be empty for a web page)")
    if "topics" in ds:
        topics = ds["topics"]
        if not (_is_str_list(topics) and topics):
            problems.append(f"{where}.topics: must be a non-empty list")
        else:
            bad = [t for t in topics if t not in TOPICS]
            if bad:
                problems.append(f"{where}.topics: {bad} not in the vocabulary {list(TOPICS)}")
    if "cadence" in ds and not (ds["cadence"] in CADENCES or ds["cadence"] == UNKNOWN):
        problems.append(f"{where}.cadence: {ds['cadence']!r} not in {list(CADENCES)} or \"unknown\"")
    status = ds.get("status")
    if "status" in ds and status not in DATASET_STATUS:
        problems.append(f"{where}.status: {status!r} not in {list(DATASET_STATUS)}")
    if "coverage" in ds:
        _check_coverage(ds["coverage"], where, problems, discontinued=(status == "discontinued"))
    if "publication_lag_business_days" in ds:
        lag = ds["publication_lag_business_days"]
        ok = (isinstance(lag, int) and not isinstance(lag, bool) and lag >= 0) or lag == UNKNOWN
        if not ok:
            problems.append(f"{where}.publication_lag_business_days: integer >= 0 or \"unknown\"")
    if "units" in ds and not _is_str(ds["units"]):
        problems.append(f"{where}.units: must be a non-empty string")
    if "access" in ds:
        _check_access(ds["access"], f"{where}.access", problems,
                      own_slug=own_slug, known_slugs=known_slugs, partial=True)
    if "terms" in ds:
        _check_terms(ds["terms"], f"{where}.terms", problems, partial=True)
        if isinstance(ds["terms"], dict) and isinstance(entry.get("terms"), dict):
            _check_terms_evidence(merge_block(entry["terms"], ds["terms"]), f"{where}.terms", problems)
    if "roadmap" in ds and not _is_str_list(ds["roadmap"]):
        problems.append(f"{where}.roadmap: must be a list of strings")
    if "verified_on" in ds:
        d = _parse_full_date(ds["verified_on"])
        if d is None:
            problems.append(f"{where}.verified_on: must be YYYY-MM-DD")
        elif today is not None and d > today:
            problems.append(f"{where}.verified_on: {ds['verified_on']} is in the future")
    _check_read_from(ds.get("read_from"), where, problems)
    if "notes" in ds and not _is_str_list(ds["notes"]):
        problems.append(f"{where}.notes: must be a list of strings")


def validate(entry, *, slug=None, known_slugs=None, today=None):
    """Problems with one catalogue entry, as strings; empty when valid.

    `slug`: the file stem, checked against the entry's own `slug`.
    `known_slugs`: slugs that exist on disk, for `via` checks (None skips them).
    `today`: the date `verified.on` may not exceed (default: today).
    """
    today = today or date.today()
    problems = []
    if not _check_keys(entry, TOP_REQUIRED, TOP_OPTIONAL, "top level", problems):
        return problems

    if entry.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version: must be {SCHEMA_VERSION}")

    own_slug = entry.get("slug")
    if not (_is_str(own_slug) and SLUG_RE.match(own_slug)):
        problems.append(f"slug: must match {SLUG_RE.pattern}")
    elif slug is not None and own_slug != slug:
        problems.append(f"slug: {own_slug!r} does not match the file name {slug!r}")

    role = entry.get("role")
    if role not in ROLES:
        problems.append(f"role: {role!r} not in {list(ROLES)}")

    for key in ("name", "short_name", "description"):
        if not _is_str(entry.get(key)):
            problems.append(f"{key}: must be a non-empty string")
        elif "<" in entry[key]:
            problems.append(f"{key}: plain text only (no HTML)")
    if not _is_url(entry.get("homepage")):
        problems.append("homepage: must start with http:// or https://")

    _check_access(entry.get("access"), "access", problems,
                  own_slug=own_slug, known_slugs=known_slugs)
    _check_terms(entry.get("terms"), "terms", problems)
    if isinstance(entry.get("terms"), dict):
        _check_terms_evidence(entry["terms"], "terms", problems)

    verified = entry.get("verified")
    if _check_keys(verified, VERIFIED_REQUIRED, set(), "verified", problems):
        d = _parse_full_date(verified.get("on"))
        if d is None:
            problems.append("verified.on: must be YYYY-MM-DD")
        elif d > today:
            problems.append(f"verified.on: {verified['on']} is in the future")
        if not _is_str(verified.get("by")):
            problems.append("verified.by: must be a non-empty string")

    datasets = entry.get("datasets")
    if not isinstance(datasets, list):
        problems.append("datasets: must be a list (empty for a reference source)")
    else:
        if role == "reference" and datasets:
            problems.append("datasets: a 'reference' source has no datasets")
        seen = set()
        for i, ds in enumerate(datasets):
            ds_id = ds.get("id") if isinstance(ds, dict) else None
            where = f"datasets[{ds_id if ds_id else i}]"
            if ds_id is not None:
                if ds_id in seen:
                    problems.append(f"{where}: duplicate dataset id {ds_id!r}")
                seen.add(ds_id)
            _check_dataset(ds, entry, where, problems,
                           own_slug=own_slug, known_slugs=known_slugs, today=today)

    if "notes" in entry and not _is_str_list(entry["notes"]):
        problems.append("notes: must be a list of strings")

    return problems


def missing_read_from(entry):
    """(lacking, total) fact blocks — access, terms, each dataset — without a
    `read_from`. The validator does not require read_from; a workflow verifier
    does, and `report` prints this count so it can see where to look."""
    blocks = [entry.get("access", {}), entry.get("terms", {})]
    blocks += [ds for ds in entry.get("datasets", []) if isinstance(ds, dict)]
    lacking = sum(1 for b in blocks if not b.get("read_from"))
    return lacking, len(blocks)


# ── Descriptor references ────────────────────────────────────────────────────

def _load_descriptors(series_dir=SERIES_DIR):
    out = {}
    for f in sorted(os.listdir(series_dir)):
        if f.endswith(".json"):
            with open(os.path.join(series_dir, f)) as fh:
                out[os.path.splitext(f)[0]] = json.load(fh)
    return out


def check_descriptor_refs(catalog, series_dir=SERIES_DIR):
    """Problems with every `series/*.json`'s catalogue references."""
    problems = []
    for series_id, d in _load_descriptors(series_dir).items():
        where = f"series/{series_id}.json"
        for i, ref in enumerate(d.get("sources", [])):
            if not isinstance(ref, dict):
                problems.append(f"{where}: sources[{i}] must be an object")
                continue
            unknown = ref.keys() - SOURCE_REF_KEYS
            if unknown:
                problems.append(
                    f"{where}: sources[{i}] unknown keys {sorted(unknown)} "
                    f"(only {sorted(SOURCE_REF_KEYS)}; name and licence come from the catalogue)"
                )
            problems += _check_ref(ref, catalog, f"{where}: sources[{i}]")
        for inp in d.get("inputs", []):
            ref = {"slug": inp.get("source")}
            if "dataset" in inp:
                ref["dataset"] = inp["dataset"]
            problems += _check_ref(ref, catalog, f"{where}: inputs[{inp.get('id')}]")
    return problems


def _check_ref(ref, catalog, where):
    problems = []
    slug = ref.get("slug")
    if slug not in catalog:
        problems.append(f"{where}: no catalogue file for slug {slug!r} under catalog/sources/")
        return problems
    ds_id = ref.get("dataset")
    if ds_id is not None and find_dataset(catalog[slug], ds_id) is None:
        problems.append(f"{where}: {slug!r} has no dataset {ds_id!r}")
    if "url" in ref and not _is_url(ref["url"]):
        problems.append(f"{where}: url must start with http:// or https://")
    if "note" in ref and not _is_str(ref["note"]):
        problems.append(f"{where}: note must be a non-empty string")
    return problems


def resolve_source_ref(ref, *, catalog=None):
    """A descriptor's `{slug, dataset?, url?, note?}` reference resolved into
    the `meta.sources[]` entry the About tab renders:

        {slug, short_name, dataset?, name, dataset_name?, url, licence, terms_status, via?, note?}

    `url` defaults to the source's homepage; `licence` is the merged
    `terms.summary`; `via` is the hosting source's short_name. `short_name` is
    the referenced source's own compact form (e.g. "Shiller/Yale") — added for
    gs10_long's per-observation source tooltip (site/js/charts/timeseries.js),
    which needs something shorter than `name` to put on a hover line. Raises
    ValueError naming the slug/dataset when the reference does not resolve.
    """
    catalog = catalog if catalog is not None else load_all()
    slug = ref.get("slug")
    if slug not in catalog:
        raise ValueError(f"no catalogue file for source slug {slug!r} under catalog/sources/")
    source = catalog[slug]
    access, terms = source.get("access", {}), source.get("terms", {})

    out = {"slug": slug, "short_name": source["short_name"]}
    ds_id = ref.get("dataset")
    if ds_id is not None:
        ds = find_dataset(source, ds_id)
        if ds is None:
            raise ValueError(f"catalogue source {slug!r} has no dataset {ds_id!r}")
        access = merge_block(access, ds.get("access"))
        terms = merge_block(terms, ds.get("terms"))
        out["dataset"] = ds_id
        out["name"] = source["name"]
        out["dataset_name"] = ds["name"]
    else:
        out["name"] = source["name"]

    out["url"] = ref.get("url") or source["homepage"]
    out["licence"] = terms.get("summary", UNKNOWN)
    out["terms_status"] = terms.get("status", UNKNOWN)
    via = access.get("via")
    if via:
        host = catalog.get(via)
        out["via"] = host["short_name"] if host else via
    if ref.get("note"):
        out["note"] = ref["note"]
    return out


def used_by(series_dir=SERIES_DIR):
    """{(slug, dataset_or_None): [series ids]} derived from every descriptor's
    `sources[]` and `inputs[]` — never stored in the catalogue."""
    out = {}
    for series_id, d in _load_descriptors(series_dir).items():
        keys = set()
        for ref in d.get("sources", []):
            if isinstance(ref, dict) and ref.get("slug"):
                keys.add((ref["slug"], ref.get("dataset")))
        for inp in d.get("inputs", []):
            if inp.get("source"):
                keys.add((inp["source"], inp.get("dataset")))
        for k in keys:
            out.setdefault(k, []).append(series_id)
    return {k: sorted(v) for k, v in out.items()}


# ── Command line ─────────────────────────────────────────────────────────────

def _rel(path):
    return os.path.relpath(path, REPO_ROOT)


def cmd_check(paths):
    problems = []
    known = set(slugs())
    if paths:
        for p in paths:
            slug = os.path.splitext(os.path.basename(p))[0]
            try:
                with open(p) as f:
                    entry = json.load(f)
            except (OSError, ValueError) as e:
                problems.append(f"{_rel(p)}: {e}")
                continue
            problems += [f"{_rel(p)}: {m}" for m in validate(entry, slug=slug, known_slugs=known | {slug})]
    else:
        catalog = {}
        for slug in slugs():
            try:
                entry = load(slug)
            except ValueError as e:
                problems.append(f"{_rel(path_for(slug))}: {e}")
                continue
            catalog[slug] = entry
            problems += [f"{_rel(path_for(slug))}: {m}" for m in validate(entry, slug=slug, known_slugs=known)]
        problems += check_descriptor_refs(catalog)
    for m in problems:
        print(m)
    return 1 if problems else 0


def _coverage_text(cov):
    if cov == UNKNOWN or not isinstance(cov, dict):
        return UNKNOWN
    return f"{cov.get('start')}–{cov.get('end')}"


def cmd_report(topic):
    if topic is not None and topic not in TOPICS:
        print(f"unknown topic {topic!r}; vocabulary: {', '.join(TOPICS)}")
        return 1
    catalog = load_all()
    uses = used_by()
    hosted = {}  # host slug -> ["slug/dataset", ...]
    for slug, entry in catalog.items():
        datasets = entry.get("datasets", [])
        if topic is not None:
            datasets = [ds for ds in datasets if topic in ds.get("topics", [])]
            if not datasets:
                continue
        lacking, total = missing_read_from(entry)
        source_users = uses.get((slug, None), [])
        print(
            f"{slug}  ({entry.get('role')})  terms: {entry.get('terms', {}).get('status')}"
            f"  verified: {entry.get('verified', {}).get('on')}"
            f"  blocks lacking read_from: {lacking}/{total}"
            + (f"  used by: {', '.join(source_users)}" if source_users else "")
        )
        for ds in datasets:
            access = merge_block(entry.get("access"), ds.get("access"))
            if access.get("via"):
                hosted.setdefault(access["via"], []).append(f"{slug}/{ds.get('id')}")
            ds_users = uses.get((slug, ds.get("id")), [])
            flags = []
            if ds.get("status") == "discontinued":
                flags.append("discontinued")
            if access.get("via"):
                flags.append(f"via {access['via']}")
            print(
                f"  {ds.get('id'):<16} {str(ds.get('cadence')):<10} {_coverage_text(ds.get('coverage')):<22}"
                f" topics: {', '.join(ds.get('topics', [])):<32}"
                + (f" used by: {', '.join(ds_users)}" if ds_users else "")
                + (f"  [{'; '.join(flags)}]" if flags else "")
            )
    for host in sorted(hosted):
        print(f"{host} hosts: {', '.join(sorted(hosted[host]))}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_check = sub.add_parser("check", help="validate catalogue files (all, or the paths given)")
    p_check.add_argument("paths", nargs="*", help="catalogue files to check alone")
    p_report = sub.add_parser("report", help="sources x datasets x used-by, plus the via reverse index")
    p_report.add_argument("--topic", help="only datasets carrying this topic")
    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check(args.paths)
    return cmd_report(args.topic)


if __name__ == "__main__":
    sys.exit(main())
