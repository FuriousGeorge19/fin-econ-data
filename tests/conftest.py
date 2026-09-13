"""Shared fixtures for the correctness test suite.

Fixtures load the committed JSON in `data/` — these are the files the deployed
site actually reads via `site/data/` (see CLAUDE.md's data-flow note: the
workflow copies `data/` → `site/data/` but never commits fetched data back to
`main`, so what's committed here can lag what's live).

Tests that call the FRED API directly (to cross-check a fetcher's output
against an independent pull) are marked `@pytest.mark.network` and skipped
automatically when FRED_API_KEY is unset.
"""

import json
import os

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(REPO_ROOT, "data")

SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
import sys
sys.path.insert(0, SCRIPTS_DIR)


def load_json(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


@pytest.fixture
def dgs10():
    return load_json("dgs10.json")


@pytest.fixture
def sp500_pe():
    return load_json("sp500_pe.json")


@pytest.fixture
def yield_curve():
    return load_json("yield_curve.json")


@pytest.fixture
def spreads():
    return load_json("spreads.json")


@pytest.fixture
def usrec():
    return load_json("usrec.json")


def has_fred_key():
    return bool(os.environ.get("FRED_API_KEY"))


requires_fred_key = pytest.mark.skipif(
    not has_fred_key(), reason="FRED_API_KEY not set — skipping live network check"
)
