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

## 2026-09-16 — S10 dry run: charts for US Equity Valuations, proposed from the catalogue alone
topics: equity-valuation, equity-returns, macro
- **Question**: can the catalogue, on its own, recommend a set of charts for a US Equity
  Valuations page, name each source's `terms.status`, say which charts can go on the
  public site, and name the gaps — the Session Plan's S10 test of whether the inventory
  does what [[What I Want]] asks.
- **Searched / read**: `python3 scripts/catalog.py report --topic equity-valuation` and
  the full report; every `series/*.json`; `catalog/sources/{shiller,spglobal,damodaran,
  federal-reserve-board,multpl,fred,ofr}.json` and the S9 entries below. No web
  searches. Four FRED API `/fred/series` lookups and two FRED series pages, for the
  one addition the brief allowed (GDP) and for Z.1 line ids the catalogue named but
  hadn't resolved (next two entries).
- **Found**: four charts buildable for the public site from verified-terms sources
  alone — Buffett indicator (Z.1 public corporate equities ÷ BEA GDP), Damodaran's
  implied ERP (annual, 1960–), household allocation to equities (Z.1 B.101), and a
  Tobin's Q proxy (Z.1's own `NCBCEPNW`). Every price- or earnings-based chart (CAPE,
  trailing P/E, earnings yield vs real yield, dividend yield, real price) depends on
  Shiller's `ie_data.xls` (terms `unknown`) and on S&P Composite price and S&P earnings
  inside it, so all are local-only until Shiller's terms are established. Roadmap
  chart 7 (ERP, S11c) as scoped uses `sp500_pe` and is therefore local-only too;
  rebuilding it on the CAPE yield makes it share CAPE's fate instead. Forward P/E has
  no source; nominal as-reported EPS has none but Shiller's own earnings column.
- **Outcome**: adopted (the proposal); open (Shiller's terms); gap (forward P/E)
- **Landed in**: Obsidian `S10 — US Equity Valuations — Chart Proposals.md` · Session
  Plan S10 row and Phase 4 · catalog/sources/fred.json (dataset gdp) ·
  catalog/sources/federal-reserve-board.json (dataset notes)

## 2026-09-16 — FRED GDP as the Buffett-indicator denominator
topics: macro, equity-valuation
- **Question**: the catalogue had no GDP series; the S10 brief allowed one unlisted
  FRED series if recorded. Which one, and under what label?
- **Searched / read**: https://api.stlouisfed.org/fred/series?series_id=GDP and
  https://fred.stlouisfed.org/series/GDP.
- **Found**: `GDP` — Gross Domestic Product, BEA, quarterly, seasonally adjusted annual
  rate, billions of dollars, from 1947-01-01; latest observation 2026-04-01 (Q2 2026,
  $32,486bn), last updated on FRED 2026-08-26. FRED's label: "Public Domain: Citation
  Requested". Revised after first publication (advance, second, third estimate), unlike
  every series the site fetches today.
- **Outcome**: adopted
- **Landed in**: catalog/sources/fred.json (dataset gdp)

## 2026-09-16 — Z.1 lines for total equity market value, household fund shares and Tobin's Q, with FRED ids
topics: equity-valuation, equity-returns, macro
- **Question**: S9 catalogued the Z.1 tables (L.224, B.101, B.103) and one FRED mirror
  each, and left "which line" open for the Buffett indicator. Which FRED ids carry the
  whole-economy equity total, the household fund-share leg, and a Tobin's Q ratio?
- **Searched / read**: FRED API `/fred/series/search` for "all sectors corporate
  equities liability level", "households nonprofit mutual fund shares asset level",
  "nonfinancial corporate business net worth level"; `/fred/series/observations`
  (latest value) for each id; https://fred.stlouisfed.org/series/BOGZ1LM883164105Q.
- **Found**: `BOGZ1LM883164105Q` All Domestic Sectors; Corporate Equities; Liability,
  Market Value Levels (from 1945-10-01; Q2 2026 $109.2tn) and `BOGZ1LM883164115Q` the
  same table's *Public* Corporate Equities line ($93.6tn), against `NCBEILQ027S`
  nonfinancial corporate only ($83.1tn). Against GDP that is 336% / 288% / 256% — the
  line choice moves the indicator by a third. Household side: `HNOMFAQ027S` mutual fund
  shares and `BOGZ1FL153064005Q` equities + non-MMF fund shares (from 1945-10-01; Q2
  2026 $69.2tn, 35% of `TNWBSHNO` net worth $195.9tn). Tobin's Q: the Board publishes
  `NCBCEPNW` Corporate Equities as a Percentage of Net Worth directly (242% in Q2
  2026), with `TNWMVBSNNCB` as net worth at market value. All are Z.1 release 52
  series under the Board's public-domain terms; the one page read carries "Public
  Domain: Citation Requested".
- **Outcome**: adopted — the S10 proposal recommends the public-equities line for the
  Buffett indicator and `NCBCEPNW` for Tobin's Q.
- **Landed in**: catalog/sources/federal-reserve-board.json (notes and read_from on
  datasets l224-corporate-equities, b101-household-balance-sheet,
  b103-nonfinancial-corporate-leverage)

## 2026-09-16 — Forward P/E, price/sales and price/book: what the catalogue's silence means
topics: equity-valuation
- **Question**: which US equity-valuation measures the catalogue cannot supply, and
  whether each silence follows a search or just an unassigned topic.
- **Searched / read**: the catalogue only (every `equity-valuation`-tagged dataset,
  `damodaran/industry-pe`'s notes) and the S9 EPS-replacement entries below.
- **Found**: forward P/E — no dataset carries analyst estimates; `damodaran/industry-pe`
  has a forward P/E market total, but as a once-a-year snapshot overwritten in place,
  no history. S9's EPS survey (multpl, Siblis, FactSet, Damodaran) covered the free
  candidates, so this is a searched gap; the data lives with FactSet and S&P Capital
  IQ, paid. Price/sales, price/book and profit margins — no dataset and no log entry,
  because no S9 agent was assigned the topic: an unresearched gap, not a finding.
- **Outcome**: gap (forward P/E, searched) · open (price multiples other than P/E,
  unresearched — a candidate for the next research workflow)
- **Landed in**: Session Plan Phase 4 (US Equity Valuations row)

## 2026-09-16 — Open: Shiller's terms decide every price- or earnings-based valuation chart
topics: equity-valuation
- **Question**: which of the S10 proposals could go on the public site, given that
  `shiller/ie-data` is `unknown` and its price and earnings columns are S&P's data.
- **Searched / read**: catalog/sources/shiller.json (terms, both pages re-read in S9:
  no statement) and spglobal.json (S&P's 2026-09-15 answer, which excludes "the P/E
  values" even from the paid licence).
- **Found**: CAPE, dividend yield, real price since 1871, and an ERP built on the
  earnings or CAPE yield all come from the same file and share the same status. The
  arguments each way are set out in the proposal's §3; neither settles it. The file's
  maintainer (shillerdata.com; the workbook's metadata names Laurence Black) has not
  been asked.
- **Outcome**: open — the user's decision. Recommended: build the charts locally in
  S9b (`presentation.publish: false`), and ask by email before publishing any of them.
- **Landed in**: Session Plan open items · Obsidian `S10 — US Equity Valuations —
  Chart Proposals.md` §3

## 2026-09-16 — S&P answered: displaying index values publicly is a paid licence
topics: equity-valuation, equity-returns
- **Question**: may joemirza.com keep publishing the S&P 500 P/E chart, whose price is
  FRED's monthly average of SP500 and whose earnings come from S&P's own workbook?
- **Searched / read**: the reply thread from S&P Index Client Services (case 01015670,
  2026-09-15), alongside the terms read in a browser the day before
  (https://www.spglobal.com/spdji/en/disclaimers/).
- **Found**: S&P charges for display of index values in charts on public websites —
  US$8,000/year for one headline index under a Web Display Agreement, which allows up
  to ten years of index levels "but not the P/E values". Nothing free was offered for
  personal, non-commercial use. FRED's own legal page already limited third-party
  series to "your own personal use" without the owner's permission.
- **Outcome**: adopted — the chart is no longer published. `series/sp500_pe.json` gained
  `presentation.publish: false`; `scripts/build_site.py` now derives every page, nav
  entry, curated block and copied data file from the published set, so the flag removes
  the chart page, its Markets entry and `site/data/sp500_pe.json` from the deploy.
  `scripts/dev.sh` passes `--include-unpublished`, so the chart still works locally.
  Verified live: `/charts/sp500_pe/` and `/data/sp500_pe.json` return 404, the other
  three charts are unchanged.
- **Open**: where the P/E chart lives long-term (a password-protected or private host)
  is deliberately undecided — see the Session Plan's open items. Old copies remain in
  `gh-pages` history and in `main`'s `data/`.
- **Landed in**: catalog/sources/spglobal.json (source notes, sp500-index, sp-500-eps) ·
  series/sp500_pe.json · scripts/build_site.py · scripts/dev.sh

## 2026-09-15 — S&P Dow Jones Indices terms and index page, read in a browser (S9)
topics: equity-valuation, equity-returns, real-estate
- **Question**: what S&P DJI's own terms say about reproducing index data, and whether its S&P 500 page still links an earnings workbook. Both pages returned 403 to automated fetches in S8 and again in S9.
- **Searched / read**: in Claude in Chrome: https://www.spglobal.com/spdji/en/terms-of-use/ (the URL catalogued in S8); the footer's Legal Disclaimer page https://www.spglobal.com/spdji/en/disclaimers/; the footer's Terms of Use link https://www.spglobal.com/en/terms-of-use; https://www.spglobal.com/spdji/en/indices/equity/sp-500/ with Additional Info expanded.
- **Found**:
  - The S8 terms URL is a 404 page in a browser. The 403 was hiding a dead link.
  - The Legal Disclaimer's General Disclaimer: "Redistribution or reproduction in whole or in part are prohibited without written permission of S&P Dow Jones Indices LLC." A later sentence names "index data" among the content that may not be "reproduced or distributed in any form or by any means, or stored in a database or retrieval system, without the prior written permission of S&P Dow Jones Indices."
  - S&P Global's corporate Terms of Use (text in a collapsed accordion) restricts copying of credit ratings; it is not the operative text for index data.
  - The S&P 500 page's Additional Info lists four documents (SPIVA After-Tax Scorecard, "The Gauge of the U.S. Large-Cap Market", GICS Scorecard, Stock Buybacks) and no earnings workbook.
- **Outcome**: adopted. `spglobal` source-level terms moved from `unverified` to `restricted`. The P/E price-column question is still open: the disclaimer confirms written permission is needed, so the answer to the email to index_services@spdji.com decides it.
- **Landed in**: catalog/sources/spglobal.json (terms, access notes)

*The S9 entries below were written by the S9 research agents (one per source, 2026-09-15) and appended by the session owner unedited. A per-file verifier then spot-checked each catalogue file and a fix step corrected some facts afterwards, so where an entry and its catalogue file disagree, the file is the later word.*

## 2026-09-15 — Treasury daily par yield curve CSV recipe and start date
topics: rates
- **Question**: Does the daily-treasury-rates.csv/<year>/all?type=daily_treasury_yield_curve recipe work, and when does the nominal series actually start (task said 1990)?
- **Searched / read**: curl'd https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/1990/all?type=daily_treasury_yield_curve (data, last row 12/31/1990, 9 tenors) and the same for /1989/... (empty body, header row only); also /2026/... (14 tenors, latest 09/14/2026).
- **Found**: 1990 is the first year with data; 1989 returns nothing. Tenor count grew from 9 (1990: 3mo,6mo,1yr,2yr,3yr,5yr,7yr,10yr,30yr) to 14 (2026: adds 1mo,1.5mo,2mo,4mo,20yr) but the exact year each tenor was added wasn't mapped beyond the two endpoints checked.
- **Outcome**: adopted
- **Landed in**: catalog/sources/treasury-gov.json (dataset yield-curve)

## 2026-09-15 — Treasury real yield curve start date
topics: rates, inflation
- **Question**: When does the Real CMT (TIPS-derived) series actually start (task said 2003)?
- **Searched / read**: curl'd .../daily-treasury-rates.csv/2003/all?type=daily_treasury_real_yield_curve (data, last row 12/31/2003, 3 tenors: 5yr/7yr/10yr) and /2002/... (empty body).
- **Found**: 2003 is the first year with data; 2002 returns nothing. 2026's file has 5 tenors (adds 20yr, 30yr) vs 2003's 3 — addition year not checked.
- **Outcome**: adopted
- **Landed in**: catalog/sources/treasury-gov.json (dataset real-yield-curve)

## 2026-09-15 — Current-year CSV caching quirk
topics: rates
- **Question**: Does home.treasury.gov cache the current-year CSV file, as reported anecdotally, and can it be verified rather than just recorded as hearsay?
- **Searched / read**: curl -D- on the 2026 nominal CSV with a plain query string vs the same URL plus a cache-busting junk parameter; compared X-Drupal-Cache and X-Age response headers, then diffed the actual CSV bodies.
- **Found**: Plain request → X-Drupal-Cache: HIT. Same URL + junk param → X-Drupal-Cache: MISS. Bodies were identical in this check (today's newest row was already present in the cached copy), so the header comparison confirms the caching layer exists but doesn't demonstrate it ever serves stale current-day data.
- **Outcome**: adopted (recorded as verified-mechanism, not verified-staleness)
- **Landed in**: catalog/sources/treasury-gov.json (access.notes)

## 2026-09-15 — Treasury site copyright/terms statement
topics: rates
- **Question**: Does Treasury's site have a quotable copyright/public-domain/reuse statement, at the URL pattern given (policies-and-guidance/other-policies/website-policies-and-major-links) or elsewhere?
- **Searched / read**: WebFetch on the given URL (404); web search for "home.treasury.gov website policies copyright public domain" surfaced https://home.treasury.gov/subfooter/site-policies-and-notices as the real page; fetched it directly (curl) and grepped the extracted text for "copyright" — no match; scanned its outbound links for a dedicated copyright/legal page — none found.
- **Found**: The given URL doesn't exist; the actual site-policies page is a link list (Privacy Policy, Accessibility, FOIA, etc.) with no copyright sentence in the reachable HTML.
- **Outcome**: gap
- **Landed in**: catalog/sources/treasury-gov.json (terms — left as unverified, url set to the working page, no quote)

## 2026-09-15 — HQM corporate bond yield curve: Treasury's own page vs FRED
topics: credit, rates
- **Question**: Does Treasury publish the HQM corporate bond yield curve directly, and how does it relate to fred.json's existing hqmcb dataset?
- **Searched / read**: https://home.treasury.gov/data/treasury-coupon-issues-and-corporate-bond-yield-curve/corporate-bond-yield-curve (curl, since WebFetch's JS-rendered summary lacked file links); grepped for hqm*.xls hrefs and their link-title context; cross-checked catalog/sources/fred.json's existing hqmcb entry (read-only, not edited).
- **Found**: Treasury serves HQM data as chunked 5-year .xls spot-rate workbooks (hqm_84_88.xls ... hqm_24_28.xls, plus end-of-month hqmeom_* equivalents) and one consolidated par-yields workbook (hqm_qh_pars.xls / hqmeom_qh_pars.xls) spanning 1984-present. fred.json already catalogues the same underlying data (HQMCB1YR-HQMCB30YR, monthly, from 1984-01) as dataset hqmcb, via the FRED API, which is what series_meta.py actually resolves today.
- **Outcome**: adopted
- **Landed in**: catalog/sources/treasury-gov.json (dataset hqm-corporate-par-yields, cross-referenced to catalog/sources/fred.json dataset hqmcb)

## 2026-09-15 — Damodaran implied ERP and historical-returns datasets
topics: equity-valuation, equity-returns
- **Question**: Does NYU Stern's Damodaran data page publish an annual implied equity risk premium history (from 1960) and annual stock/bond/bill/real-estate/gold returns (from 1928), and under what terms?
- **Searched / read**: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html (dataset index); https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histimpl.html and .../datafile/histretSP.html (dataset detail pages); HEAD/GET on https://pages.stern.nyu.edu/~adamodar/pc/datasets/histimpl.xls and .../histretSP.xls for Last-Modified/size.
- **Found**: histimpl.xls = implied ERP, US, annual, 1960–2025 (last-modified 2026-01-08). histretSP.xls = annual returns 1928–2025 for S&P 500, US small-cap, 3-mo T-bill, 10-yr T-bond, Baa corporate, real estate, and gold, plus $100-invested cumulative columns (last-modified 2026-08-24, later than the page's stated 2026-01-05 January refresh — an off-cycle revision, cause not established).
- **Outcome**: adopted
- **Landed in**: catalog/sources/damodaran.json (dataset implied-erp-history) · catalog/sources/damodaran.json (dataset historical-returns)

## 2026-09-15 — Damodaran usage/terms statement
topics: equity-valuation
- **Question**: Does Damodaran's site state any terms of use, copyright, citation requirement, or redistribution restriction on the downloadable data?
- **Searched / read**: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datahistory.html (the page's own '#rules' Usage Rules section and '#timing' Data Timing section); https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html; https://pages.stern.nyu.edu/~adamodar/ (homepage frameset — no terms link found here).
- **Found**: Verbatim: "I am not good at making rules and thus have very few related to the use of my data. I want the data to be widely used and to be a help, rather than a hindrance. Acknowledgements: If you do use my data and wish to acknowledge that you did get the data off my site, I thank you. If not, I will not lose any sleep and you should not either." Update timing, also verbatim: "I update most of the data only once a year, in the first two weeks of January. There are a few data items, like equity risk premiums, that I update more frequently..."
- **Outcome**: adopted
- **Landed in**: catalog/sources/damodaran.json (terms block, access.notes)

## 2026-09-15 — Damodaran industry P/E and credit-spread (ratings) workbooks
topics: equity-valuation, credit
- **Question**: Are current industry multiples (P/E by sector) and credit spreads (bond rating / default spread table) clearly downloadable, and at what cadence/coverage?
- **Searched / read**: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/pedata.html; https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html (both linked from datacurrent.html's 'Multiples' and 'Discount Rate Estimation' sections respectively).
- **Found**: pedata.xls — current trailing/forward P/E, PEG by ~100+ US industry sectors across ~6,000 firms, footer dated 'Last Updated in January 2026'; a cross-sectional snapshot, not a time series (global/regional variants exist as separate files, not researched). ratings.xls — interest-coverage-ratio bands mapped to a synthetic Moody's/S&P rating and default spread over the risk-free rate, for large non-financial vs. financial firms, 'as of January 2026'; also a snapshot.
- **Outcome**: adopted (with coverage recorded as unknown — these are overwritten snapshots, not append-only histories, so no historical start date could be established without guessing)
- **Landed in**: catalog/sources/damodaran.json (dataset industry-pe) · catalog/sources/damodaran.json (dataset credit-spreads)

## 2026-09-15 — Does Damodaran publish S&P 500 earnings (EPS) that could replace S&P Global's discontinued workbook?
topics: equity-valuation
- **Question**: The S&P Global public EPS workbook (quarterly as-reported EPS) was discontinued 31 Jan 2026. Does Damodaran's data page publish any annual or quarterly S&P 500 earnings/EPS series (as-reported or operating) that could substitute?
- **Searched / read**: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html — grepped the full dataset index (all ~90 linked workbooks: betas, capex, dividends, debt, margins, R&D, WACC, multiples, ratings, returns, implied ERP, etc.) for 'S&P 500' / 'earnings' / 'EPS' mentions; also read datahistory.html for any general mention of an earnings series.
- **Found**: The only 'S&P' mentions on the index page are inside the S&P bond-ratings dataset description (unrelated to equity EPS) and the two datasets already catalogued (histretSP.xls's S&P 500 *return* column, and histimpl.xls's S&P 500 *index level/earnings-yield inputs* used internally for the ERP calculation — neither publishes a standalone EPS or earnings-level series usable as an earnings input elsewhere). No dedicated S&P 500 earnings/EPS workbook, at any cadence or measure (as-reported or operating), appears anywhere on the current data page.
- **Outcome**: gap — Damodaran's site does not have a substitute for the discontinued S&P Global EPS workbook; the CLAUDE.md 'Known gap' item (replacement source for the discontinued EPS workbook) remains open and needs a different source.
- **Landed in**: catalog/sources/damodaran.json (top-level notes)

## 2026-09-15 — Kenneth French Data Library: core factor files and coverage
topics: equity-returns
- **Question**: What are the file names (ids), coverage start dates, and update cadence for the Fama/French 3-factor (monthly, daily), Fama/French 5-factor (2x3), and momentum factor datasets?
- **Searched / read**: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html (main library page, via WebFetch then curl for exact zip filenames and raw HTML); https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html (FF3 description); https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html (FF5 2x3 description); https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html (momentum description).
- **Found**: FF3 monthly zip `F-F_Research_Data_Factors_CSV.zip`, coverage "July 1926 - July 2026" (as read 2026-09-15); FF3 daily zip `F-F_Research_Data_Factors_daily_CSV.zip`, coverage "July 1, 1926 - July 31, 2026"; FF5 2x3 monthly zip `F-F_Research_Data_5_Factors_2x3_CSV.zip`, coverage "July 1963 - July 2026"; momentum monthly zip `F-F_Momentum_Factor_CSV.zip`, coverage "January 1927 - July 2026". Update-cadence statement on the library page: "We reconstruct the full history of returns each month when we update the portfolios." No numeric lag (business days) stated anywhere.
- **Outcome**: adopted
- **Landed in**: catalog/sources/kenneth-french.json (datasets ff3-factors-monthly, ff3-factors-daily, ff5-factors-2x3-monthly, momentum-factor-monthly)

## 2026-09-15 — Kenneth French Data Library: terms/usage statement
topics: equity-returns
- **Question**: Does the Ken French Data Library state any terms of use, license, or redistribution permission?
- **Searched / read**: Full text of https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html (raw HTML via curl, searched for "copyright", "terms", "license", "permission", "use").
- **Found**: Only a footer copyright notice, dynamically year-stamped by inline JavaScript: `Copyright <script>...document.write(year)...</script> Eugene F. Fama and Kenneth R. French` — verbatim as rendered on 2026-09-15: "Copyright 2026 Eugene F. Fama and Kenneth R. French". No separate terms-of-use page, no explicit statement permitting or prohibiting republication/redistribution of the data or derived charts was found on this page or linked from it.
- **Outcome**: gap (no clean status fit — see report's terms_status note; classified restricted as the conservative reading, flagged open)
- **Landed in**: catalog/sources/kenneth-french.json (terms block)

## 2026-09-15 — Fama/French 5 Factors (2x3): daily coverage is stale, commented-out HTML
topics: equity-returns
- **Question**: What is the coverage start/end for the FF5 2x3 daily and weekly return files, to catalogue alongside the monthly file?
- **Searched / read**: Raw HTML of https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html via curl, checked for HTML comment markers around each Returns row.
- **Found**: The Daily Returns and Weekly Returns table rows (reading "July 1, 1963-May 31, 2014" and "July 2, 1963-May 31, 2014") are wrapped inside an HTML comment (`<!-- ... -->`) and do not render on the live page — only Monthly ("July 1963 - July 2026") and Annual ("1964 - 2025") rows are live. The zip files for FF5 2x3 daily/weekly (`F-F_Research_Data_5_Factors_2x3_daily_CSV.zip`, etc.) are still linked and downloadable from the main library page despite the description page's stale/hidden text.
- **Outcome**: gap (daily coverage recorded as unknown rather than using the stale commented dates; daily/weekly not catalogued as separate dataset entries per task scope, which asked for FF5 2x3 as one line)
- **Landed in**: catalog/sources/kenneth-french.json (dataset ff5-factors-2x3-monthly, notes field)

## 2026-09-15 — Z.1 release cadence, format and DDP status
topics: equity-returns, macro
- **Question**: What is the Z.1 Financial Accounts release schedule, and how is the data downloaded (formats, tools)?
- **Searched / read**: https://www.federalreserve.gov/releases/z1/ ; https://www.federalreserve.gov/datadownload/Build.aspx?rel=z1 (via WebSearch); WebFetch on the Z.1 release page
- **Found**: Quarterly release, roughly ten weeks after quarter-end (Q2 2026 released 2026-09-11; next release Thursday 2026-12-10 for Q3 2026). File structure per release: a Z.1 PDF, per-table HTML pages, and a compressed CSV package with data dictionaries, downloadable via the Data Download Program (DDP). The Board's own page states the DDP's 'Build Your Package' feature was scheduled for removal during the week of 2026-11-09 in preparation for the DDP's eventual retirement, pointing users to FRED for expanded download options instead.
- **Outcome**: adopted
- **Landed in**: catalog/sources/federal-reserve-board.json (access block, notes)

## 2026-09-15 — Board website copyright/terms statement
topics: equity-returns, macro
- **Question**: What does the Board of Governors' own site (federalreserve.gov, distinct from the Reserve Banks' sites) say about reuse of its published information?
- **Searched / read**: WebSearch 'federalreserve.gov website policies copyright terms of use reproduction' surfaced federalreserve.gov/disclaimer.htm; fetched and curl'd that page directly for the verbatim sentence
- **Found**: "Unless otherwise indicated, information on Board's website is in the public domain and may be copied and distributed without permission." with a request to cite the Board as source; a separate carve-out for any photo/graphic/material explicitly marked as copyrighted or associated with a non-Board party. Distinct from several Reserve Bank sites (SF Fed, NY Fed, FRBservices) which have their own, differently worded terms — not relevant here since this file is the Board, not a Reserve Bank.
- **Outcome**: adopted
- **Landed in**: catalog/sources/federal-reserve-board.json (terms block, status verified)

## 2026-09-15 — Which Z.1 tables cover household equity allocation and corporate leverage
topics: equity-returns, macro, credit
- **Question**: Which Z.1 table numbers hold household equity holdings, aggregate corporate-equities market value, and nonfinancial-corporate leverage inputs (debt vs equity)?
- **Searched / read**: WebSearch for B.101/table numbers; fetched https://www.federalreserve.gov/releases/z1/20260109/html/b101.htm ; WebSearch for L.223/corporate-equities table (found it renumbered to L.224/F.224, confirmed via https://www.federalreserve.gov/releases/z1/20201210/html/l223.htm search snippet describing the renumbering); WebSearch for B.103 nonfinancial corporate business leverage (https://www.federalreserve.gov/releases/Z1/20250612/html/b103.htm)
- **Found**: B.101 line 23 = corporate equities (households/nonprofits, direct holdings, market value), line 25 = mutual fund shares — the household equity-allocation inputs. L.223 (corporate equities market value across all sectors) was renumbered to L.224/F.224 in a recent release; mutual fund shares are the separate L.225/F.225. B.103 gives nonfinancial corporate business debt (securities line 31 + loans line 35) and total equity (line 43, market value) — the standard leverage-ratio inputs.
- **Outcome**: adopted
- **Landed in**: catalog/sources/federal-reserve-board.json (datasets b101-household-balance-sheet, l224-corporate-equities, b103-nonfinancial-corporate-leverage)

## 2026-09-15 — FRED mirror series ids and coverage start for the Buffett-indicator/leverage roadmap items
topics: equity-returns, macro
- **Question**: What are the confirmed FRED series ids mirroring the relevant Z.1 lines, and what is the earliest observation date (a proxy for the Financial Accounts' overall coverage start)?
- **Searched / read**: FRED API (https://api.stlouisfed.org/fred/series) for HNOCEAQ027S, TNWBSHNO, NCBEILQ027S, NCBDBIQ027S, NCBCEBQ027S, BOGZ1FL192090005Q
- **Found**: HNOCEAQ027S (Households/Nonprofits; Corporate Equities; Asset, Level), TNWBSHNO (Households/Nonprofits; Net Worth, Level) and NCBDBIQ027S (Nonfinancial Corporate Business; Debt Securities; Liability, Level) all start 1945-10-01. NCBEILQ027S (Nonfinancial Corporate Business; Corporate Equities; Liability, Level) also starts 1945-10-01. NCBCEBQ027S (a transactions, not level, series) starts a year later, 1946-10-01 — not used. BOGZ1FL192090005Q (Households; Net Worth, Level, a narrower household-only variant) only starts 1987-10-01, so TNWBSHNO (households+nonprofits) was preferred as the better coverage match for B.101.
- **Outcome**: adopted
- **Landed in**: catalog/sources/federal-reserve-board.json (dataset notes on b101-household-balance-sheet, l224-corporate-equities, b103-nonfinancial-corporate-leverage; coverage.start 1945-10 on all three datasets)

## 2026-09-15 — Numeric publication lag for Z.1 (not established)
topics: macro
- **Question**: Is there an official stated publication-lag rule (e.g. 'X business days after quarter end') for the Z.1 release, the way FRED series pages sometimes state one?
- **Searched / read**: https://www.federalreserve.gov/releases/z1/z1_technical_qa.htm (WebFetch); the Z.1 release page's own next-release-date line
- **Found**: No stated lag rule — the Board simply publishes specific calendar dates per quarter on its release-schedule page (observed pattern: Q2 2026 data released 2026-09-11, roughly 10 weeks after quarter-end; Q3 2026 due 2026-12-10). The Technical Q&A page covers methodology/revision questions, not a lag policy.
- **Outcome**: gap
- **Landed in**: catalog/sources/federal-reserve-board.json (publication_lag_business_days: "unknown" on all three datasets; explained in the file's top-level notes)

## 2026-09-15 — JST Macrohistory Database: license, release, and coverage
topics: credit, real-estate, equity-returns, macro
- **Question**: What is the JST Macrohistory Database's latest release, coverage, variables, formats, and terms of use for catalog/sources/jst-macrohistory.json?
- **Searched / read**: https://www.macrohistory.net/database/ (main database page: license, citations, downloads), https://www.macrohistory.net/data/ (release/download URL structure), https://www.macrohistory.net/ (homepage/nav, confirms DATABASE section and Kiel Institute / MacroFinance & MacroHistory Lab hosting)
- **Found**: Release R.6 (2022), 18 advanced economies, annual data from 1870-ongoing, 48 variables (real economy, credit, house prices, crisis dates, equity/housing/bond/bill returns, bank balance-sheet ratios, etc.), distributed only as one whole-database xlsx (JSTdatasetR6.xlsx) or Stata .dta (JSTdatasetR6.dta) file-download, no API. Licence: "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" with the verbatim restriction "Commercial data providers are thus strictly forbidden to integrate all or parts of the dataset into their services and/or resell the data." Citation requirement is split across three papers depending on which variables are used (2017 general, 2019 returns, 2021 bank ratios). No dated release-history page for R1-R6 was found, so inter-release cadence is unknown/irregular rather than a fixed schedule.
- **Outcome**: adopted
- **Landed in**: catalog/sources/jst-macrohistory.json (dataset jst-dataset-r6)

## 2026-09-15 — OFR Financial Stress Index: download method and coverage
topics: credit, equity-valuation, macro, global
- **Question**: What is the OFR FSI, does it have a CSV download and/or an API, what's its coverage start date and cadence, and what are its category/region sub-indexes?
- **Searched / read**: WebFetch on https://www.financialresearch.gov/financial-stress-index/ and /financial-stress-index/regions/ and /data/; grepped the raw HTML of the FSI page for csv/api/download links; found and curl'd https://www.financialresearch.gov/financial-stress-index/data/fsi.csv directly with a browser-UA.
- **Found**: The FSI page describes 5 category sub-indexes (credit, equity valuation, funding, safe assets, volatility) and 3 region sub-indexes (United States, other advanced economies, emerging markets), refreshed daily, current from two business days prior. The single fsi.csv (200 OK, text/csv, 514,753 bytes) contains all 9 series (national + 8 sub-indexes) as columns, 6,757 daily rows from 2000-01-03 through 2026-09-11. Checked for an FSI-specific API: /financial-stress-index/api/ and /financial-stress-index/download/ both returned 404 — no API for the FSI itself. The OFR's Data & Standards page (/data/) links separate APIs for the unrelated Short-Term Funding Monitor and Hedge Fund Monitor products only.
- **Outcome**: adopted
- **Landed in**: catalog/sources/ofr.json (dataset fsi)

## 2026-09-15 — OFR terms of use / data policy for the FSI
topics: credit, equity-valuation, macro, global
- **Question**: Does OFR have a terms-of-use or data-policy statement for the FSI, and specifically does the FSI's basket of 33 underlying market variables include third-party licensed data that would limit redistribution of the derived index?
- **Searched / read**: WebFetch on https://www.financialresearch.gov/about/data-policy/ (404 — no such page) and https://www.financialresearch.gov/about/policies/ (200; covers Accessibility, FOIA, Information Quality Act, No FEAR Act, Plain Writing, Website Privacy, Open Government — none address FSI data reuse); WebSearch for "financialresearch.gov terms of use data policy copyright"; re-read the FSI page's own footer text (General Disclaimer, Disclaimer Regarding Non-OFR Data and Information, Suggested Citation) via a local grep of the fetched HTML with tags stripped.
- **Found**: No dedicated terms-of-use page exists. The FSI page's "Disclaimer Regarding Non-OFR Data and Information" is explicitly about *external, non-government sites* the OFR links to ("These sites may contain information that is copyrighted with restrictions on reuse. Permission to use copyrighted materials must be obtained from the original source...") — it does not describe the FSI's own construction or its 33 input variables' individual licences, and no page itemizes those inputs' sources or terms. Only a suggested-citation sentence and a general accuracy/liability disclaimer apply to the FSI itself.
- **Outcome**: gap — terms.status recorded as "unknown" rather than guessed; whether the FSI's third-party inputs impose any redistribution limit on the derived index is unresolved and left as an open note in the dataset entry.
- **Landed in**: catalog/sources/ofr.json (dataset fsi)

## 2026-09-15 — Philadelphia Fed SPF: variable history, files, and timing
topics: inflation, expectations
- **Question**: For the Survey of Professional Forecasters, what are the exact coverage start dates and download files for CPI, CORECPI and CPI10, and how does the survey's quarterly release timing work?
- **Searched / read**: https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters (overview, history: 1968:Q4 start under ASA/NBER, Philly Fed took over 1990:Q2); https://www.philadelphiafed.org/surveys-and-data/data-files (file index); https://www.philadelphiafed.org/surveys-and-data/cpi-spf, /corecpi, /cpi10 (raw HTML via curl, extracted the Individual/Mean/Median/Dispersion xlsx download links); full spf-documentation.pdf (Last Update: July 28, 2026) — Overview (p.2-3: variable-addition history), Table 1A (p.8: quarterly timing 1990:Q3-present — questionnaires sent end of month N, deadline mid-month N+1, release middle-to-late month N+1), Table 2 (p.10-16: per-variable 'First survey to include this variable' — CPI 1981:Q3, CORECPI 2007:Q1, CPI10 1991:Q4, with CPI10 explicitly not restricted to first-quarter surveys unlike RGDP10/STOCK10/BOND10/etc.), Section 5 (p.35: Inflation.xlsx and the INFCPI10YR/INFCPI1YR/INFPGDP1YR derived series).
- **Found**: All three variables have documented first-survey quarters but the documentation itself says pre-1990:Q2 survey timing (which would place an exact day/month on CPI's 1981:Q3 start) is uncertain ("we do not know with certainty the timing of surveys conducted by the ASA/NBER... our reference dates do not cover surveys prior to that of 1990:Q2") — so CPI's coverage.start was recorded at year granularity, while CORECPI and CPI10 (both post-1990) got month-level estimates from Table 1A's release pattern.
- **Outcome**: adopted
- **Landed in**: catalog/sources/philadelphia-fed.json (datasets cpi, corecpi, cpi10)

## 2026-09-15 — Philadelphia Fed site-wide terms of use
topics: inflation, expectations
- **Question**: Does philadelphiafed.org have a terms-of-use or copyright statement covering the SPF data files, and what does it say?
- **Searched / read**: web search for "Philadelphia Fed website terms of use copyright"; found and read https://www.philadelphiafed.org/about-us/privacy-notice via curl (raw HTML, grepped for 'copyright'). No separate /terms-of-use, /legal or /copyright page exists on philadelphiafed.org — the privacy notice page is the site's terms statement.
- **Found**: Verbatim: "Some of the content on this website may be copyrighted. Permission to use such copyrighted material must be obtained from the owner." Also: prohibition on using the Federal Reserve's name for advertising/endorsement/commercial purposes, and a page footer "Copyright 2026. All rights reserved. Federal Reserve Bank of Philadelphia."
- **Outcome**: adopted
- **Landed in**: catalog/sources/philadelphia-fed.json (terms.status: restricted)

## 2026-09-15 — Livingston Survey considered, not added
topics: inflation, expectations
- **Question**: Is the Philadelphia Fed's Livingston Survey clearly relevant enough to inflation expectations to add as a second dataset in this file, per the task's optional instruction?
- **Searched / read**: web search "Philadelphia Fed Livingston Survey inflation expectations semiannual since 1946" — surfaced https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/livingston-survey and /livingston-historical-data, not fetched directly (only search-result summaries read, which are discovery, not citation, per the task's fetching rule).
- **Found**: Confirmed via search summary only: started 1946 by columnist Joseph Livingston, semiannual (June/December), Philadelphia Fed took over administration in 1990, covers economists' forecasts including inflation. No official page was actually read for terms, exact variable list, or file structure.
- **Outcome**: gap — a future S9 agent (or this session's owner) can add it as a fourth dataset in this file, or its own file if its terms differ, but only after reading its actual documentation/terms pages; not added here to avoid an unresearched entry.
- **Landed in**: catalog/sources/philadelphia-fed.json (top-level notes, flagging the gap)

## 2026-09-15 — FDIC National Rates and Rate Caps: coverage, cadence, methodology
topics: rates, macro
- **Question**: Where do current and historical National Rates and Rate Caps live, what format, what cadence, what coverage start, which products/CD terms, and what's the methodology (deposit-weighted retail average vs brokered CD offers)?
- **Searched / read**: WebSearch "FDIC National Rates and Rate Caps data download methodology"; WebFetch https://www.fdic.gov/national-rates-and-rate-caps (current month page); WebFetch https://www.fdic.gov/national-rates-and-rate-caps/national-rates-and-rate-caps-previous-rates; curl -A ... of the current-month page for exact HTML text (grep confirmed no .csv/.xlsx link on that page).
- **Found**: "The FDIC began posting the National Rate and Rate Cap on May 18, 2009." Products: Savings, Interest Checking, Money Market, and CDs at 1/3/6/12/24/36/48/60-month on-tenor terms. Cadence: "published every 3rd Monday of each month" (next business day if that Monday is a Federal holiday) — confirmed monthly, not verified as having a fixed lag in business days relative to month-end. Methodology, verbatim: "the average of rates paid by all insured depository institutions and credit unions for which data is available, with rates weighted by each institution's share of domestic deposits" — a deposit-weighted average of rates actually paid (retail), source data "S&P Capital IQ Pro; SNL Financial Data," calculations by FDIC; "Savings and interest checking account rates are based on the $2,500 product tier, while money market and certificate of deposit rates represent an average of the $10,000 and $100,000 product tiers." A rule change effective 2021-04-01 redefined the national rate/cap; the Previous Rates page splits historical Excel downloads into "Historical Rates Prior Rule" (from 2009-05-18) and "Historical Rates Revised Rule" (from 2021-04-01) — two different definitions, not directly comparable across the break. No CSV/XLSX link on the current-month page itself; history is manual-download Excel only. No explicit FDIC statement using the word "brokered" — I described the retail/paid-rate distinction from their own definition rather than attribute a brokered-CD contrast to them.
- **Outcome**: adopted
- **Landed in**: catalog/sources/fdic.json (dataset national-rates-and-caps)

## 2026-09-15 — FDIC website terms/copyright statement for own data
topics: rates
- **Question**: Does fdic.gov state a copyright/public-domain/reuse position for its own website content and data (as opposed to linked third-party content)?
- **Searched / read**: WebSearch "fdic.gov website policies copyright terms of use"; WebFetch https://www.fdic.gov/about/website-policies; curl -A ... of that page, grepped for "copyright", "Copyright", "public domain", "Public Domain", "reuse", "republi".
- **Found**: The only copyright-adjacent sentence on the policies page is: "External sites may contain information that is copyrighted with restrictions on reuse. Permission to use copyrighted materials must be obtained from the original source and cannot be obtained from the FDIC." This is scoped to linked (third-party) sites, not FDIC's own data or the National Rates and Rate Caps table. No "public domain" or "U.S. government work" statement found anywhere on the page.
- **Outcome**: gap
- **Landed in**: catalog/sources/fdic.json (terms.status: unknown, url set to the website-policies page that was actually read)

## 2026-09-15 — FRED-hosted mirrors of FDIC national rates/caps
topics: rates
- **Question**: Does FRED host the FDIC's National Rates and Rate Caps series, and under what ids and coverage?
- **Searched / read**: curl https://api.stlouisfed.org/fred/series/search?search_text=National+Rate (FRED API), then targeted curl https://api.stlouisfed.org/fred/series?series_id=<ID> for SNDR, SNRC, ICNDR, ICNRC, MMNDR, MMNRC, and NDR{1,3,6,12,24,36,48,60}MCD / NRC{1,3,6,12,24,36,48,60}MCD.
- **Found**: All 18 series exist on FRED under a <PRODUCT>NDR (rate) / <PRODUCT>NRC (cap) naming convention, monthly, except NRC36MCD (36-month CD rate cap) — that one returned "Bad Request. The series does not exist." while NDR36MCD (the rate) and every other on-tenor cap (NRC1MCD...NRC60MCD except 36) do exist. Every FRED series' observation_start is 2021-04-01 — the Revised Rule period only; none carry the 2009-2021 Prior Rule history. FRED's own series notes quote the same national-rate/national-rate-cap definition text as the FDIC page.
- **Outcome**: adopted (ids recorded as a `gives` note; fred.json itself not edited per the task's instruction not to touch it)
- **Landed in**: catalog/sources/fdic.json (dataset national-rates-and-caps, gives field)

## 2026-09-15 — ICE BofA (BAML*) FRED history window and copyright status
topics: credit, rates
- **Question**: What is FRED's current coverage window, cadence and copyright status for the ICE BofA option-adjusted-spread and effective-yield series (BAMLC0A0CM, BAMLH0A0HYM2, BAMLC0A1CAAAEY, BAMLC0A2CAAEY, BAMLC0A3CAEY, BAMLC0A4CBBBEY, BAMLH0A1HYBBEY, BAMLH0A2HYBEY), and does FRED still carry the full history back to the mid/late 1990s the earlier planning notes assumed?
- **Searched / read**: FRED API `/fred/series?series_id=<ID>&api_key=$FRED_API_KEY&file_type=json` for all 8 series ids; FRED series pages https://fred.stlouisfed.org/series/BAMLC0A0CM and https://fred.stlouisfed.org/series/BAMLH0A0HYM2 (via WebFetch) for the copyright tag.
- **Found**: All 8 series report `observation_start: 2023-09-18`, `observation_end: 2026-09-14`, daily close frequency. Every series' notes field includes the identical sentence: "Starting in April 2026, this series will only include 3 years of observations. For more data, go to the source." Both series pages checked show the tag "Copyrighted: Pre-Approval Required" and the notes carry ICE's full copyright/reproduction-prohibited/internal-use-only language, ending with "Certain indices and index data included in FRED are the property of ICE Data Indices, LLC (\"ICE DATA\") and used under license... BOFA... LICENSED BY BANK OF AMERICA CORPORATION."
- **Outcome**: adopted — recorded the 3-year trailing window as a prominent caveat (both in `access.notes` and a top-level `notes` entry) since it contradicts the planning assumption of 25+ years of history; recorded `terms.status: restricted` with the quoted copyright sentence.
- **Landed in**: catalog/sources/ice-bofa.json (datasets `oas`, `effective-yields-by-rating`)

## 2026-09-15 — ICE Data Indices' own terms and conditions page
topics: credit
- **Question**: Does ICE Data Indices publish its own public terms-of-use statement for index data (independent of FRED), and does it say anything more permissive or more specific than the FRED-hosted copyright notice?
- **Searched / read**: WebFetch on https://www.theice.com/market-data/indices/terms-and-conditions (redirected to https://www.ice.com/market-data/indices/terms-and-conditions, 404); web search "ICE Data Indices terms and conditions index data republication" turned up https://www.ice.com/publicdocs/IDI_-_Terms_and_Conditions_for_the_Index_Data_and_Custom_Index_Services.pdf (fetched via curl, read pages 1-2 with the PDF reader).
- **Found**: No public terms-and-conditions *page* exists at the expected URL (404). The PDF found instead is a direct-subscriber licence agreement ("Terms and Conditions for the Index Data and Custom Index Services", v.9 010126): a paid, non-exclusive, non-transferable licence granted to a named Subscriber under a signed Schedule, restricted to internal use, with no free/public access path described anywhere in it.
- **Outcome**: rejected as the terms.status basis (it governs a different access path — direct paid subscription, not the free FRED-hosted route this repo actually uses) but kept as background context in `verified.by`, since it independently confirms ICE licenses this data restrictively rather than releasing it.
- **Landed in**: catalog/sources/ice-bofa.json (verified.by note; no dataset field)

## 2026-09-15 — University of Michigan Surveys of Consumers: FRED metadata and quirks
topics: expectations, inflation, macro
- **Question**: What do FRED's own series records say about MICH (median 1-yr expected inflation) and UMCSENT (Index of Consumer Sentiment) — cadence, coverage, copyright label, and any withheld/delayed-data quirk?
- **Searched / read**: https://api.stlouisfed.org/fred/series?series_id=MICH and ...UMCSENT (FRED API, observation_start/frequency/notes); https://fred.stlouisfed.org/series/MICH and .../UMCSENT (copyright tag, via WebFetch, checked twice independently)
- **Found**: MICH: monthly, observation_start 1978-01-01, notes state "The most recent value is not shown due to an agreement with the source." UMCSENT: monthly, observation_start 1952-11-01, notes state "At the request of the source, the data is delayed by 1 month. To obtain historical data prior to January 1978, please see FRED data series UMCSENT1." Both series pages carry the copyright tag "Copyrighted: Citation Required" (not "Pre-Approval Required").
- **Outcome**: adopted
- **Landed in**: catalog/sources/umich-surveys.json (dataset mich-inflation-expectations) · catalog/sources/umich-surveys.json (dataset umcsent-consumer-sentiment)

## 2026-09-15 — CLAUDE.md's 'MICH is Pre-Approval Required' claim does not match the live FRED page
topics: expectations, inflation
- **Question**: This repo's CLAUDE.md (Licence Notes, 2026-09-14) lists 'University of Michigan MICH' among FRED's third-party "Pre-approval required" series needing the owner's permission beyond personal use, grouped with ICE BofA BAML* and S&P DJI. Is that accurate for MICH (and by extension UMCSENT, the sibling series)?
- **Searched / read**: https://fred.stlouisfed.org/series/MICH and https://fred.stlouisfed.org/series/UMCSENT, both fetched twice with a prompt specifically asking to enumerate every tag and flag any "Pre-Approval Required" label
- **Found**: Both pages' tag lists show "Copyrighted: Citation Required", with no "Pre-Approval Required" tag present on either page.
- **Outcome**: rejected (the CLAUDE.md characterization does not hold for MICH/UMCSENT as currently published on FRED) — flagged for the session owner rather than silently corrected
- **Landed in**: catalog/sources/umich-surveys.json (top-level notes)

## 2026-09-15 — University of Michigan Surveys of Consumers: direct-site access and terms
topics: expectations, inflation, macro
- **Question**: Does sca.isr.umich.edu / data.sca.isr.umich.edu serve the sentiment and inflation-expectations tables directly, and under what terms?
- **Searched / read**: https://sca.isr.umich.edu/ (WebFetch, redirected via http:// after https:// failed), http://data.sca.isr.umich.edu/, http://data.sca.isr.umich.edu/agreement.php
- **Found**: The public site and its data portal show current index values, charts (image/PDF/Excel export) and historical tables with no login required for headline series (a Log In link exists for sponsors seeking extended data). Footer copyright: "Copyright © 2026, The Regents of the University of Michigan. All Rights Reserved." The data portal's usage agreement (agreement.php) permits displaying/reformatting/printing for one's own organization's use but states: "You agree not to reproduce, retransmit, distribute, sell, publish, or broadcast the data and materials from the Surveys of Consumers website without the express written consent of the University of Michigan."
- **Outcome**: adopted
- **Landed in**: catalog/sources/umich-surveys.json (source-level access, source-level terms)

## 2026-09-15 — sca.isr.umich.edu not reachable via curl from this session's network sandbox
topics: expectations
- **Question**: Can the direct Michigan survey site be fetched with curl (per the task's fallback instruction) if WebFetch is insufficient?
- **Searched / read**: `curl -sL -A "Mozilla/5.0 ..." https://fred.stlouisfed.org/series/MICH` and the same for data.sca.isr.umich.edu, from both /tmp and the session scratchpad
- **Found**: Every curl attempt returned exit code 1 / HTTP 000 (DNS/connect failure) — outbound curl appears blocked in this session's sandbox regardless of target host. WebFetch worked for all needed pages, so this did not block the file.
- **Outcome**: gap (curl fallback unavailable in this sandbox; noted in case a future agent hits the same wall and wonders why)
- **Landed in**: (no file — process note only)

## 2026-09-15 — NBER Macrohistory Database: interest-rate and price series
topics: rates, inflation, macro
- **Question**: Does the NBER Macrohistory Database (data.nber.org) cover pre-WWII U.S. interest rates (commercial paper / call money rates) and prices, and specifically a pre-1934 short-term rate for chart 5?
- **Searched / read**: https://www.nber.org/research/data/nber-macrohistory-database (overview, 16 chapters, .db/.dat format description, contact info); https://www.nber.org/research/data/nber-macrohistory-xiii-interest-rates (full series list: call money, commercial paper, Fed and foreign discount rates, bond/equity/mortgage yields, rate spreads — ~60 series); https://www.nber.org/research/data/nber-macrohistory-iv-prices (wholesale/retail commodity prices, BLS wholesale price index, CPI all items); HEAD request to https://data.nber.org/databases/macrohistory/data/13/m13001a.db (200, 9,482 bytes, Last-Modified 2005-08-26); directory listing at https://data.nber.org/databases/macrohistory/data/ (16 numbered chapter folders).
- **Found**: Call Money Rates (m13001a) runs 1857-01 through 1934-04 — a genuine pre-1934 short rate. Commercial Paper Rates NYC (m13002) runs 1857-01 through 1971-12. Series id convention is cadence-prefix (m/q/a) + 2-digit chapter + 3-digit series number, with letter suffixes for vintage variants. Files offered as Micro-TSP .db and rectangular .dat, unchanged since at least 2005 per Last-Modified headers. No discontinuation notice found anywhere, but also no evidence of any update since 2005.
- **Outcome**: adopted
- **Landed in**: catalog/sources/nber.json (dataset macrohistory)

## 2026-09-15 — NBER Macrohistory terms: differs from the chronology dataset's permission grant
topics: rates, macro
- **Question**: Do the macrohistory database pages carry the same "permission to copy is granted, provided attribution of source is given" statement the chronology dataset (already catalogued, terms.status verified) has?
- **Searched / read**: full text scan of https://www.nber.org/research/data/nber-macrohistory-database and https://www.nber.org/research/data/nber-macrohistory-xiii-interest-rates for "permission"/"copyright"; cross-checked https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions (the chronology page) to see whether its permission sentence and the "All Rights Reserved" footer are the same text or two different statements; also tried https://www.nber.org/terms-use (404).
- **Found**: The chronology page has both the site-wide footer "© 2026 National Bureau of Economic Research. All Rights Reserved." AND a separate, specific sentence near the contact block: "Permission to copy is granted, provided attribution of source is given." The macrohistory database pages and the Chapter XIII page have only the site-wide footer — the specific permission sentence does not appear on them.
- **Outcome**: adopted (as a dataset-level terms override, status restricted rather than inheriting/matching the chronology dataset's verified status)
- **Landed in**: catalog/sources/nber.json (dataset macrohistory)

## 2026-09-15 — ALFRED vintage/real-time access on the FRED API
topics: rates, credit
- **Question**: Does FRED offer a separate vintage/real-time data API (ALFRED), and how is it invoked?
- **Searched / read**: https://alfred.stlouisfed.org/ ; https://fred.stlouisfed.org/docs/api/fred/series_observations.html ; https://fred.stlouisfed.org/docs/api/fred/realtime_period.html ; https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
- **Found**: ALFRED ('Economic data time travel since 2006') is not a separate API — every /fred/series* endpoint accepts realtime_start/realtime_end (YYYY-MM-DD, default today, closed interval) to select the data as it was known during that period; /fred/series/vintagedates?series_id={id} lists the actual revision dates for a series (excludes releases where data didn't change), up to 10,000 per call with limit/offset pagination. Same key, same base URL as the rest of the FRED API.
- **Outcome**: adopted
- **Landed in**: catalog/sources/fred.json (access.notes, source level — no new dataset, per instruction)

## 2026-09-15 — Moody's seasoned corporate bond yields (DAAA/DBAA/AAA/BAA) via FRED
topics: credit, rates
- **Question**: Are Moody's Aaa/Baa seasoned corporate bond yields on FRED public-domain/citation-required (→ fred.json dataset) or pre-approval-required (→ own moodys.json file)?
- **Searched / read**: https://fred.stlouisfed.org/series/DAAA ; https://fred.stlouisfed.org/series/DBAA ; https://fred.stlouisfed.org/series/AAA ; https://fred.stlouisfed.org/series/BAA (usage-rights badge near the title, via WebFetch) plus the FRED API /fred/series endpoint for observation_start/frequency/notes on all four ids
- **Found**: All four pages' badge reads 'Copyrighted: Citation Required', source 'Moody's'. DAAA starts 1983-01-03, DBAA starts 1986-01-02, AAA and BAA both start 1919-01, all daily/monthly averages of 20-year+ maturity bonds. Each series' FRED API 'notes' field (separate from the badge) carries Moody's own restrictive boilerplate ('MAY NOT BE COPIED OR OTHERWISE REPRODUCED ... WITHOUT MOODY'S PRIOR WRITTEN CONSENT'), which reads more like pre-approval language than citation-required — a real tension between FRED's badge and Moody's own notice, same as the one already on file for NFCI/T10YIE.
- **Outcome**: adopted (as a fred.json dataset, keyed on the badge per the S8 NFCI/T10YIE precedent) — but flagged as open: if the rule should also weigh the restrictive free-text notes, this belongs in its own moodys.json with access.via fred instead
- **Landed in**: catalog/sources/fred.json (dataset moodys-corporate)

## 2026-09-15 — S&P Cotality Case-Shiller home price indices on FRED
topics: real-estate
- **Question**: What are the FRED series ids, native coverage, cadence and copyright status for the S&P CoreLogic Case-Shiller national/20-city/10-city home price indices, for a new catalog dataset?
- **Searched / read**: FRED API `/fred/series` for CSUSHPINSA, CSUSHPISA, SPCS20RSA, SPCS10RSA (api.stlouisfed.org); FRED series pages for the same four ids (fred.stlouisfed.org/series/<id>) via WebFetch, since direct curl to fred.stlouisfed.org returned exit 92 (HTTP/2 stream error) from this environment.
- **Found**: All four are monthly, via S&P Dow Jones Indices. CSUSHPINSA (NSA) and CSUSHPISA (SA) are both titled "S&P Cotality Case-Shiller U.S. National Home Price Index" and both start 1987-01; SPCS10RSA (10-City Composite, SA) also starts 1987-01; SPCS20RSA (20-City Composite, SA) starts 2000-01 — 13 years later than the other three. FRED's own series titles now read "S&P Cotality Case-Shiller ...", not "S&P CoreLogic Case-Shiller ..." — CoreLogic rebranded to Cotality at some point before 2026-09-15; the underlying index methodology and rights holder (S&P DJI) are unchanged. All four series pages carry FRED's "Copyrighted: Pre-Approval Required" label (confirmed via WebFetch on each), and the FRED API's `notes` field for SPCS20RSA/SPCS10RSA quote S&P DJI's standard restriction: "Reproduction of S&P Case-Shiller 20-City Home Price Index in any form is prohibited except with the prior written permission of S&P Dow Jones Indices LLC."
- **Outcome**: adopted
- **Landed in**: catalog/sources/spglobal.json (dataset case-shiller)

## 2026-09-15 — S&P DJI terms and index pages, re-check
topics: equity-valuation, real-estate
- **Question**: Has https://www.spglobal.com/spdji/en/terms-of-use/ or the S&P 500 / Case-Shiller index pages become fetchable since the S8 session (2026-09-14), so the source-level terms.status could move off unverified?
- **Searched / read**: WebFetch on https://www.spglobal.com/spdji/en/terms-of-use/; curl with a Chrome-like User-Agent against the same URL and against https://www.spglobal.com/spdji/en/documents/additional-material/sp-500-eps-est.xlsx (via `dangerouslyDisableSandbox`, since the sandboxed curl failed with a network-level error rather than reaching the server).
- **Found**: All three requests returned HTTP 403 (Akamai edge block), identical to S8's result the day before. No terms text was read.
- **Outcome**: rejected (no new information; confirms S8's finding still holds)
- **Landed in**: catalog/sources/spglobal.json (terms.status unchanged, unverified)

## 2026-09-15 — Does S&P DJI still publish the public S&P 500 EPS workbook?
topics: equity-valuation
- **Question**: The S&P 500 EPS workbook (reference_resources/sp-500-eps-est.xlsx) carries a notice saying S&P's public EPS files ended 31 January 2026. Has S&P DJI quietly resumed publishing it, or is there a replacement page/file, as of 2026-09-15?
- **Searched / read**: Web search "S&P 500 earnings and estimates report site:spglobal.com 2026" and "S&P 500 earnings estimates public file discontinued 2026 spglobal spdji"; the search results included a URL for what looks like the same file, https://www.spglobal.com/spdji/en/documents/additional-material/sp-500-eps-est.xlsx, appearing in a September-2026-dated search index. Tried a direct curl HEAD against that URL (browser user-agent, sandbox disabled) to check if it resolves.
- **Found**: The search-engine result surfacing that URL is not itself evidence the file is currently servable — a curl HEAD against it returned HTTP 403 (Akamai edge block), the same wall every other S&P DJI page returns to automated fetches. Could not confirm whether the file is live, stale-but-still-hosted, or genuinely gone; a human would need to open the URL in a browser to check.
- **Outcome**: gap
- **Landed in**: catalog/sources/spglobal.json (access.notes, sp-500-eps dataset context) — no replacement source found; the discontinuation-workbook path in CLAUDE.md's "Known gap" section is still the open item

## 2026-09-15 — multpl.com as an EPS-replacement candidate
topics: equity-valuation
- **Question**: Is multpl.com a usable free replacement for S&P Global's discontinued public EPS workbook (quarterly/monthly as-reported trailing S&P 500 EPS, reachable without a paid account, terms that permit publishing a derived P/E with attribution)?
- **Searched / read**: https://www.multpl.com/ , https://www.multpl.com/s-p-500-pe-ratio/table/by-month , https://www.multpl.com/s-p-500-earnings/table/by-month , https://www.multpl.com/s-p-500-earnings , https://www.multpl.com/about (404 — no about page); web search "multpl.com terms of use disclaimer" (no results for the actual domain)
- **Found**: Site shows S&P 500 P/E (trailing-12-month 'as reported' earnings basis), earnings (real/inflation-adjusted dollars), earnings yield, dividend and price back to 1871, updated monthly, combining Shiller's historical dataset with current S&P figures. HTML tables only — no CSV/API/export. Only legal text found anywhere on the site is a footer disclaimer: "Information is provided 'as is' and solely for informational purposes, not for trading purposes or advice, and may be delayed." No terms-of-use, licence, or republication statement exists to search for a permission quote in.
- **Outcome**: adopted (catalogued as a candidate; not adopted as the EPS-replacement fix — see report summary for why: HTML-scrape-only access, unknown terms, real-dollar rather than nominal-EPS figures, and it re-sources the same restricted/unknown-terms data already in the pipeline rather than adding an independent source)
- **Landed in**: catalog/sources/multpl.json (datasets sp-500-pe-ratio, sp-500-earnings)

## 2026-09-15 — Siblis Research and FactSet Earnings Insight as EPS-replacement candidates
topics: equity-valuation
- **Question**: Do Siblis Research's or FactSet's Earnings Insight publish a free, machine-readable, permissively-licensed trailing S&P 500 EPS series that could replace the discontinued S&P Global workbook?
- **Searched / read**: web search "Siblis Research S&P 500 earnings free download historical" (siblisresearch.com pages: sector P/E page, global valuations database page, CAPE-by-sector page); web search "FactSet Earnings Insight free weekly S&P 500 EPS report" (insight.factset.com report index and sample report URLs)
- **Found**: Siblis Research's Global Equity Valuations Database — which has the trailing-TTM as-reported earnings series wanted — is a paid subscription product with API access; free pages are point-in-time snapshot tables (e.g. current sector P/E), not a downloadable historical EPS series. FactSet's Earnings Insight is a free weekly PDF/web commentary report (growth rates, beat/miss counts, forward estimates) authored by John Butters, not a downloadable clean trailing-EPS time series, and carries no stated redistribution terms — it's FactSet's own copyrighted research.
- **Outcome**: rejected (both) — Siblis's usable data is paywalled; FactSet's free content isn't a fetchable EPS series
- **Landed in**: catalog/sources/multpl.json (notes field, as a comparison point) · this report's ranking (no file written for either — no slug created)

## 2026-09-15 — Shiller ie_data.xls: Yale frozen, shillerdata.com is the maintained copy
topics: equity-valuation, equity-returns
- **Question**: Is Yale's ie_data.xls (Last-Modified 2023-10-17 per S8's HEAD check) frozen, with shillerdata.com hosting the actively maintained copy?
- **Searched / read**: Downloaded http://www.econ.yale.edu/~shiller/data/ie_data.xls directly. Fetched https://shillerdata.com/ HTML and found its visible download link is script-rendered — the real file lives at https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/70fec4f5-727f-4e53-b5f1-179af109c5fa/ie_data.xls?ver=1788371540009 (grepped for href="...ie_data.xls..." in the page source). Downloaded that file too. Read both workbooks' Data sheet with pandas (header=7) and OLE metadata with `file`.
- **Found**: Yale copy — OLE Last Saved 2023-09-17 (matches the 2023-10-17 Last-Modified header); last row with a price (column P) is 2023.09 ($4515.77); last row with earnings (column E) is 2023.06 ($181.17). shillerdata.com copy — OLE Last Saved 2026-09-02 by "Laurence Black"; last row with a price is 2026.09 ($7631.47); last row with earnings is 2026.06 ($295.3881). Different MD5s, different byte sizes (1,628,672 vs 1,674,752). shillerdata.com's copy is unambiguously the maintained one.
- **Outcome**: adopted — catalog/sources/shiller.json's access.url now points to the shillerdata.com file URL (Yale URL kept as a note). Repointing scripts/fetch_sp500_pe.py itself was left as a recommendation, not made (out of this task's file scope) — the live P/E series has been running on 2023-09/2023-06 confirmed Shiller data for three years by mistake since it still fetches the Yale URL.
- **Landed in**: catalog/sources/shiller.json (dataset ie-data)

## 2026-09-15 — J.P. Morgan Guide to the Markets: reference entry
topics: equity-valuation, rates, macro
- **Question**: What is J.P. Morgan Asset Management's Guide to the Markets, how is it accessed, and what do its terms say about reuse?
- **Searched / read**: am.jpmorgan.com/us/en/asset-management/adv/insights/market-insights/guide-to-the-markets/ (landing page); WebSearch "J.P. Morgan Asset Management Guide to the Markets terms of use reproduction"; am.jpmorgan.com/us/en/asset-management/adv/terms-of-use/ (read directly)
- **Found**: Quarterly PDF chartbook, free to view without login (some interactive tools/app need a Financial Professional or Shareholder login). Site terms of use (J.P. Morgan Chase) prohibit copying/distributing/reproducing content without prior written consent except under Copyright Act fair use.
- **Outcome**: adopted
- **Landed in**: catalog/sources/jpmorgan-guide-to-the-markets.json

## 2026-09-15 — Yardeni Research: reference entry
topics: equity-valuation, equity-returns, macro
- **Question**: What does Yardeni Research offer free vs. behind subscription, and what do its terms say about reuse?
- **Searched / read**: WebSearch "Yardeni Research free chart pdf archive stock market briefing"; yardeni.com (homepage, read directly); yardeni.com/copyright (read directly)
- **Found**: A handful of sample charts are free; full daily briefings and the 7,600+ real-time chart library require a paid subscription (4-week free trial, no card). archive.yardeni.com hosts older PDF chart books, appears to be a legacy mirror. Copyright/hedge-clause page prohibits any download/reproduction/dissemination of site material without explicit written consent.
- **Outcome**: adopted
- **Landed in**: catalog/sources/yardeni.json

## 2026-09-15 — Crestmont Research: reference entry
topics: equity-valuation, rates
- **Question**: What free content does Crestmont Research publish and what do its terms say about reuse?
- **Searched / read**: crestmontresearch.com (homepage, read directly); crestmontresearch.com/about/ (read directly, contains the site's terms/copyright section)
- **Found**: Free PDF/Excel downloads on secular stock-market cycles, P/E-vs-inflation, and interest-rate patterns. Copyright retained but explicit permission granted to use charts/quote text with attribution ("Copyright [year], www.CrestmontResearch.com"), plus a request (not requirement) to notify them of published use.
- **Outcome**: adopted
- **Landed in**: catalog/sources/crestmont.json

## 2026-09-15 — Advisor Perspectives (dshort): reference entry, terms page blocked
topics: equity-valuation, macro, real-estate
- **Question**: What is the dshort section of Advisor Perspectives, and what do its terms say about reuse?
- **Searched / read**: WebSearch "Advisor Perspectives dshort charts site"; WebFetch on advisorperspectives.com/dshort (403); curl with a real Chrome UA on the same URL (403); WebSearch "advisorperspectives.com terms of use reprint permission" (found the URL advisorperspectives.com/member/terms-of-use); WebFetch on that URL (403); curl with two different UAs on that URL (403 both times)
- **Found**: The site (Cloudflare-fronted) rejects every automated fetch attempted in this session, on both the content page and the terms page. Search-indexed summary text (not a direct page read) describes materials as "not [to] be copied, reproduced, modified, published... without Advisor Perspectives' prior written permission," with limited sharing via membership features.
- **Outcome**: gap — terms.status left as unverified (URL known, no verbatim quote confirmed) rather than restricted, since I cannot vouch for a quote I never read on the page myself
- **Landed in**: catalog/sources/advisor-perspectives.json

## 2026-09-15 — BlackRock Student of the Market: reference entry
topics: equity-valuation, equity-returns, macro
- **Question**: What is BlackRock's Student of the Market, how is it accessed, and what do BlackRock's site terms say about reuse?
- **Searched / read**: WebSearch "BlackRock Student of the Market monthly PDF chart pack"; blackrock.com/us/financial-professionals/insights/student-of-the-market (read directly via WebFetch and curl, curl used to locate the terms link in the page's raw HTML); blackrock.com/corporate/compliance/terms-and-conditions (read directly)
- **Found**: Monthly PDF/video/customizable deck, viewable and downloadable without login (only the branding customization tool needs an Advisor Center login). Site terms prohibit distributing/reposting/using content for public or commercial purposes without BlackRock's written permission, and separately prohibit automated (robot/spider) copying of the site.
- **Outcome**: adopted
- **Landed in**: catalog/sources/blackrock-student-of-the-market.json

## 2026-09-15 — Current Market Valuation: reference entry, no terms page exists
topics: equity-valuation, recession-dating
- **Question**: What valuation/recession models does currentmarketvaluation.com offer, and what do its terms say about reuse?
- **Searched / read**: WebFetch on currentmarketvaluation.com (404 — root path quirk); curl on currentmarketvaluation.com/ (200, read directly, footer and full link list inspected); curl + grep on currentmarketvaluation.com/about.php for any "terms of use"/"reproduc" text; WebSearch "currentmarketvaluation.com terms of use OR terms of service" (no site-specific terms page turned up)
- **Found**: Free tier covers all models on a quarterly update cadence; paid membership adds weekly updates, interactive graphs, and a members-only aggregate model, with a 7-day free trial. The only rights-related text anywhere on the site is the footer line "© Current Market Valuation. All rights reserved." — no dedicated terms-of-use page, no reproduction/reuse statement of any kind found in the homepage or about.php HTML.
- **Outcome**: adopted (as terms.status unknown, per the README's definition — site searched, no terms statement found)
- **Landed in**: catalog/sources/currentmarketvaluation.json

## 2026-09-15 — Koyfin as a design reference (free tier, terms unreadable)
topics: equity-returns, macro
- **Question**: What is Koyfin, what does its free tier offer, and what are its terms on reproducing/redistributing content?
- **Searched / read**: koyfin.com (homepage, WebFetch), koyfin.com/pricing (WebFetch), search "Koyfin free plan registration sign up required", app.koyfin.com/terms-and-conditions (WebFetch and curl with a Chrome UA)
- **Found**: Koyfin is a cross-asset charting/dashboard platform (stocks, ETFs, yields, indices, FX, commodities, macro, crypto, earnings transcripts, news). Free tier needs registration (email or Google/Apple, no card): 2yr financials + 1yr estimates, advanced charting, macro dashboards, 2 watchlists/screens/custom dashboards, limited snapshots, no ETF holdings/screener/press releases/filings. app.koyfin.com/terms-and-conditions returns 200 but is a client-rendered app shell (React/SPA) with no server-rendered terms text under any fetch method tried; a web search turned up a paraphrase (no-redistribution clause covering Koyfin's own and third-party/Morningstar data) but not a quotable original.
- **Outcome**: adopted (role: reference, terms.status: unverified — URL known, text unreadable by our tools)
- **Landed in**: catalog/sources/koyfin.json

## 2026-09-15 — testfolio as a design reference (SPA blocks reading its terms)
topics: equity-returns
- **Question**: What is testfol.io, is it free, and what do its terms say about reuse?
- **Searched / read**: testfol.io (curl + WebFetch, og:description read successfully), testfol.io/terms (curl with Chrome UA and Googlebot UA, WebFetch — all returned only the app shell), search "testfol.io sign up required backtest free account", search "testfol.io terms of use ... reproduce/redistribute/republish"
- **Found**: testfolio is a free portfolio backtester (asset allocation, rebalancing, cashflows, historical risk/return); basic backtesting needs no account, a free account raises limits/adds cloud save and is required for some advanced tools (e.g. Tactical Allocation, gated after API abuse). /terms is a real page (search results reference actual clauses about hypothetical backtests, no investment advice, third-party data) but every fetch attempt returned only the pre-render SPA shell (5032 bytes, identical across UAs), so no verbatim terms text could be captured.
- **Outcome**: adopted (role: reference, terms.status: unverified)
- **Landed in**: catalog/sources/testfolio.json

## 2026-09-15 — Callan Periodic Table blocked by Cloudflare to every fetch method tried
topics: equity-returns, global
- **Question**: What is the Callan Periodic Table of Investment Returns, how is it published, and what do Callan's terms say about reuse?
- **Searched / read**: WebFetch on callan.com/periodic-table/, callan.com/research/2025-classic-periodic-table/, and a guessed callan.com/terms-of-use/ (all 403); curl with a Chrome UA on the same three URLs plus extra Accept/Accept-Language headers (all 403, Cloudflare 'Attention Required' challenge page); search "Callan Periodic Table of Investment Returns terms of use copyright" and "callan.com terms of use site:callan.com" (found only page titles, no readable terms text)
- **Found**: callan.com sits behind Cloudflare bot protection that returned HTTP 403 to every automated request regardless of URL or headers — this is a block, not evidence the pages lack terms or don't exist. No official-page fact could be directly confirmed; the description in the file is built from search-result summaries and general knowledge of this well-known chart (created by Jay Kloepfer in 1999, annual, ranks 8-ish asset classes best-to-worst over ~20 years), which is not a citable primary source.
- **Outcome**: gap — access blocked; terms.status recorded as unknown with an explicit note that this reflects a fetch-tool limitation, and a flag for a future session with browser (not curl/WebFetch) access to re-verify
- **Landed in**: catalog/sources/callan-periodic-table.json

## 2026-09-15 — Novel Investor asset-class quilt: restrictive general terms, narrower embed exception
topics: equity-returns, global
- **Question**: What is Novel Investor's asset-class-returns quilt, and what do the site's terms say about reproducing it?
- **Searched / read**: novelinvestor.com/asset-class-returns/ (curl, full HTML parsed for footer/copyright/description), novelinvestor.com/terms-of-use/ (curl, full text parsed)
- **Found**: A 15-year ranked quilt across 8 asset classes plus a diversified blend. The page's own footer/embed feature offers a downloadable image and embed code with a 'Source: NovelInvestor.com' attribution requirement — but the site's general Terms of Use (section 10, Intellectual Property Information) is a standard restrictive clause: "Except for a single copy made for personal use only, you may not copy, reproduce, modify, republish, upload, post, transmit, or distribute any documents or information from this site in any form or by any means without prior written permission..."
- **Outcome**: adopted (role: reference, terms.status: restricted — quoted; noted the narrower embed exception without treating it as overriding the general restriction)
- **Landed in**: catalog/sources/novel-investor.json

## 2026-09-15 — UBS Global Investment Returns Yearbook: free public summary PDF, permission-gated quoting
topics: equity-returns, global, inflation, rates
- **Question**: Is there a free version of the UBS/Dimson-Marsh-Staunton Global Investment Returns Yearbook, how is it accessed, and what does it say about reuse?
- **Searched / read**: search "UBS Global Investment Returns Yearbook Dimson Marsh Staunton free summary PDF download" (found the direct PDF URL), giry2026-summary-public.pdf downloaded via curl and read in full (title/foreword, Imprint page 18, General disclaimer page 19)
- **Found**: UBS publishes a free 19-page 'Public summary edition' PDF each year (no registration) extracting charts/findings from the full 310-page paid Yearbook (35 markets, back to 1900, by Dimson/Marsh/Staunton). The full report and underlying DMS dataset are commercial, reached only by contacting the authors directly (pmarsh@london.edu) or a UBS rep. Imprint page: "Copyright © 2026 Elroy Dimson, Paul Marsh and Mike Staunton. All rights reserved. No part of this document may be reproduced or used in any form...without prior written permission from the copyright holders," plus a 'To quote from this publication' clause requiring authors' permission and a specific acknowledgement line on any reused chart/table.
- **Outcome**: adopted (role: reference, terms.status: restricted — quoted)
- **Landed in**: catalog/sources/ubs-global-investment-returns-yearbook.json

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
