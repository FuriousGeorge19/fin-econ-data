## ADDED Requirements

### Requirement: Section placement and chart type for the S&P 500 P/E series

`series/sp500_pe.json` SHALL carry a `presentation` block placing the series in the
`markets` section with `order` 7 and chart type `sp500_pe`, a custom module at
`site/js/charts/sp500_pe.js` that draws the confirmed trace and the dashed estimated
trace (prepended with the last confirmed point), provides the latest / long-term
average / 10-year high and low stats, the 24-row table with the dagger note, and the
`date,pe,price,earnings,estimated` CSV; presets 1Y / 10Y / 25Y / 50Y / All; no
recession shading by default.

#### Scenario: P/E page renders with the distinction visible

- **WHEN** the user opens `/charts/sp500_pe/` or a grid listing the series
- **THEN** the card shows the P/E chart with the confirmed-vs-estimated distinction
  visible and the Markets nav row lists "S&P 500 P/E"

## REMOVED Requirements

### Requirement: Tab label for the S&P 500 P/E series
**Reason**: There are no tabs; placement is a descriptor `presentation` value.
**Migration**: "Section placement and chart type for the S&P 500 P/E series" above.
