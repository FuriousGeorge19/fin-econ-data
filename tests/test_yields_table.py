"""Correctness tests for yields_table (S11d, roadmap item 11): the "what can I
earn" grid — instrument type by maturity, one FRED value per cell.

Structural checks need no network. The per-cell cross-check against FRED needs
network + FRED_API_KEY.
"""

import os
import sys

import pytest

import series_meta
from fred_utils import fetch_series

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import fetch_yields_table  # noqa: E402

requires_fred_key = pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@pytest.fixture
def grid(load_data):
    return load_data("yields_table")


# ── Structural invariants (no network) ──────────────────────────────────────

def test_rows_and_columns_match_the_fetcher_config(grid):
    assert [r["id"] for r in grid["rows"]] == [r["id"] for r in fetch_yields_table.ROWS]
    assert [c["id"] for c in grid["columns"]] == [c["id"] for c in fetch_yields_table.COLUMNS]


def test_every_cell_sits_in_a_declared_column_and_names_its_series(grid):
    column_ids = {c["id"] for c in grid["columns"]}
    spec = {r["id"]: r["cells"] for r in fetch_yields_table.ROWS}
    for row in grid["rows"]:
        for col, cell in row["cells"].items():
            assert col in column_ids, f"{row['id']}: unknown column {col}"
            assert cell["series_id"] == spec[row["id"]][col], (row["id"], col)


def test_columns_are_ordered_by_maturity(grid):
    months = [c["months"] for c in grid["columns"]]
    assert months == sorted(months) and len(set(months)) == len(months)


def test_a_missing_series_leaves_a_blank_not_a_number(grid):
    # No 9-month or 1-month column exists, and TIPS has nothing under 5 years;
    # those cells must be absent rather than filled.
    tips = next(r for r in grid["rows"] if r["id"] == "tips")
    assert set(tips["cells"]) <= {"5Y", "7Y", "10Y", "20Y", "30Y"}
    for row in grid["rows"]:
        for cell in row["cells"].values():
            assert cell["value"] is not None


def test_overnight_rates_only_fill_the_overnight_column(grid):
    for rid in ("fedfunds", "sofr"):
        row = next(r for r in grid["rows"] if r["id"] == rid)
        assert list(row["cells"]) == ["ON"]


def test_values_are_plausible_percent_yields(grid):
    # Percent, not a decimal fraction: a 4.5% yield stored as 0.045 would pass
    # a bare > 0 check, so the range starts well above that.
    for row in grid["rows"]:
        for col, cell in row["cells"].items():
            assert -3 < cell["value"] < 15, (row["id"], col, cell["value"])
    treasury = next(r for r in grid["rows"] if r["id"] == "treasury")
    assert any(c["value"] > 1 for c in treasury["cells"].values())


def test_row_as_of_is_its_newest_cell_and_cells_never_postdate_it(grid):
    for row in grid["rows"]:
        dates = [c["date"] for c in row["cells"].values()]
        assert row["as_of"] == max(dates), row["id"]


def test_every_row_input_exists_in_the_descriptor_and_the_as_of_block(grid):
    descriptor = series_meta.load("yields_table")
    input_ids = {i["id"] for i in descriptor["inputs"]}
    for row in grid["rows"]:
        assert row["input"] in input_ids, row["id"]
        assert row["input"] in grid["as_of"]["inputs"], row["id"]


def test_each_input_last_observation_is_its_rows_newest_date(grid):
    newest = {}
    for row in grid["rows"]:
        newest[row["input"]] = max(newest.get(row["input"], ""), row["as_of"])
    for input_id, entry in grid["as_of"]["inputs"].items():
        assert entry["last_observation"] == newest[input_id], input_id


def test_the_monthly_corporate_row_is_judged_on_a_monthly_clock(grid):
    # The point of one input per row: the corporate curve is published monthly,
    # so its due_by lands a month after Treasury's for the same fetch.
    hqm = grid["as_of"]["inputs"]["hqm"]
    treasury = grid["as_of"]["inputs"]["treasury"]
    assert hqm["due_by"] > treasury["due_by"] or hqm["last_observation"] < treasury["last_observation"]
    assert grid["as_of"]["due_by"] == min(e["due_by"] for e in grid["as_of"]["inputs"].values())


def test_the_ratings_rows_the_source_terms_forbid_are_not_here(grid):
    # ICE BofA rating yields are `restricted` (see series/yields_table.json
    # notes); a BAML* series reaching this grid would need publish: false.
    for row in grid["rows"]:
        for cell in row["cells"].values():
            assert not cell["series_id"].startswith("BAML"), cell["series_id"]


def test_treasury_row_agrees_with_the_yield_curve_fixture_when_dates_coincide(grid, load_data):
    curve = load_data("yield_curve")
    tenor = {"3M": "3mo", "6M": "6mo", "1Y": "1yr", "2Y": "2yr", "3Y": "3yr",
             "5Y": "5yr", "7Y": "7yr", "10Y": "10yr", "20Y": "20yr", "30Y": "30yr"}
    treasury = next(r for r in grid["rows"] if r["id"] == "treasury")
    checked = 0
    for col, cell in treasury["cells"].items():
        observed = curve["observations"].get(cell["date"], {}).get(tenor[col])
        if observed is None:
            continue
        assert observed == pytest.approx(cell["value"], abs=0.005), (col, cell["date"])
        checked += 1
    if not checked:
        pytest.skip("yield_curve.json fixture does not reach the grid's date")


# ── Live cross-check ────────────────────────────────────────────────────────

@requires_fred_key
@pytest.mark.network
def test_every_cell_matches_a_direct_fred_pull_on_its_own_date(grid):
    checked = 0
    for row in grid["rows"]:
        for col, cell in row["cells"].items():
            window = fetch_series(
                cell["series_id"], sort_order=None,
                extra_params={"observation_start": cell["date"], "observation_end": cell["date"]},
            )
            assert window, f"{cell['series_id']} has no observation on {cell['date']}"
            assert window[0]["value"] == pytest.approx(cell["value"], abs=0.005), (row["id"], col)
            checked += 1
    assert checked == sum(len(r["cells"]) for r in grid["rows"]) == 26


# ── Freshness on each row's own clock (synthetic, no fixture dependence) ────

def test_each_row_is_judged_on_its_own_publication_clock():
    from datetime import date
    from staleness import compute_due_by

    # August's corporate curve is due 2026-10-06 (next month end + 4 business
    # days), so on 2026-09-18 that row is on time.
    assert compute_due_by(date(2026, 8, 1), "monthly", 4) == date(2026, 10, 6)
    # A daily row last seen Monday 2026-09-14 is due Wednesday 2026-09-16
    # (Tuesday's period end + 1 business day), so it is overdue from the 17th.
    assert compute_due_by(date(2026, 9, 14), "daily", 1) == date(2026, 9, 16)
