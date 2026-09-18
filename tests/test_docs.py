"""Keeps the root CLAUDE.md short.

The root file loads into every Claude Code session; the nested <dir>/CLAUDE.md files load
only when a file in that directory is read, so they are not budgeted. Before the 2026-09-18
split the root was 1,362 lines, 748 of them changelog. The routing table in the root says
where each kind of fact goes instead.
"""

import os
import re

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
ROOT_CLAUDE_MD = os.path.join(REPO_ROOT, "CLAUDE.md")
LINE_BUDGET = 200
NESTED = ["series", "scripts", "site/js", "catalog", "tests"]

ROUTING = (
    "Where it goes instead: a rule -> the CLAUDE.md nearest the files it protects; "
    "what a session built -> CHANGELOG.md (<= ~15 lines) + the Obsidian handoff; "
    "a decision -> ARCHITECTURE.md's decision log or the OpenSpec change's design.md; "
    "a licence fact -> catalog/sources/<slug>.json + catalog/research-log.md; "
    "a gotcha -> HOW-IT-WORKS.md Troubleshooting; a new series/source/chart type -> nothing."
)


def _root_lines():
    with open(ROOT_CLAUDE_MD, encoding="utf-8") as f:
        return f.read().splitlines()


def test_root_claude_md_stays_within_line_budget():
    n = len(_root_lines())
    assert n <= LINE_BUDGET, (
        f"CLAUDE.md is {n} lines; the budget is {LINE_BUDGET}. {ROUTING}"
    )


def test_root_claude_md_carries_no_dated_changelog_bullets():
    dated = [ln for ln in _root_lines() if re.match(r"^- \*\*20\d\d-\d\d", ln)]
    assert not dated, (
        "CLAUDE.md has changelog-style dated bullets again; they belong in CHANGELOG.md: "
        + "; ".join(d[:60] for d in dated)
    )


def test_every_nested_claude_md_the_root_map_names_exists():
    root = "\n".join(_root_lines())
    for d in NESTED:
        assert f"`{d}/CLAUDE.md`" in root, f"root Map should name {d}/CLAUDE.md"
        assert os.path.isfile(os.path.join(REPO_ROOT, d, "CLAUDE.md")), f"{d}/CLAUDE.md missing"
