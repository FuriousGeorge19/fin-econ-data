# Research log

One entry per productive search — a search that found nothing is productive if it stops
the next session repeating it. Newest first. Edited by the session owner only: a
workflow agent puts its research notes in its report, in this template, and the merge
step appends them here (see `catalog/README.md`).

Template:

```markdown
## YYYY-MM-DD — Short title
topics: rates, credit
- **Question**: what we were trying to find
- **Searched / read**: the queries and pages, with URLs
- **Found**: what the pages actually said
- **Outcome**: adopted | rejected | gap | open
- **Landed in**: catalog/sources/<slug>.json (dataset <id>) · series/<id>.json · Session Plan item N
```

Entries marked *back-filled* were written on 2026-09-14 from the planning notes in
Obsidian (`Conversation Synthesis.md` §4, the Session Plan) and have not been
re-verified against their pages.

---

## 2026-09-14 — Terms and access pages for the four seed sources (S8)
topics: rates, equity-valuation, recession-dating
- **Question**: what each seed source's official page actually says about access and
  republication, so the catalogue's first entries carry verified terms rather than the
  descriptors' inherited one-liners.
- **Searched / read**: FRED legal page https://fred.stlouisfed.org/legal/, FRED API terms
  https://fred.stlouisfed.org/docs/api/terms_of_use.html, API key and observations docs,
  the FRED API `/fred/series` endpoint for every family listed in `fred.json`, the FRED
  pages for SP500, EXPINF1YR, NFCI, HQMCB10YR and T10YIE (copyright labels); Shiller's
  Yale data page http://www.econ.yale.edu/~shiller/data.htm (direct fetch) and
  https://shillerdata.com/; S&P DJI terms https://www.spglobal.com/spdji/en/terms-of-use/
  and the S&P 500 index page (both 403 to automated fetches); NBER's dating-committee
  page and https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions;
  https://data.nber.org/cycles/business_cycle_dates.json.
- **Found**:
  - FRED: series labelled "Public Domain: Citation requested" and "Copyrighted: Citation
    required" may be displayed with attribution to FRED and the original source; "Pre-
    approval required" series need the owner's permission for anything beyond personal
    use. The API terms require the notice "This product uses the FRED® API but is not
    endorsed or certified by the Federal Reserve Bank of St. Louis." **The site does not
    carry that notice.** No numeric rate limit is published. EXPINF1YR and HQMCB10YR are
    public-domain labelled; NFCI and T10YIE are "Copyrighted: Citation required".
  - SP500 on FRED: S&P DJI copyright, "Reproduction of S&P 500 in any form is prohibited
    except with the prior written permission of S&P Dow Jones Indices LLC"; a new
    FRED–S&P agreement limits FRED to ten years of daily history. **The P/E chart's table
    and CSV export publish the monthly average price derived from this series** (from
    2016 on; earlier months are Shiller's).
  - Shiller: the Yale page describes ie_data.xls (monthly price, dividends, earnings, CPI,
    long rate, CAPE from January 1871) but carries no terms statement; shillerdata.com
    carries only a disclaimer. The Yale xls answered a HEAD request with Last-Modified
    2023-10-17 — the copy the fetcher downloads may no longer be refreshed.
  - S&P Global: terms and index pages return HTTP 403 to automated fetches; not read.
  - NBER: "Permission to copy is granted, provided attribution of source is given." The
    JSON chronology at data.nber.org is a list of {peak, trough} month dates from the
    1854-12-01 trough.
  - University of Michigan MICH on FRED is "Copyright, 2016, Surveys of Consumers …
    Reprinted with permission" and withholds the latest value; a third party under the
    catalogue's boundary rule, so it is not a `fred` dataset.
- **Outcome**: adopted (the four seeds) — with three **open** items below.
- **Landed in**: catalog/sources/{fred,shiller,spglobal,nber}.json;
  series/sp500_pe.json (price input now `spglobal/sp500-index`, via FRED).

## 2026-09-14 — The FRED API attribution notice was missing from the site
topics: macro
- **Question**: does joemirza.com carry the notice the FRED API Terms of Use require?
- **Searched / read**: `site/js`, `site/css`, `scripts/build_site.py`, `pages/` for
  "endorsed" / "FRED® API" — no match.
- **Found**: the terms require "This product uses the FRED® API but is not endorsed or
  certified by the Federal Reserve Bank of St. Louis." on products using the API.
- **Outcome**: adopted — the user asked for it in the same session; every generated
  page now carries the notice in a footer (`scripts/build_site.py`'s shell, styled by
  `.site-footer` in `site/css/site.css`), and the `site-build` spec says so.
- **Landed in**: scripts/build_site.py; catalog/sources/fred.json (notes).

## 2026-09-14 — Open: does publishing the P/E's monthly average S&P 500 price fit S&P's terms?
topics: equity-valuation, equity-returns
- **Question**: the P/E chart's Table and CSV include `price`, FRED's monthly average of
  SP500, for months after Shiller's last confirmed month. S&P's notice on FRED prohibits
  "reproduction of S&P 500 in any form" without written permission.
- **Searched / read**: FRED SP500 series notes; S&P DJI terms page (403, unread).
- **Found**: see the S8 entry above. The P/E ratio itself is a derived figure; the
  monthly average price column is closer to reproduction.
- **Outcome**: open — decide whether to drop `price` from the P/E table/CSV for FRED-era
  months, or request permission from index_services@spdji.com. Until decided, the
  catalogue records the terms as `restricted` and the About tab says so.
- **Landed in**: catalog/sources/spglobal.json (dataset sp500-index, notes).

## 2026-09-14 — Open: is Shiller's Yale copy of ie_data.xls still maintained?
topics: equity-valuation
- **Question**: `scripts/fetch_sp500_pe.py` downloads
  http://www.econ.yale.edu/~shiller/data/ie_data.xls; its Last-Modified header reads
  2023-10-17. shillerdata.com describes the same file.
- **Searched / read**: HEAD on the Yale xls; https://shillerdata.com/ (its download link
  is rendered by script and was not captured).
- **Found**: the confirmed/estimated split in `data/sp500_pe.json` will show where
  Shiller's confirmed months end; if the Yale copy is frozen, the confirmed history stops
  in 2023 and everything after is FRED price + the overrides file.
- **Outcome**: open — compare the two files' last month; if shillerdata.com is newer,
  point the fetcher there (an S9 research item, or S11a alongside chart 4).
- **Landed in**: catalog/sources/shiller.json (access notes).

## 2026-09-14 — Open: catalogue candidates surfaced while seeding
topics: expectations, real-estate, credit
- **Question**: which sources found in passing need their own file under the boundary
  rule, for S9's agent list.
- **Found**: University of Michigan Surveys of Consumers (`MICH` on FRED; copyrighted,
  reprinted with permission, latest value withheld) → `umich-surveys`; S&P Case-Shiller
  home price indexes on FRED (S&P DJI terms) → a dataset under `spglobal` once its FRED
  series and terms are read; ICE BofA index series on FRED (`BAML*`) → `ice-bofa`
  (chart 8 must record the terms first); U.S. Treasury daily par and real yield curve
  CSVs → `treasury-gov` (see the Aug 2026 entry).
- **Outcome**: open — S9.
- **Landed in**: nowhere yet; this entry is the pointer.

## 2026-09-13 — S&P Global's public EPS workbook is discontinued *(back-filled)*
topics: equity-valuation
- **Question**: while designing series metadata (S3), why the P/E had run on estimated
  earnings for eleven months.
- **Searched / read**: the workbook itself, `reference_resources/sp-500-eps-est.xlsx`
  (its own notice), not a web page.
- **Found**: S&P's public EPS files ended 31 January 2026. The last confirmed quarter in
  `data/earnings_overrides.json` ends 2025-09-30.
- **Outcome**: open — a replacement source for quarterly as-reported S&P 500 EPS is
  needed. No free machine-readable source is known (Uncertainty #3). Candidates to check
  in S9: S&P's index-earnings page in a browser; Damodaran's annual S&P earnings;
  multpl.com's monthly earnings table (terms unknown).
- **Landed in**: catalog/sources/spglobal.json (dataset sp-500-eps, `discontinued`);
  series/sp500_pe.json (earnings input `status: discontinued`); Session Plan decisions
  table 2026-09-13.

## 2026-08-29 — Consolidated sources for historical-context charts *(back-filled)*
topics: equity-valuation, equity-returns, global, macro
- **Question**: which chartbooks and raw archives frame current U.S. markets in
  historical context (the user's `market-history-sources.md` note).
- **Searched / read**: the note's own list; not re-verified here.
- **Found**: raw archives — FRED (+ ALFRED for vintages), Shiller/Yale, Damodaran (ERP
  since 1960, annual returns since 1928, industry multiples), Kenneth French Data
  Library (factors since 1926), Fed Z.1 Financial Accounts, Jordà-Schularick-Taylor
  Macrohistory (17–18 economies, 1870+; check licence), OFR Financial Stress Index,
  Chicago Fed NFCI. Chartbooks (design references, not feeds): JPMorgan Guide to the
  Markets, Yardeni archive PDFs, Crestmont Research, Advisor Perspectives, BlackRock
  Student of the Market, currentmarketvaluation.com, multpl.com, Koyfin, testfol.io,
  Callan periodic table, UBS Global Investment Returns Yearbook.
- **Outcome**: adopted — the seeds and the S9 agent list. Chartbooks get
  `role: reference` entries in S9.
- **Landed in**: catalog/sources/{fred,shiller}.json; Conversation Synthesis §4a/§4b;
  Session Plan S9.

## 2026-08-29 — Free data for the "what can I earn" yields table (item 11) *(back-filled)*
topics: rates, credit
- **Question**: free equivalents for each row of Fidelity's "Search by yield" grid.
- **Found**: Treasury — FRED `DGS*` (no 9-month tenor); TIPS — `DFII*`; corporate by
  maturity — Treasury HQM curve `HQMCB1YR…30YR` (monthly, public domain); corporate by
  rating — ICE BofA effective yields `BAMLC0A1CAAAEY`, `BAMLC0A2CAAEY`, `BAMLC0A3CAEY`,
  `BAMLC0A4CBBBEY`, `BAMLH0A1HYBBEY`, `BAMLH0A2HYBEY` (terms to read) and Moody's
  `DAAA`/`DBAA`; CDs — FDIC national deposit rates (retail average, not brokered
  offers); overnight — `DFF`, `SOFR`.
- **Outcome**: adopted (`fred/hqmcb`, `fred/fedfunds`, `fred/sofr`); open (ICE BofA
  terms, FDIC file location); **gap** — no free daily series for STRIPS, agency/GSE
  curves, or municipal curves (Bond Buyer indexes on FRED were discontinued); a
  purchased-data candidate.
- **Landed in**: catalog/sources/fred.json; Session Plan S11d free-data mapping.

## 2026-08-29 — Longer free daily S&P 500 history *(back-filled)*
topics: equity-returns
- **Question**: daily S&P 500 closes further back than FRED's ten-year window, for the
  risk-off-day and stock–bond-correlation tables (items 15–17).
- **Found**: FRED `SP500` carries only the trailing ten years under the S&P agreement;
  stooq.com sits behind a proof-of-work wall — skip. Shiller gives monthly, not daily.
- **Outcome**: gap — ten years is enough for items 15–17 back to 2016; a longer free
  daily history remains an open research item.
- **Landed in**: catalog/sources/spglobal.json (dataset sp500-index).

## 2026-08 — Treasury.gov daily par and real yield-curve CSVs *(back-filled)*
topics: rates
- **Question**: same-day Treasury curve data, ahead of FRED's next-day H.15 posting, and
  a TIPS curve source for items 10 and 14.
- **Found** (recipe from the 19 Aug 2026 bond-portfolio handoff §6): one CSV per year, no
  key, at `…/daily-treasury-rates.csv/<year>/all?type=daily_treasury_yield_curve` and
  `type=daily_treasury_real_yield_curve`; nominal from 1990, real from 2003. The server
  caches the current-year file — append a junk query parameter to force a fresh copy.
- **Outcome**: adopted as an S9 candidate (`treasury-gov`); not yet catalogued.
- **Landed in**: Conversation Synthesis §4a; this log.

## 2026-04 — FRED families for the fixed-income roadmap *(back-filled)*
topics: rates, inflation, credit, recession-dating
- **Question**: which FRED series carry roadmap charts 1–10 and how far back each goes
  (the fixed-income planning conversation, `reference_resources/fixed-income-charts-conversation.md`).
- **Found**: `DGS*` daily from 1962 (chart 1, 2, 9); `GS10` monthly from 1953 stitched
  to Shiller's pre-1953 long rate (chart 4); `TB3MS` from 1934 with `CPIAUCSL` for an
  ex-post real short rate (chart 5); `T10YIE`/`T5YIE` breakevens from 2003 (chart 6);
  `DFII*` TIPS from 2003 (charts 7, 10); `FEDFUNDS` from 1954 (chart 3); `USREC` from
  1854 for shading; ICE BofA `BAMLC0A0CM`/`BAMLH0A0HYM2` OAS from 1996/1997 (chart 8)
  with republication terms to read first; `T10Y2Y`/`T10Y3M` as test oracles for the
  computed spreads.
- **Outcome**: adopted — every family above is a `fred` dataset now, start dates
  verified via the FRED API on 2026-09-14; ICE BofA stays open until chart 8's terms
  reading.
- **Landed in**: catalog/sources/fred.json; ARCHITECTURE.md planned-charts table.
