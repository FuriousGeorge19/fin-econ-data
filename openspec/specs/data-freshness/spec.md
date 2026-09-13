# data-freshness Specification

## Purpose
TBD - created by archiving change s3-series-metadata. Update Purpose after archive.
## Requirements
### Requirement: Business-day calendar

`scripts/staleness.py` SHALL define a business day as Monday to Friday excluding US
bond-market holidays: the US federal holidays (observed dates) and Good Friday,
computed by rule with no external dependency, plus an `extra_closures` list of one-off
dates. Good Friday SHALL be treated as closed even in years when Treasury markets
trade, because the error in that direction is one extra day of slack rather than a
false badge.

#### Scenario: Thanksgiving week

- **WHEN** one business day is added to Wed 2026-11-25
- **THEN** the result is Fri 2026-11-27 (Thanksgiving skipped; the Friday after is a
  business day)

#### Scenario: Good Friday

- **WHEN** one business day is added to Thu 2027-03-25
- **THEN** the result is Mon 2027-03-29

#### Scenario: One-off closure

- **WHEN** `2025-01-09` is listed in `extra_closures` and one business day is added to
  Wed 2025-01-08
- **THEN** the result is Fri 2025-01-10

### Requirement: Due-by rule

The fetcher SHALL compute `due_by` for an input with cadence `c`, publication lag `L`
business days and last observation `d` as `period_end(d)` (daily: `d`; monthly: the
last day of `d`'s month; quarterly: the last day of `d`'s calendar quarter), advanced
one cadence step (daily: the next business day; monthly: the last day of the next
month; quarterly: the last day of the next quarter), plus `L` business days. An input
is overdue on a viewing date `V` exactly when `V > due_by`. For a daily input with
`L = 1` this equals the 2026-08-29 rule "overdue when more than cadence plus
publication lag business days have passed".

#### Scenario: Daily, lag 1

- **WHEN** DGS10's last observation is Thu 2026-09-10
- **THEN** `due_by` is Mon 2026-09-14, so the series is on time through Monday and
  overdue from Tue 2026-09-15

#### Scenario: Daily across Labor Day

- **WHEN** DGS10's last observation is Thu 2026-09-03
- **THEN** `due_by` is Tue 2026-09-08 (Fri 09-04 is the next period; Mon 09-07 is
  skipped)

#### Scenario: Monthly, lag 1

- **WHEN** the P/E price input's last observation is `2026-08-01`
- **THEN** `due_by` is Thu 2026-10-01

#### Scenario: Monthly, lag 5

- **WHEN** USREC's last observed month is `2026-08-01`
- **THEN** `due_by` is Wed 2026-10-07

#### Scenario: Quarterly, lag 60

- **WHEN** the earnings input's last confirmed quarter ends `2025-09-30`
- **THEN** `due_by` is Mon 2026-03-30 (60 business days after Wed 2025-12-31, skipping
  1 Jan, 19 Jan and 16 Feb 2026)

### Requirement: Dataset due-by rolls up over required active inputs

A dataset's `as_of.due_by` SHALL be the earliest `due_by` among its inputs that are
`required` and whose `status` is `active`. Inputs with `status: discontinued` SHALL be
excluded from the roll-up. A single-input dataset's `due_by` is that input's.

#### Scenario: Discontinued input excluded

- **WHEN** `series/sp500_pe.json` marks the earnings input `status: discontinued` and
  the price input's `due_by` is `2026-10-01`
- **THEN** `as_of.due_by` is `2026-10-01` even though the earnings input's own `due_by`
  is long past

### Requirement: Python computes, the browser compares on the US Eastern date

`due_by` SHALL be computed at fetch time and stored in the data file; the browser SHALL
NOT perform business-day or holiday arithmetic. The browser SHALL define "today" as
the current calendar date in `America/New_York` (for example via
`toLocaleDateString('en-CA', {timeZone: 'America/New_York'})`) and SHALL treat a
dataset or input as overdue exactly when that date is later than its `due_by`.

#### Scenario: Viewer east of UTC

- **WHEN** it is 10:00 Tuesday in Sydney (20:00 Monday US Eastern) and DGS10's
  `due_by` is Mon 2026-09-14
- **THEN** no badge is shown, because the Eastern date is still Monday

#### Scenario: Healthy pipeline never badges

- **WHEN** each weekday's run (after FRED's ~16:15 ET update) deploys before US
  Eastern midnight
- **THEN** no daily series shows a badge on any calendar date

#### Scenario: One missed run

- **WHEN** Monday's run fails and Tuesday's page still carries Thursday's observation
  with `due_by` Monday
- **THEN** the badge appears on Tuesday (Eastern date) and disappears once a newer
  file is deployed

### Requirement: Overdue badge

When a dataset is overdue, its chart SHALL show a badge beside the chart title reading
`Overdue · expected by <due_by as 14 Sep 2026> · <N> days late`, where `N` is the
number of calendar days from `due_by` to today. For a multi-input dataset the badge
SHALL name the overdue input and its expected period, for example `Earnings overdue ·
Q4 2025 expected by 30 Mar 2026 · 167 days late`. When the dataset is on time no badge
SHALL be shown; the in-chart source line already carries the data-through date.

#### Scenario: Three days late

- **WHEN** today (Eastern) is 2026-09-17 and `due_by` is `2026-09-14`
- **THEN** the badge reads `Overdue · expected by 14 Sep 2026 · 3 days late`

#### Scenario: On time

- **WHEN** today (Eastern) is on or before `due_by`
- **THEN** no badge element is rendered for that chart

### Requirement: Discontinued input is stated, not alarmed

An input with `status: discontinued` SHALL be described in the in-chart source line and
the About tab using its `status_note`, and SHALL never produce an overdue badge.

#### Scenario: Discontinued earnings source

- **WHEN** the P/E chart renders with the earnings input discontinued
- **THEN** its source line ends `earnings confirmed through Q3 2025, estimated since
  Jan 2026 (source discontinued)` and the About tab shows the `status_note`, with no
  badge attributable to the earnings input

### Requirement: Staleness check reads as_of

The staleness check SHALL evaluate each dataset from its data file's `as_of.due_by`
(and per-input `due_by`) against today's US Eastern date, replacing the hard-coded
`SERIES` table; this applies to `scripts/staleness.py`'s `check()`,
`tests/test_staleness.py` and `scripts/dev.sh` alike. The
check SHALL report, per dataset and per input, the last observation, `due_by`, and
whether it is overdue. `tests/test_staleness.py` SHALL carry a `staleness` pytest
marker so CI can run it separately from the deploy gate.

#### Scenario: dev.sh warning

- **WHEN** `scripts/dev.sh` runs on a checkout whose `data/dgs10.json` has `due_by`
  earlier than today
- **THEN** it prints a warning line for `dgs10` naming the last observation and
  `due_by`, and still serves the site

