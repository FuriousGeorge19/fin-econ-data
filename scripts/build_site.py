#!/usr/bin/env python3
"""Generates the multi-page static site from series descriptors and page
manifests. Stdlib only — no JavaScript toolchain, no templating library.

Inputs: `pages/site.json` (site name + sections), every `series/<id>.json`
(read directly, so a `presentation` block is available — the copy embedded
into a data file's `meta` has `presentation` stripped, see
`scripts/series_meta.py`), and every `pages/<slug>.json` manifest.

Outputs, under `site/` (all generated paths, gitignored per
openspec/changes/s5-chart-components/design.md decision 2):
  - `charts/<id>/index.html` for every descriptor that carries `presentation`
  - `<section>/index.html` for each of the three sections: an automatic grid
    of that section's charts, `half` size, sorted by `presentation.order`
  - `<section>/<slug>/index.html` for every manifest that names a `section`
  - `index.html` for `pages/home.json`, but ONLY if that file exists — the
    single-file dashboard at `/` stays live and untouched until cutover
  - `data/<id>.json`, copied verbatim from `data/<id>.json`

Rerun after editing a descriptor's `presentation`, adding a series, or
editing a page manifest. `scripts/dev.sh` and the deploy workflow both call
this before serving/publishing `site/`.
"""

import glob
import html
import json
import os
import re
import shutil
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SERIES_DIR = os.path.join(REPO_ROOT, "series")
PAGES_DIR = os.path.join(REPO_ROOT, "pages")
DATA_DIR = os.path.join(REPO_ROOT, "data")
SITE_DIR = os.path.join(REPO_ROOT, "site")
JS_DIR = os.path.join(SITE_DIR, "js")

PLOTLY_SCRIPT = "https://cdn.plot.ly/plotly-2.35.0.min.js"

# `chart.presets` grammar: a count plus M(onth)/Y(ear), or the literals YTD/All.
PRESET_RE = re.compile(r"^(\d+[MY]|YTD|All)$")

# Names a `presentation.chart.type` may never take, because they would
# collide with the built-in chart types shipped in site/js/charts/.
RESERVED_TYPE_NAMES = {"timeseries", "curve"}

PAYLOAD_KEYS_BY_TYPE = {
    "timeseries": ("series", "observations"),
    "curve": ("tenors",),
}


class BuildError(Exception):
    """A validation failure that must stop the build before anything is
    written — see design.md decision 1.3's fail-list. The message names the
    offending file/value so a broken deploy step points straight at the fix."""


# ── Loading ──────────────────────────────────────────────────────────────


def load_site(pages_dir):
    path = os.path.join(pages_dir, "site.json")
    with open(path) as f:
        return json.load(f)


def load_descriptors(series_dir):
    """`{id: descriptor}` for every `series/<id>.json`, in the raw form on
    disk — unlike `series_meta.load()`, this keeps `presentation`, since
    that block is what the generator exists to read."""
    descriptors = {}
    for path in sorted(glob.glob(os.path.join(series_dir, "*.json"))):
        series_id = os.path.splitext(os.path.basename(path))[0]
        with open(path) as f:
            descriptors[series_id] = json.load(f)
    return descriptors


def load_manifests(pages_dir):
    """`{slug: manifest}` for every `pages/<slug>.json` except `site.json`."""
    manifests = {}
    for path in sorted(glob.glob(os.path.join(pages_dir, "*.json"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        if slug == "site":
            continue
        with open(path) as f:
            manifests[slug] = json.load(f)
    return manifests


# ── Validation (design.md decision 1.3) ─────────────────────────────────


def validate(*, site, descriptors, manifests, js_dir):
    section_ids = {s["id"] for s in site["sections"]}

    for series_id, descriptor in descriptors.items():
        if series_id in RESERVED_TYPE_NAMES:
            raise BuildError(
                f"series/{series_id}.json: id {series_id!r} collides with a "
                f"built-in chart type name"
            )
        presentation = descriptor.get("presentation")
        if presentation is None:
            continue

        unknown_sections = set(presentation.get("sections", [])) - section_ids
        if unknown_sections:
            raise BuildError(
                f"series/{series_id}.json: presentation.sections "
                f"{sorted(unknown_sections)} not in pages/site.json"
            )

        chart = presentation.get("chart", {})
        chart_type = chart.get("type")
        if chart_type:
            module_path = os.path.join(js_dir, "charts", f"{chart_type}.js")
            if not os.path.isfile(module_path):
                raise BuildError(
                    f"series/{series_id}.json: presentation.chart.type "
                    f"{chart_type!r} has no module at "
                    f"{os.path.relpath(module_path, REPO_ROOT)}"
                )

        for preset in chart.get("presets", []):
            if not PRESET_RE.match(preset):
                raise BuildError(
                    f"series/{series_id}.json: preset {preset!r} does not "
                    f"match ^\\d+[MY]$|YTD|All"
                )

    for slug, manifest in manifests.items():
        section = manifest.get("section")
        if section is not None and section not in section_ids:
            raise BuildError(
                f"pages/{slug}.json: section {section!r} not in pages/site.json"
            )
        for block in manifest.get("blocks", []):
            chart_id = block.get("chart")
            if chart_id is None:
                continue
            descriptor = descriptors.get(chart_id)
            if descriptor is None or descriptor.get("presentation") is None:
                raise BuildError(
                    f"pages/{slug}.json: block names chart {chart_id!r}, "
                    f"which has no series/{chart_id}.json presentation block"
                )


# ── Derived structure ────────────────────────────────────────────────────


def charts_with_presentation(descriptors):
    return {
        series_id: d for series_id, d in descriptors.items()
        if d.get("presentation") is not None
    }


def section_charts(section_id, chartable):
    """Descriptors placed on `section_id`, sorted by `presentation.order`."""
    return sorted(
        (d for d in chartable.values() if section_id in d["presentation"]["sections"]),
        key=lambda d: d["presentation"]["order"],
    )


def section_composites(section_id, manifests):
    """Composite-page manifests placed on `section_id`, sorted by title for
    a deterministic nav — no ordering field is defined for composite pages."""
    return sorted(
        (m for slug, m in manifests.items() if m.get("section") == section_id),
        key=lambda m: m["title"],
    )


# ── Blocks and inline page JSON ──────────────────────────────────────────


def chart_block(descriptor, *, size, preset=None):
    block = {
        "id": descriptor["id"],
        "title": descriptor["title"],
        "short_title": descriptor["short_title"],
        "summary": descriptor["presentation"]["summary"],
        "href": f"/charts/{descriptor['id']}/",
        "presentation": descriptor["presentation"],
        "size": size,
    }
    if preset:
        block["preset"] = preset
    return block


def text_block(text):
    return {"text": text}


def manifest_blocks(manifest, chartable):
    blocks = []
    for raw in manifest.get("blocks", []):
        if "chart" in raw:
            descriptor = chartable[raw["chart"]]
            blocks.append(chart_block(
                descriptor, size=raw.get("size", "half"), preset=raw.get("preset"),
            ))
        elif "text" in raw:
            blocks.append(text_block(raw["text"]))
    return blocks


# ── HTML rendering ─────────────────────────────────────────────────────


def _link(href, label, *, current_href):
    current = ' aria-current="page" class="current"' if href == current_href else ""
    return f'<a href="{html.escape(href)}"{current}>{html.escape(label)}</a>'


def render_nav(*, site, current_href, current_section, chartable, manifests):
    top_items = [_link("/", site["name"], current_href=current_href)]
    for section in site["sections"]:
        href = f'/{section["id"]}/'
        top_items.append(_link(href, section["label"], current_href=current_href))
    rows = [f'<nav class="nav-primary">{"".join(top_items)}</nav>']

    if current_section is not None:
        section_items = []
        for d in section_charts(current_section, chartable):
            section_items.append(_link(
                f'/charts/{d["id"]}/', d["short_title"], current_href=current_href,
            ))
        for slug, m in manifests.items():
            if m.get("section") != current_section:
                continue
            section_items.append(_link(
                f'/{current_section}/{slug}/', m["title"], current_href=current_href,
            ))
        rows.append(f'<nav class="nav-section">{"".join(section_items)}</nav>')

    return "\n".join(rows)


# Required verbatim by the FRED API Terms of Use
# (https://fred.stlouisfed.org/docs/api/terms_of_use.html) on any product that
# uses the API; every page shows FRED-sourced data, so every page carries it.
# See catalog/sources/fred.json and the site-build spec.
FRED_API_NOTICE = (
    "This product uses the FRED® API but is not endorsed or certified by the "
    "Federal Reserve Bank of St. Louis."
)


def render_shell(*, title, nav_html, blocks_html, page_json, chart_css):
    css_links = "\n".join(
        f'    <link rel="stylesheet" href="/css/charts/{name}.css">'
        for name in chart_css
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="/css/site.css">
{css_links}
<script src="{PLOTLY_SCRIPT}"></script>
</head>
<body>
{nav_html}
<main>
{blocks_html}
</main>
<footer class="site-footer">
<p>{FRED_API_NOTICE}</p>
</footer>
<script type="application/json" id="page">{json.dumps(page_json)}</script>
<script type="module" src="/js/app.js"></script>
</body>
</html>
"""


def render_blocks(blocks):
    """One placeholder element per block; `card.js` (S6b) builds the actual
    card DOM from the matching entry in the inline `#page` JSON."""
    parts = []
    for i, block in enumerate(blocks):
        if "text" in block:
            parts.append(f'<div class="text-block" data-block="{i}"></div>')
        else:
            parts.append(f'<div class="card" data-block="{block["id"]}"></div>')
    return "\n".join(parts)


def chart_css_names(site_dir):
    css_dir = os.path.join(site_dir, "css", "charts")
    if not os.path.isdir(css_dir):
        return []
    return sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(css_dir, "*.css"))
    )


# ── Page writers ─────────────────────────────────────────────────────────


def write_page(output_dir, rel_path, contents, written):
    path = os.path.join(output_dir, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(contents)
    written.append(path)


def build_chart_page(descriptor, *, site, chartable, manifests, output_dir, chart_css, written):
    block = chart_block(descriptor, size="full")
    sections = descriptor["presentation"]["sections"]
    primary_section = sections[0] if sections else None
    page = {"slug": descriptor["id"], "title": descriptor["title"], "layout": "single"}
    nav_html = render_nav(
        site=site, current_href=f'/charts/{descriptor["id"]}/',
        current_section=primary_section, chartable=chartable, manifests=manifests,
    )
    contents = render_shell(
        title=f'{descriptor["title"]} — {site["name"]}',
        nav_html=nav_html,
        blocks_html=render_blocks([block]),
        page_json={"page": page, "blocks": [block]},
        chart_css=chart_css,
    )
    write_page(output_dir, os.path.join("charts", descriptor["id"], "index.html"), contents, written)


def build_section_page(section, *, site, chartable, manifests, output_dir, chart_css, written):
    blocks = [chart_block(d, size="half") for d in section_charts(section["id"], chartable)]
    page = {"slug": section["id"], "title": section["label"], "layout": "grid"}
    nav_html = render_nav(
        site=site, current_href=f'/{section["id"]}/',
        current_section=section["id"], chartable=chartable, manifests=manifests,
    )
    contents = render_shell(
        title=f'{section["label"]} — {site["name"]}',
        nav_html=nav_html,
        blocks_html=render_blocks(blocks),
        page_json={"page": page, "blocks": blocks},
        chart_css=chart_css,
    )
    write_page(output_dir, os.path.join(section["id"], "index.html"), contents, written)


def build_manifest_page(slug, manifest, *, site, chartable, manifests, output_dir, chart_css, written):
    blocks = manifest_blocks(manifest, chartable)
    page = {
        "slug": slug,
        "title": manifest["title"],
        "layout": manifest.get("layout", "grid"),
    }
    if "intro" in manifest:
        page["intro"] = manifest["intro"]

    section = manifest.get("section")
    is_home = section is None
    href = "/" if is_home else f'/{section}/{slug}/'
    nav_html = render_nav(
        site=site, current_href=href, current_section=section,
        chartable=chartable, manifests=manifests,
    )
    contents = render_shell(
        title=f'{manifest["title"]} — {site["name"]}' if not is_home else site["name"],
        nav_html=nav_html,
        blocks_html=render_blocks(blocks),
        page_json={"page": page, "blocks": blocks},
        chart_css=chart_css,
    )
    rel_path = "index.html" if is_home else os.path.join(section, slug, "index.html")
    write_page(output_dir, rel_path, contents, written)


def copy_data(*, descriptors, data_dir, output_dir, written):
    data_out = os.path.join(output_dir, "data")
    os.makedirs(data_out, exist_ok=True)
    for series_id in descriptors:
        src = os.path.join(data_dir, f"{series_id}.json")
        if not os.path.isfile(src):
            continue
        dst = os.path.join(data_out, f"{series_id}.json")
        shutil.copyfile(src, dst)
        written.append(dst)


# ── Entry point ──────────────────────────────────────────────────────────


def build(*, series_dir=SERIES_DIR, pages_dir=PAGES_DIR, data_dir=DATA_DIR,
           output_dir=SITE_DIR, js_dir=JS_DIR):
    """Runs the generator; returns the list of paths written. Raises
    `BuildError` (naming the offending file) on a validation failure —
    nothing is written in that case."""
    site = load_site(pages_dir)
    descriptors = load_descriptors(series_dir)
    manifests = load_manifests(pages_dir)

    validate(site=site, descriptors=descriptors, manifests=manifests, js_dir=js_dir)

    chartable = charts_with_presentation(descriptors)
    chart_css = chart_css_names(output_dir)
    written = []

    for descriptor in chartable.values():
        build_chart_page(
            descriptor, site=site, chartable=chartable, manifests=manifests,
            output_dir=output_dir, chart_css=chart_css, written=written,
        )

    for section in site["sections"]:
        build_section_page(
            section, site=site, chartable=chartable, manifests=manifests,
            output_dir=output_dir, chart_css=chart_css, written=written,
        )

    for slug, manifest in manifests.items():
        if manifest.get("section") is None:
            continue  # home.json (no section) is handled separately below
        build_manifest_page(
            slug, manifest, site=site, chartable=chartable, manifests=manifests,
            output_dir=output_dir, chart_css=chart_css, written=written,
        )

    # Migration rule (design.md decision 2): the single-file dashboard stays
    # live at `/` until pages/home.json exists, i.e. until cutover.
    if "home" in manifests:
        build_manifest_page(
            "home", manifests["home"], site=site, chartable=chartable,
            manifests=manifests, output_dir=output_dir, chart_css=chart_css,
            written=written,
        )

    copy_data(descriptors=descriptors, data_dir=data_dir, output_dir=output_dir, written=written)

    return written


def main():
    try:
        written = build()
    except BuildError as e:
        print(f"build_site.py: {e}", file=sys.stderr)
        sys.exit(1)

    for path in written:
        print(os.path.relpath(path, REPO_ROOT))


if __name__ == "__main__":
    main()
