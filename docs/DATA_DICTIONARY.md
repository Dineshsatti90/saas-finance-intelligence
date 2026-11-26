# Financial data dictionary

## Source population

| Input | Reference rows | Grain |
| --- | ---: | --- |
| `sec_sub` | 6,304 | Filing submission |
| `sec_num` | 3,832,977 | XBRL numeric fact by filing/tag/period/unit/context |
| `sec_tag` | 84,907 | Tag metadata |
| `sec_pre` | 719,346 | Financial-statement presentation record |
| Eight company-facts JSON files | 171,654 observations | Reported tagged observations, including repeated comparative vintages |

All four SEC bulk tables are ingested as source strings. They support population profiling. The company-facts files are a separate source used to normalize peer annual financials; their records must not be blindly appended to the bulk table as additional unique economic events.

## Normalized outputs

| Output | Grain / interpretation |
| --- | --- |
| `annual_facts.csv` | Ticker × metric × fiscal period end, selected at analysis cutoff |
| `annual_financials.csv` | Ticker × fiscal period end with supported annual financial metrics |
| `peer_metrics.csv` | Annual financials with revenue growth and operating/gross/FCF ratios |
| `backtest.csv` | Ticker × historical origin × target period × forecast method |
| `population_coverage.csv` | Filing form with population filing/fact coverage |
| `population_annual_revenue.csv` | Raw candidate annual revenue observations from bulk 10-K filings; not deduplicated comparable companies |
| `model_inputs.json` | Salesforce actual financials with per-metric sources and separately labeled planning rates |
| `variance_evidence.json` | Gross-profit bridge values and reconciliation difference |

## Core metric definitions

- **Revenue:** supported US-GAAP annual USD revenue tag; not ARR, bookings or customer cash receipts.
- **Gross profit:** reported gross profit where present; otherwise revenue less supported cost-of-revenue tag. Missing cost information is not assumed zero.
- **Operating income:** reported operating income/loss, retaining negative values.
- **Free cash flow:** operating cash flow less capital expenditure represented by payments to acquire property, plant and equipment. This definition may differ from an issuer's adjusted FCF measure.
- **Operating margin:** operating income / matching annual revenue.
- **FCF margin:** defined FCF / matching annual revenue.
- **Revenue growth:** current normalized annual revenue / preceding normalized annual revenue − 1. Check adjacent fiscal periods before interpreting unusual observations.
- **WAPE:** total absolute forecast error / total actual target revenue. Larger companies have greater weight.
- **MAPE:** unweighted mean absolute percentage error across valid forecast observations.
- **AI contribution:** incremental feature revenue − inference cost − incremental fixed cost. It excludes unspecified sales/support/tax costs and retention benefits.

`filed`, `accn`, `tag`, `period_end`, `source_url` and `asof` preserve a metric's audit trail. Fiscal year ends remain explicit because peers have different fiscal calendars. Do not relabel this panel as calendar-year or monthly company actuals.
