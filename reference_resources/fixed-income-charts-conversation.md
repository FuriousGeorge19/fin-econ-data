# Fixed Income Charts — Planning Conversation

This conversation covers data sources, chart design, and organization for a web-based fixed income / yield curve dashboard. It's intended as a reference for implementation in Claude Code.

---

## Q: What sources should we use for yield curve data? How should it be presented? What are best practices?

**Context:** Building charts and tables for a website using Claude Code. Want current and historical data for all major points on the yield curve. For long-term history, go as far back as dependable even if it requires patching together multiple series with different sources and frequencies. For recent data, want daily data.

### Data Sources — A Tiered Approach

**Tier 1: FRED (St. Louis Fed)** — the primary workhorse. The FRED API is free, well-documented, and offers both daily and monthly series for all standard tenors. Key series IDs follow a clean pattern:

Daily series use the `DGS` prefix (DGS1MO, DGS3MO, DGS6MO, DGS1, DGS2, DGS3, DGS5, DGS7, DGS10, DGS20, DGS30). These generally start in the early 1990s for shorter tenors and go back further for benchmarks like the 10-year. Monthly series use `GS` prefix (GS10 back to April 1953, GS5 to 1953, GS3M to 1982) and `TB` prefix for T-bills (TB3MS goes back to January 1934).

**Tier 2: Treasury.gov XML/CSV feed** — useful for same-day data. Treasury publishes daily yield curve rates at treasury.gov/resource-center/data-chart-center. This can supplement FRED if you need intraday freshness, since FRED has a slight lag.

**Tier 3: Long-run historical patches.** For going deeper than the 1950s: Robert Shiller's dataset (long-term government bond yields back to 1871, monthly), the NBER Macrohistory database (some short-rate series back to the 1800s), and Sidney Homer & Richard Sylla's *A History of Interest Rates* (scholarly gold standard but not machine-readable without effort).

### Practical Architecture for Stitching Series

The further back you go, the fewer tenors you have and the coarser the frequency. A good schema acknowledges this:

**1990–present:** Full curve, daily. All 11 standard tenors from FRED's DGS series. The 30-year has a gap (Feb 2002–Feb 2006 when Treasury suspended issuance) — interpolate or leave null with a UI annotation. The 20-year was reintroduced in May 2020, so it's sparse before that.

**1953–1990:** Core tenors, monthly. GS10, GS5, GS3, GS1 are solid. Short end via TB3MS and TB6MS. You lose the 2-year, 7-year, and 20-year for much of this period.

**1934–1953:** Thin curve, monthly. Essentially just the 3-month T-bill (TB3MS) and perhaps a long bond proxy. Shiller's long-rate series can fill the long end.

**Pre-1934:** Shiller's data only, monthly, basically one "long-term rate" series. Useful for context (150 years of long rates) but not a real curve.

The data model should carry metadata per observation: source, original frequency, and whether it's an original observation or interpolated/spliced.

### Presentation — What Works Well

**The essentials (high value, moderate complexity):**

- **Yield curve snapshot** — current rates plotted across tenors with the ability to overlay historical dates for comparison. Add a toggle to show the curve from 1 week, 1 month, 1 year, and 5 years ago as ghost lines.
- **Spread time series** — the 10y-2y and 10y-3m spreads over time, with recession shading (FRED series USREC). Every inversion since the 1960s preceded a recession.
- **Multi-tenor time series** — let users select tenors and see them on a shared time axis. Color-code by maturity.

**The impressive (higher complexity, high impact):**

- **Heatmap** with time on the y-axis, tenor on the x-axis, color mapped to yield. Instant visual of regime shifts.
- **3D surface plot** (time × tenor × yield) — visually striking but a heatmap often communicates the same information more accessibly.
- **Animated curve** — a play button stepping through time. Effective for storytelling.

### Best Practices

**Data engineering:** Cache FRED pulls aggressively, store in a normalized format with date/tenor/yield/source columns, handle missing data explicitly (FRED returns "." for holidays — don't coerce to zero), document every splice point. Use the FRED API with your own key.

**Presentation:** Always show recession shading on time-series charts, label the current yield curve with actual values, make the 30-year gap (2002-2006) visible rather than hiding it. Use consistent color scales — sequential for heatmaps, diverging (red/blue) for spreads where zero is meaningful.

**Frequency mixing:** When showing long-run data transitioning from monthly to daily, either downsample daily to monthly for consistency, or clearly indicate the frequency change. Don't upsample monthly to daily — it creates false precision.

### Implementation Notes

Use FRED's API as the single data layer, store fetched data as JSON or SQLite for caching, build charts with D3.js or Recharts depending on the stack.

---

## Q: Can we make everything daily? For monthly data from the 1930s, assign it to a single day and let the gaps communicate that finer-grained data isn't available.

Yes — this is a clean solution. It avoids the two bad alternatives (upsampling with fake precision, or maintaining parallel schemas for different frequencies).

### Key considerations:

**Date assignment convention.** FRED's monthly series like GS10 and TB3MS are already dated to the first of the month. Stick with that — it's the convention the source uses.

**Charting implications.** Line chart connector lines will span 30-day gaps in the monthly era versus 1-day gaps in the daily era. This looks fine zoomed out (where monthly and daily are visually indistinguishable), and at closer zoom levels the spacing difference is exactly the signal you want. A point/scatter layer underneath the lines makes the density change even more legible.

**Computed series.** For derived data like the 10y-2y spread, only compute for dates where both inputs actually exist. With everything on a single daily timeline, a simple inner join on date handles this automatically.

**Tooltip/annotation opportunity.** When a user hovers on a data point from the pre-daily era, show "Monthly observation" in the tooltip alongside the source. Lightweight, no schema complexity.

### Recommended schema:

One unified daily-indexed table with date, tenor, yield, and source. Simple to query, simple to chart, and the visual density tells the data-quality story without extra UI machinery.

---

## Q: What about real interest rate measures?

### TIPS Yields — The Direct Market Measure

TIPS give you a market-priced real yield directly. FRED daily series: DFII5, DFII7, DFII10, DFII20, DFII30. Problem is history — 10-year TIPS only starts January 2003, 5-year in 2004. These are the cleanest real rate for the modern era — directly observable, no model needed, what fixed income professionals actually trade.

### Breakeven Inflation — A Free Bonus

Nominal minus TIPS yield for the same tenor = breakeven inflation rate (the market's implied inflation expectation). FRED: T10YIE, T5YIE. You get this for free from data you're already pulling. Worth including as a derived series.

### Ex-Post Real Rates — Simple, Long History, Backward-Looking

Nominal yield minus trailing realized CPI inflation. Computable back to the 1930s for T-bills and CPI (FRED: CPIAUCSL, back to 1913). The math is trivial — subtract year-over-year CPI change from the nominal yield.

**Drawback:** This tells you what the real rate *turned out to be*, not what investors expected. During inflation shocks (1973-74, 1979-80) the ex-post real rate goes deeply negative even though nobody intentionally bought bonds at negative real yields. Label clearly as "realized" or "ex-post."

### Ex-Ante Real Rates — What Investors Actually Expected

Nominal yield minus expected inflation. Three options for expectations:

- **Michigan Survey** (FRED: MICH) — consumer 1-year inflation expectations, monthly, back to 1978. Simple, widely used, but reflects consumer sentiment rather than market pricing.
- **Cleveland Fed Inflation Expectations** — model-based estimates at multiple horizons (1-year through 30-year), monthly, back to 1982. FRED: EXPINF1YR, EXPINF10YR, etc. Best bet for systematic ex-ante real rates across tenors.
- **SPF (Survey of Professional Forecasters)** — Philadelphia Fed, quarterly, back to 1968. Higher quality respondents but coarser frequency.

### Recommendation

**Two real rate series, clearly distinguished:**

1. **TIPS yields** as "market real rate" for 2003-present, daily. Display alongside nominal yields on the curve snapshot with a toggle between nominal and real curve.
2. **Ex-post real rate** (nominal minus trailing 12-month CPI) as the long-run series, going back to the 1930s or further. Label plainly as "nominal yield minus realized inflation." Shows financial repression in the 1940s, deeply negative 1970s, post-2008 and 2020-2022 episodes.

**Consider skipping** the ex-ante approach unless you want the complexity. TIPS already gives you the market's ex-ante real rate for the modern period, and ex-post is more intuitive for the historical view.

**Presentation note:** When showing real rates over a very long horizon, recession shading becomes even more valuable. The pattern of real rates turning negative before or during recessions — and the 1940s financial repression era — jumps off the chart.

---

## Q: How should these charts be organized? Not by asset class — by analytical question.

**Context:** Three identified use cases:
- **Economic** — understanding where rates are now versus history and implications for medium-term growth, recession likelihood, etc.
- **Financial market** — implications for asset prices, risk-adjusted returns on fixed income versus equities.
- **Investable assets** — what returns are available on different fixed income securities right now.

### Key Insight

Organizing by asset class is organizing by *data source*, when what you actually want is organization by *analytical question*. The yield curve shows up in all three use cases but surrounded by different context each time.

### Suggested Structure

**Economy** — macro conditions, leading indicators, the "where are we in the cycle" view. Yield spreads, real rates, labor, inflation, GDP. Heavy use of recession shading. The long-run historical depth matters most here. Natural companions: unemployment rate, initial claims, SAHM rule indicator, CPI, PCE, breakevens, GDP growth, leading indicator composites. Fed Funds rate belongs here as a policy variable.

**Markets** — relative valuation and risk pricing across asset classes. Equity risk premium (earnings yield minus 10-year real rate), credit spreads (IG and HY OAS over Treasuries), cross-asset volatility. Natural companions: equity valuation measures (Shiller CAPE, forward P/E, Buffett Indicator), VIX, credit spreads (FRED: BAMLC0A0CM, BAMLH0A0HYM2), dollar index. Fixed income and equities *must* live side by side here because the analytical question demands comparison.

**Rates & Yields** — the practical "what can I earn" dashboard. Current curve, current TIPS yields, savings and CD rates, possibly a simple bond return calculator. This is the only section organized by asset class, and that's fine because the question itself is asset-specific.

### Cross-Section Note

Some series appear in multiple sections with different presentations. The 10-year yield shows up in Economy (time series with recession shading and spread calculations), Markets (denominator in the equity risk premium), and Rates (current number on the curve snapshot). That's not duplication — it's the same data answering different questions.

**Implementation implication:** The data layer should be unified (one cache of FRED series), but chart components should be organized by section, each pulling from the shared data and presenting it in the appropriate analytical context.

---

## Q: Stack rank the top 10 charts to build first.

Not organizing by section yet — just building individual charts, and the having them in front of me will help clarify their organization.

### Ranked List

**1. Yield curve snapshot with historical overlays.**
Current curve across all tenors, with ghost lines for 1 week, 1 month, 1 year, and 5 years ago. The single chart every fixed income discussion starts with. Pull the full DGS series set from FRED.

**2. 10y-2y and 10y-3m spreads, long history, with recession shading.**
The inversion chart. Use GS10 minus GS2 (or TB3MS for the 3-month version to get back to the 1980s). Overlay USREC for recession bars. Predictive track record is remarkable.

**3. Fed Funds rate, long history, with recession shading.**
FEDFUNDS back to 1954. The single most important rate in the economy. Simple to build, massive payoff.

**4. 10-year nominal yield, ultra-long history.**
Stitch GS10 (1953-present) with Shiller's long bond yield (1871-1953). Shows the entire secular bond bull market from 1981 to 2020 and puts today's rates in 150-year context.

**5. Ex-post real short rate (3-month yield minus trailing CPI).**
TB3MS minus year-over-year CPIAUCSL change. Shows financial repression in the 1940s, deeply negative real rates in the 1970s, Volcker shock, ZIRP, and current regime. Best chart for understanding the saver's actual experience over time.

**6. Breakeven inflation (10-year).**
T10YIE from FRED, 2003-present. Market's inflation expectations in one line. Short history but extremely high signal. Quick to implement — single pre-computed FRED series.

**7. Equity risk premium.**
S&P 500 earnings yield (inverse of Shiller CAPE, or forward P/E from Damodaran) minus 10-year real yield (DFII10 for TIPS era, or ex-post real for longer history). Bridges Economy and Markets sections. Tells you whether stocks are compensating for risk relative to bonds.

**8. Credit spreads — IG and HY OAS.**
FRED series BAMLC0A0CM (investment grade) and BAMLH0A0HYM2 (high yield), from ICE BofA, back to 1996-1997. With recession shading, shows risk appetite in real time. Two lines, one chart, high information density.

**9. Multi-tenor time series with selectable tenors.**
User picks 2-4 tenors and plots them together over a chosen time range. Exploratory workhorse for investigating specific questions.

**10. TIPS real yield curve snapshot.**
Current real yields across 5, 7, 10, 20, and 30-year TIPS tenors. Answers "what real return can I lock in right now." Historical overlays work well since the TIPS market has gone through dramatic regime changes since 2003.

### Implementation Notes

The first five cover the core macro story with straightforward FRED data. Charts 6-8 add cross-asset and market-conditions layers. Charts 9-10 round out interactive and practical dimensions. Each builds on the same FRED data infrastructure, so marginal effort per chart decreases as you go.

---

## Key FRED Series Reference

### Nominal Yields — Daily
| Series ID | Description |
|-----------|-------------|
| DGS1MO | 1-Month Treasury |
| DGS3MO | 3-Month Treasury |
| DGS6MO | 6-Month Treasury |
| DGS1 | 1-Year Treasury |
| DGS2 | 2-Year Treasury |
| DGS3 | 3-Year Treasury |
| DGS5 | 5-Year Treasury |
| DGS7 | 7-Year Treasury |
| DGS10 | 10-Year Treasury |
| DGS20 | 20-Year Treasury |
| DGS30 | 30-Year Treasury |

### Nominal Yields — Monthly (longer history)
| Series ID | Description | Start |
|-----------|-------------|-------|
| GS10 | 10-Year Treasury | 1953 |
| GS5 | 5-Year Treasury | 1953 |
| GS3 | 3-Year Treasury | 1953 |
| GS1 | 1-Year Treasury | 1953 |
| TB3MS | 3-Month T-Bill | 1934 |
| TB6MS | 6-Month T-Bill | 1958 |

### TIPS Real Yields — Daily
| Series ID | Description | Start |
|-----------|-------------|-------|
| DFII5 | 5-Year TIPS | 2004 |
| DFII7 | 7-Year TIPS | 2003 |
| DFII10 | 10-Year TIPS | 2003 |
| DFII20 | 20-Year TIPS | 2004 |
| DFII30 | 30-Year TIPS | 2004 |

### Breakeven Inflation
| Series ID | Description |
|-----------|-------------|
| T10YIE | 10-Year Breakeven Inflation |
| T5YIE | 5-Year Breakeven Inflation |

### Other Key Series
| Series ID | Description | Start |
|-----------|-------------|-------|
| FEDFUNDS | Fed Funds Rate | 1954 |
| CPIAUCSL | CPI (All Urban Consumers) | 1913 |
| USREC | NBER Recession Indicator | 1854 |
| MICH | Michigan Inflation Expectations | 1978 |
| BAMLC0A0CM | IG Corporate OAS | 1996 |
| BAMLH0A0HYM2 | HY Corporate OAS | 1997 |

### External Data Sources
| Source | Description | Coverage |
|--------|-------------|----------|
| Shiller (Yale) | Long-term bond yields, stock data | 1871–present |
| Cleveland Fed | Inflation expectations by horizon | 1982–present |
| Damodaran (NYU) | Equity risk premium data | Varies |
