# S&P 500 P/E Ratio: How Multpl.com Constructs the Monthly Table

## What It Is (and Isn't)

This is **not** a forward P/E. The multpl.com S&P 500 P/E is based on **trailing twelve month "as reported" earnings** — the current PE is estimated from the latest reported earnings and the current market price. So it's a trailing TTM P/E using GAAP "as reported" figures, which is a more conservative earnings measure than operating earnings (which strip out write-downs, restructuring charges, etc.).

---

## How It's Constructed

There are two distinct segments with different data sources:

### Historical Data (back to 1871)

The source is Robert Shiller and his book *Irrational Exuberance*. Shiller maintains a freely downloadable Excel spreadsheet on his Yale website (`http://www.econ.yale.edu/~shiller/data.htm`) with monthly S&P 500 price and earnings data going back to 1871. Multpl pulls price and TTM earnings from that sheet and computes P/E = price ÷ TTM earnings.

### Recent / Current Data (marked with †)

Values for the most recent months are **estimates** — S&P Global hasn't yet reported the next trailing earnings period, so multpl holds the denominator fixed at the last reported TTM earnings and just updates the numerator (index price) as it moves. As of early March 2026, the earnings denominator is held at the TTM figure through September 2025 — the latest period reported by S&P.

---

## The Formula

```
P/E = S&P 500 Index Level ÷ (Sum of trailing 4 quarters of "as reported" EPS)
```

The **"as reported" EPS** is GAAP net income including all charges — not the adjusted/operating figure Wall Street typically uses. This is why the multpl trailing P/E tends to be higher than the forward P/E or the operating-earnings-based P/E cited by most sell-side strategists.

---

## How to Replicate It

| Component | Free Source |
|---|---|
| Historical P/E + earnings back to 1871 | Robert Shiller's Excel file at his Yale page |
| Current S&P 500 index level | Yahoo Finance, Google Finance, FRED, etc. |
| Latest TTM "as reported" S&P 500 EPS | S&P Global quarterly earnings scorecard (free PDF) |
| Multpl data via API | Quandl/Nasdaq Data Link under `MULTPL/SP500_PE_RATIO_MONTH` (may require subscription) |

The **Shiller spreadsheet** is the real workhorse — it's the cleanest single source for the full monthly series and is updated regularly. Combined with the current S&P 500 level and the latest S&P-reported TTM earnings, you can reproduce the table almost exactly.

---

## Important Caveat: Trailing vs. Forward P/E

This table is entirely **backward-looking**. The forward P/E — based on consensus analyst estimates for the next 12 months — is a completely different series and requires a commercial data provider like FactSet, Bloomberg, or Refinitiv. There is no clean, free historical time series for forward P/E the way there is for trailing P/E via the Shiller dataset.

---

## Key Data Links

- **Shiller Data**: http://www.econ.yale.edu/~shiller/data.htm
- **Multpl Source Page**: https://www.multpl.com/s-p-500-pe-ratio
- **Monthly Table**: https://www.multpl.com/s-p-500-pe-ratio/table/by-month
- **S&P Earnings Scorecard**: https://www.spglobal.com/spdji/en/indices/equity/sp-500/
