"""Tests for scripts/build_site.py, the multi-page generator. See
openspec/changes/s5-chart-components/specs/site-build/spec.md and design.md
decision 8.

Generator-behavior tests build a small synthetic series/pages/data tree in
tmp_path, isolated from the real repo, so they can freely exercise success
and failure paths without touching production content. A separate
integration test runs the real generator (real series/, pages/, data/)
writing into tmp_path — this is what the workflow's gating pytest step
relies on to catch a broken build before the deploy ships nothing (design.md
risk list). The colour-literal and forbidden-key checks scan the real,
committed `site/js/` tree, since those are a property of committed source,
not of any one generator run.
"""

import glob
import json
import os
import re
import sys

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import build_site
import series_meta


# ── Sandbox fixture: a small synthetic site, isolated from the real repo ──

def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f)


def _page_json(page_dir):
    """Parses the inline `<script id="page">` JSON out of a generated page."""
    with open(os.path.join(page_dir, "index.html")) as f:
        html = f.read()
    match = re.search(
        r'<script type="application/json" id="page">(.*?)</script>', html, re.DOTALL,
    )
    assert match, f"no inline #page JSON in {page_dir}/index.html"
    return json.loads(match.group(1))


@pytest.fixture
def sandbox(tmp_path):
    series_dir = tmp_path / "series"
    pages_dir = tmp_path / "pages"
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "site"
    js_dir = output_dir / "js"
    (js_dir / "charts").mkdir(parents=True)
    (js_dir / "charts" / "timeseries.js").write_text("export function render(el, ctx) {}\n")
    (js_dir / "charts" / "curve.js").write_text("export function render(el, ctx) {}\n")

    _write_json(str(pages_dir / "site.json"), {
        "name": "Test Site",
        "sections": [
            {"id": "economy", "label": "Economy", "tagline": "e"},
            {"id": "markets", "label": "Markets", "tagline": "m"},
            {"id": "rates", "label": "Rates", "tagline": "r"},
        ],
    })

    def add_series(series_id, *, sections, order, chart_type="timeseries",
                   presets=None, payload=None, publish=None):
        presentation = {
                "sections": sections,
                "order": order,
                "summary": f"{series_id} summary",
                "chart": {"type": chart_type, "presets": presets or ["1Y", "All"]},
                "stats": True,
                "table": {"kind": "recent", "rows": 10},
        }
        if publish is not None:
            presentation["publish"] = publish
        _write_json(str(series_dir / f"{series_id}.json"), {
            "id": series_id,
            "title": f"{series_id} title",
            "short_title": series_id,
            "kind": chart_type,
            "presentation": presentation,
        })
        _write_json(
            str(data_dir / f"{series_id}.json"),
            payload or {"meta": {"id": series_id}, "as_of": {},
                        "observations": [{"date": "2026-01-01", "value": 1}]},
        )

    add_series("alpha", sections=["economy"], order=10)
    add_series("beta", sections=["economy", "rates"], order=5)
    # Marked unpublished: every test below asserts it stays out of the
    # generated site unless the build explicitly asks for it.
    add_series("delta", sections=["markets"], order=1, publish=False)

    return dict(
        series_dir=str(series_dir), pages_dir=str(pages_dir),
        data_dir=str(data_dir), output_dir=str(output_dir), js_dir=str(js_dir),
    )


def _build(sandbox, **overrides):
    kwargs = dict(sandbox)
    kwargs.update(overrides)
    return build_site.build(**kwargs)


# ── Page per descriptor, section grids, cross-section placement ──────────

def test_page_per_descriptor_with_presentation(sandbox):
    _build(sandbox)
    for series_id in ("alpha", "beta"):
        assert os.path.isfile(
            os.path.join(sandbox["output_dir"], "charts", series_id, "index.html")
        )


def test_section_pages_list_charts_in_order(sandbox):
    _build(sandbox)
    page = _page_json(os.path.join(sandbox["output_dir"], "economy"))
    assert [b["id"] for b in page["blocks"]] == ["beta", "alpha"]  # order 5 before 10


def test_chart_in_two_sections(sandbox):
    _build(sandbox)
    economy = _page_json(os.path.join(sandbox["output_dir"], "economy"))
    rates = _page_json(os.path.join(sandbox["output_dir"], "rates"))
    assert "beta" in [b["id"] for b in economy["blocks"]]
    assert "beta" in [b["id"] for b in rates["blocks"]]
    markets = _page_json(os.path.join(sandbox["output_dir"], "markets"))
    assert markets["blocks"] == []


def test_asset_and_block_references_are_root_relative(sandbox):
    """A page under /economy/ must reference css/js/block hrefs root-relatively
    (`/css/...`, `/js/...`, `/charts/...`), never page-relatively — otherwise
    it 404s once served from a subdirectory."""
    _build(sandbox)
    with open(os.path.join(sandbox["output_dir"], "economy", "index.html")) as f:
        html = f.read()
    for href in re.findall(r'(?:href|src)="([^"]+)"', html):
        if href.startswith("http"):
            continue
        assert href.startswith("/"), f"non-root-relative reference: {href!r}"

    page = _page_json(os.path.join(sandbox["output_dir"], "economy"))
    for block in page["blocks"]:
        assert block["href"].startswith("/charts/")


# ── Manifests ──────────────────────────────────────────────────────────

def test_manifest_resolves(sandbox):
    _write_json(os.path.join(sandbox["pages_dir"], "my-page.json"), {
        "slug": "my-page", "section": "rates", "title": "My Page", "layout": "grid",
        "blocks": [{"chart": "beta", "size": "full", "preset": "1Y"}],
    })
    _build(sandbox)
    page = _page_json(os.path.join(sandbox["output_dir"], "rates", "my-page"))
    assert page["blocks"][0]["id"] == "beta"
    assert page["blocks"][0]["size"] == "full"
    assert page["blocks"][0]["preset"] == "1Y"


def test_manifest_unknown_chart_fails_the_build(sandbox):
    _write_json(os.path.join(sandbox["pages_dir"], "broken.json"), {
        "slug": "broken", "section": "rates", "title": "Broken", "layout": "grid",
        "blocks": [{"chart": "does-not-exist"}],
    })
    with pytest.raises(build_site.BuildError):
        _build(sandbox)


def test_manifest_unknown_section_fails_the_build(sandbox):
    _write_json(os.path.join(sandbox["pages_dir"], "broken.json"), {
        "slug": "broken", "section": "not-a-section", "title": "Broken", "layout": "grid",
        "blocks": [],
    })
    with pytest.raises(build_site.BuildError):
        _build(sandbox)


def test_home_page_only_when_curated(sandbox):
    _build(sandbox)
    assert not os.path.isfile(os.path.join(sandbox["output_dir"], "index.html"))

    _write_json(os.path.join(sandbox["pages_dir"], "home.json"), {
        "slug": "home", "title": "Home", "layout": "grid",
        "blocks": [{"chart": "alpha", "size": "half"}],
    })
    _build(sandbox)
    assert os.path.isfile(os.path.join(sandbox["output_dir"], "index.html"))


# ── Validation failures (design.md decision 1.3) ──────────────────────────

def test_malformed_preset_fails_the_build(sandbox):
    descriptor_path = os.path.join(sandbox["series_dir"], "alpha.json")
    with open(descriptor_path) as f:
        descriptor = json.load(f)
    descriptor["presentation"]["chart"]["presets"] = ["not-a-preset"]
    _write_json(descriptor_path, descriptor)
    with pytest.raises(build_site.BuildError):
        _build(sandbox)


def test_missing_chart_type_module_fails_the_build(sandbox):
    descriptor_path = os.path.join(sandbox["series_dir"], "alpha.json")
    with open(descriptor_path) as f:
        descriptor = json.load(f)
    descriptor["presentation"]["chart"]["type"] = "no-such-type"
    _write_json(descriptor_path, descriptor)
    with pytest.raises(build_site.BuildError):
        _build(sandbox)


def test_unknown_presentation_section_fails_the_build(sandbox):
    descriptor_path = os.path.join(sandbox["series_dir"], "alpha.json")
    with open(descriptor_path) as f:
        descriptor = json.load(f)
    descriptor["presentation"]["sections"] = ["not-a-section"]
    _write_json(descriptor_path, descriptor)
    with pytest.raises(build_site.BuildError):
        _build(sandbox)


@pytest.mark.parametrize("reserved_id", ["timeseries", "curve"])
def test_descriptor_id_colliding_with_builtin_type_fails_the_build(sandbox, reserved_id):
    _write_json(os.path.join(sandbox["series_dir"], f"{reserved_id}.json"), {
        "id": reserved_id, "title": "x", "short_title": "x", "kind": "timeseries",
        "presentation": {
            "sections": ["economy"], "order": 1, "summary": "x",
            "chart": {"type": "timeseries"}, "stats": False, "table": False,
        },
    })
    with pytest.raises(build_site.BuildError):
        _build(sandbox)


# ── Payload shape per chart type ──────────────────────────────────────────

def test_timeseries_observations_payload(sandbox):
    _build(sandbox)
    with open(os.path.join(sandbox["data_dir"], "alpha.json")) as f:
        data = json.load(f)
    assert "observations" in data or "series" in data


def test_timeseries_series_payload(sandbox):
    add = sandbox
    _write_json(os.path.join(add["data_dir"], "beta.json"), {
        "meta": {"id": "beta"}, "as_of": {},
        "series": {"leg1": {"label": "Leg 1", "observations": [{"date": "2026-01-01", "value": 1}]}},
    })
    _build(sandbox)
    with open(os.path.join(sandbox["data_dir"], "beta.json")) as f:
        data = json.load(f)
    assert "series" in data


def test_curve_tenors_payload(sandbox):
    _write_json(os.path.join(sandbox["series_dir"], "gamma.json"), {
        "id": "gamma", "title": "Gamma", "short_title": "gamma", "kind": "curve",
        "presentation": {
            "sections": ["rates"], "order": 1, "summary": "g",
            "chart": {"type": "curve"}, "stats": False, "table": True,
        },
    })
    _write_json(os.path.join(sandbox["data_dir"], "gamma.json"), {
        "meta": {"id": "gamma"}, "as_of": {}, "tenors": {"1Y": []},
    })
    _build(sandbox)
    with open(os.path.join(sandbox["data_dir"], "gamma.json")) as f:
        data = json.load(f)
    assert "tenors" in data


# ── Integration: the real repo builds cleanly (the deploy-safety check) ───

def test_real_repo_builds_into_tmp_path(tmp_path):
    """Runs the actual generator against the real series/, pages/ and data/,
    writing into a scratch directory. Must not raise — this is exactly what
    the workflow's gating pytest step relies on to keep a broken generator
    from shipping an empty deploy (design.md risk list)."""
    written = build_site.build(output_dir=str(tmp_path))
    assert written


def test_every_page_carries_the_fred_api_notice(tmp_path):
    """The FRED API Terms of Use require this sentence on any product using the
    API (site-build spec; catalog/sources/fred.json). Every page shows
    FRED-sourced data, so every generated page's footer carries it."""
    written = build_site.build(output_dir=str(tmp_path))
    pages = [p for p in written if str(p).endswith(".html")]
    assert pages
    for page in pages:
        with open(page, encoding="utf-8") as f:
            html = f.read()
        assert build_site.FRED_API_NOTICE in html, page
        assert '<footer class="site-footer">' in html, page


def test_every_presentation_chart_type_module_and_fetcher_exist():
    for series_id in series_meta.ids():
        descriptor = series_meta.load(series_id)
        presentation = descriptor.get("presentation")
        if presentation is None:
            continue

        chart_type = presentation["chart"]["type"]
        module_path = os.path.join(build_site.JS_DIR, "charts", f"{chart_type}.js")
        assert os.path.isfile(module_path), f"{series_id}: missing {module_path}"

        fetcher = descriptor.get("fetcher", f"fetch_{series_id}.py")
        fetcher_path = os.path.join(SCRIPTS_DIR, fetcher)
        assert os.path.isfile(fetcher_path), f"{series_id}: missing {fetcher_path}"


# ── Committed site/js/ source-tree checks (design.md decision 5, decision 8) ─

HEX_LITERAL_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB_LITERAL_RE = re.compile(r"\brgba?\(")
FORBIDDEN_KEYS = ("margin", "rangeslider", "height", "getElementById")
ALLOWED_FOR_FORBIDDEN_KEYS = {
    os.path.join("lib", "plotly-layout.js"),
    os.path.join("lib", "card.js"),
}


def _committed_js_files():
    js_root = os.path.join(REPO_ROOT, "site", "js")
    return glob.glob(os.path.join(js_root, "**", "*.js"), recursive=True)


def test_no_colour_literal_in_site_js():
    for path in _committed_js_files():
        text = open(path).read()
        assert not HEX_LITERAL_RE.search(text), f"{path}: hex colour literal"
        assert not RGB_LITERAL_RE.search(text), f"{path}: rgb()/rgba() colour literal"


def test_forbidden_layout_keys_confined_to_layout_and_card():
    js_root = os.path.join(REPO_ROOT, "site", "js")
    for path in _committed_js_files():
        rel = os.path.relpath(path, js_root)
        if rel in ALLOWED_FOR_FORBIDDEN_KEYS:
            continue
        text = open(path).read()
        for key in FORBIDDEN_KEYS:
            assert key not in text, f"{rel}: {key!r} used outside lib/plotly-layout.js and lib/card.js"


# ── Unpublished series (presentation.publish false) ──────────────────────

def test_unpublished_chart_is_absent_from_the_site(sandbox):
    """No page, no data file, no section entry and no nav link — the whole
    point being that a series whose terms forbid republication is never
    written into the deployed site."""
    _build(sandbox)
    out = sandbox["output_dir"]
    assert not os.path.exists(os.path.join(out, "charts", "delta"))
    assert not os.path.exists(os.path.join(out, "data", "delta.json"))

    markets = _page_json(os.path.join(out, "markets"))
    assert markets["blocks"] == []
    with open(os.path.join(out, "markets", "index.html")) as f:
        assert "/charts/delta/" not in f.read()


def test_unpublished_chart_builds_when_asked_for(sandbox):
    """scripts/dev.sh passes --include-unpublished so the chart still works
    locally."""
    _build(sandbox, include_unpublished=True)
    out = sandbox["output_dir"]
    assert os.path.isfile(os.path.join(out, "charts", "delta", "index.html"))
    assert os.path.isfile(os.path.join(out, "data", "delta.json"))
    markets = _page_json(os.path.join(out, "markets"))
    assert [b["id"] for b in markets["blocks"]] == ["delta"]


def test_curated_manifest_skips_an_unpublished_chart(sandbox):
    """pages/home.json still names the chart; the block is dropped rather
    than failing the build, so the manifest needs no edit to re-publish."""
    _write_json(os.path.join(sandbox["pages_dir"], "home.json"), {
        "slug": "home", "title": "Home", "layout": "grid",
        "blocks": [{"chart": "alpha"}, {"chart": "delta"}],
    })
    _build(sandbox)
    home = _page_json(sandbox["output_dir"])
    assert [b["id"] for b in home["blocks"]] == ["alpha"]

    _build(sandbox, include_unpublished=True)
    home = _page_json(sandbox["output_dir"])
    assert [b["id"] for b in home["blocks"]] == ["alpha", "delta"]


# Series that must carry presentation.publish false as a matter of licence, not
# preference. The generic test below proves "marked unpublished ⇒ absent from a
# default build"; this one proves the marking is still there, so flipping a flag
# fails loudly with the reason attached rather than silently publishing data we
# were refused permission to display.
LICENCE_RESTRICTED = {
    "sp500_pe": "S&P DJI declined free permission (case 01015670, 2026-09-15) and "
                "excluded 'the P/E values' even from its paid Web Display Agreement",
    "sp500_cape": "CAPE is a P/E built from S&P's price and earnings columns",
    "sp500_earnings_yield": "the inverse of a P/E built from S&P's columns",
    "sp500_dividend_yield": "S&P's dividends over S&P's price",
    "equity_risk_premium": "its equity leg is 1/CAPE, so it inherits the CAPE bar",
}


@pytest.mark.parametrize("series_id,reason", sorted(LICENCE_RESTRICTED.items()))
def test_licence_restricted_series_stay_unpublished(series_id, reason):
    """Shiller's side deferred to S&P on 2026-09-17, so every S&P-derived
    series here is settled as local-only rather than pending. Publishing one
    needs a terms decision recorded in the Session Plan, not just a flag flip.
    """
    presentation = series_meta.load(series_id).get("presentation") or {}
    assert presentation.get("publish") is False, (
        f"{series_id} must stay unpublished: {reason}. If this is a deliberate "
        "change, record the terms decision first and update LICENCE_RESTRICTED."
    )


def test_real_repo_omits_every_unpublished_series(tmp_path):
    """Whatever is marked presentation.publish false must be absent from a
    default build and present under --include-unpublished — for ALL of them,
    not just the one this was first written for.

    Parametrizing over the descriptors rather than naming ids keeps a new
    unpublished series covered the day it is added. As of S11c the set is the
    four sp500_* charts (S&P DJI declined free permission, case 01015670,
    2026-09-15; Shiller's side deferred to S&P 2026-09-17) and
    equity_risk_premium, whose CAPE yield is 1/CAPE and inherits the same bar.
    """
    unpublished = [
        series_id for series_id in series_meta.ids()
        if (series_meta.load(series_id).get("presentation") or {}).get("publish") is False
    ]
    assert unpublished, "no unpublished series found — has the publish flag moved?"

    written = build_site.build(output_dir=str(tmp_path / "public"))
    public = {os.path.relpath(p, str(tmp_path / "public")) for p in written}
    assert os.path.join("charts", "dgs10", "index.html") in public

    written_local = build_site.build(
        output_dir=str(tmp_path / "local"), include_unpublished=True,
    )
    local = {os.path.relpath(p, str(tmp_path / "local")) for p in written_local}

    for series_id in unpublished:
        assert not [p for p in public if series_id in p], (
            f"{series_id} is marked publish:false but reached a default build"
        )
        assert os.path.join("charts", series_id, "index.html") in local
        assert os.path.join("data", f"{series_id}.json") in local


def test_real_repo_omits_the_sp500_pe_chart(tmp_path):
    """The live site must not carry the S&P 500 P/E: S&P Dow Jones Indices
    declined free permission to display index values publicly (case
    01015670, 2026-09-15), so its page and data file are built locally only.
    """
    written = build_site.build(output_dir=str(tmp_path / "public"))
    public = {os.path.relpath(p, str(tmp_path / "public")) for p in written}
    assert os.path.join("charts", "dgs10", "index.html") in public
    assert not [p for p in public if "sp500_pe" in p]

    written_local = build_site.build(
        output_dir=str(tmp_path / "local"), include_unpublished=True,
    )
    local = {os.path.relpath(p, str(tmp_path / "local")) for p in written_local}
    assert os.path.join("charts", "sp500_pe", "index.html") in local
    assert os.path.join("data", "sp500_pe.json") in local
