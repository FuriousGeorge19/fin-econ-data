# tests/ — what each suite guards (loads when a test is read)

Run: `pip install -r requirements-test.txt && FRED_API_KEY=… pytest`. Markers (`pytest.ini`):
`network` (needs network and the key; skips itself without either) and `staleness` (freshness
against today's US Eastern date; `-m "not staleness"` is the deploy gate; `STALENESS_SOURCE=local`
checks `data/` instead of the live site, which is what CI does right after its fetch).

| File | Guards |
|---|---|
| `test_data_integrity.py` | dates unique and monotone, no `"."` became 0, the P/E's arithmetic and confirmed/estimated boundary. No network |
| `test_series_metadata.py` | the descriptor schema (`REQUIRED_FIELDS`, enums, `presentation` keys, presets grammar, `sections` ⊆ `pages/site.json`), `data/*.json` `meta` agreeing with its descriptor, `as_of.due_by` recomputing, the calendar and period-label fixtures |
| `test_build_site.py` | the real generator against real inputs into a scratch dir (what stops an empty deploy); a sandbox test per validation failure; the unpublished and view cases; the FRED notice footer; the two `site/js` greps (no colour literal; `margin`/`rangeslider`/`height`/`getElementById` only in `lib/plotly-layout.js` and `lib/card.js`); `LICENCE_RESTRICTED` |
| `test_catalog.py` | every catalogue file validates; every descriptor reference resolves; the `check`/`report` CLIs |
| `test_fred_utils.py` | the shared FRED helper, mocked |
| `test_staleness.py` | each dataset's and input's `due_by` (marker `staleness`) |
| `test_<id>.py`, one per data-owning series | structural invariants, a live cross-check against the source (FRED or shillerdata.com), canaries for facts the fetcher assumes (a FRED start date, `CUTOVER`) |
| `test_tenor_history.py` | the view wiring; DGS20's 1987–1993 gap is the only long one |
| `test_docs.py` | root `CLAUDE.md` ≤ 200 lines, no dated bullets, the nested files exist |

Conventions:

- Parametrize a cross-cutting test over `series_meta.ids()` (or `DATA_OWNING_IDS` to skip
  views) rather than adding a fixture per series to `conftest.py`; `conftest.py`'s
  `load_data` fixture reads any `data/<id>.json`.
- A test whose comment describes a check must assert that check. A five-line comment about
  the `"."` sentinel above `len(observations) > 0` was an S11b verifier finding.
- Sentinel guards are range guards, never `value > 0`: a 0.00 ZIRP month is real.
- Live cross-checks use `requires_fred_key` (or the `network` marker) and sample the
  oldest, a middle and the newest date.
- Where a sign convention could invert silently, assert the story (the ERP is negative at
  the 2000 peak, at its maximum in August 1982).
- `data/*.json` on `main` are fixtures. Regenerate one by running its fetcher; the live site
  is always fresher — see the data-flow note in the root `CLAUDE.md`.
- `network` tests can flake on a socket timeout; rerun once before blaming a change.
