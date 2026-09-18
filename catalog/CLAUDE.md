# catalog/ — source inventory rules, and where the terms stand (loads when a catalogue file is read)

The rules and field table are `catalog/README.md`, which is what a research agent is handed.
The schema's authority is `scripts/catalog.py`: `python3 scripts/catalog.py check [path]`
until it prints nothing; `report [--topic T]` prints sources × datasets × used-by × terms.
`catalog/research-log.md` holds productive searches, newest first. The rules most often broken:

1. One file per rights holder. A dataset gets its own file only when its terms differ from
   its host's (S&P DJI's `SP500` and ICE BofA's `BAML*` on FRED) or the publisher serves it
   directly. Public-domain data reached through FRED is a `datasets[]` entry in `fred.json` —
   **a new FRED family needs that entry before a descriptor can resolve it**
   (`resolve_source_ref` raises at fetch time otherwise).
2. Hosted data says `via`; a dataset's `access`/`terms` merge over the source's, key by key.
3. `"unknown"` means you looked and could not establish it; an absent field means nobody
   looked. Never guess.
4. Every fact block carries `read_from` (official pages only). A verifier treats a block
   without one as unverified.
5. Never store which series use a source; the report derives it from `series/*.json`.
   Every file carries `verified {on, by}` saying when and by whom it was last checked.
6. `research-log.md` is edited by the session owner only. An agent puts its notes in its
   report, in the README's entry template.

## Terms status of the sources the site depends on

**The rule**: before a series carries `publish: true`, every `sources[]` entry must resolve
`verified` — or the user has recorded a decision in the Session Plan — and the id must not
be in `tests/test_build_site.py`'s `LICENCE_RESTRICTED`. The About tab shows any status that
isn't `verified`. Quotes, URLs and dates live in each `catalog/sources/<slug>.json`; the
narrative in `research-log.md`; the pre-split prose in `CHANGELOG.md`'s frozen Licence Notes.

| Source | Status | What it means here |
|---|---|---|
| `fred` | verified | Public-domain and citation-required series display with attribution to FRED and the originator. Third-party "pre-approval required" series (`BAML*`, `SP500`) are catalogued under their own rights holder, never as `fred` datasets. FRED's API terms require the notice every generated page carries in its footer (`FRED_API_NOTICE` in `build_site.py`, tested). |
| `spglobal` (S&P DJI: `SP500` via FRED, the EPS workbook) | restricted | Refused free permission 2026-09-15 (case 01015670): public display is a paid Web Display Agreement, about US$8,000/year for one index and ten years of levels, "but not the P/E values". Consequence: `sp500_pe`, `sp500_cape`, `sp500_dividend_yield`, `sp500_earnings_yield`, `equity_risk_premium` are `publish: false`, settled. |
| `shiller` (`ie_data.xls`) | unknown | No terms page. Shiller's index advisor answered 2026-09-17: they license nothing and "you will certainly have to adhere to S&P's wishes". Every column built from S&P price, dividends or earnings follows `spglobal`. The pre-1953 long-rate column has no S&P component; the user decided 2026-09-17 it publishes (`gs10_long`). |
| `nber` | verified | "Permission to copy is granted, provided attribution of source is given." |
| `ice-bofa` (`BAML*` via FRED) | restricted | Pre-approval required, and FRED keeps a rolling three years (every series starts 2023-09-18). Chart 8 was rescoped onto Moody's; item 11's by-rating rows were dropped. |
| `fred` dataset `moodys-corporate` (`AAA`/`BAA`) | verified | Citation required. `credit_spread_baa_aaa`, monthly from 1919. |
| `damodaran`, `federal-reserve-board` (Z.1) | verified | The public S10 equity-valuation candidates, not yet built. |
| `umich-surveys`, `philadelphia-fed`, `jst-macrohistory`, most chartbooks | restricted | Catalogued, unused. `fdic` deposit rates are `unknown` and on hold (user, 2026-09-18). |
