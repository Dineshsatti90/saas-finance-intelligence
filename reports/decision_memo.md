# SaaS financial planning: decision memo

## Scope and observed financials
The warehouse contains 3,832,977 real SEC numeric records from the full 2025 Q4 population plus 171,654 company-fact observations across eight peers. Population size is not the number of comparable SaaS annual statements. Peer histories are normalized separately from the population, with source tags and filing dates preserved.

Salesforce latest complete annual financials available as of 2026-11-26: year ended 2026-01-31. Revenue $41.52bn. The gross-profit change versus the prior year is $3,003.0m, decomposed into a $2,802.1m revenue effect at prior margin and a $200.9m margin effect at current revenue. These are arithmetic bridge components, not proven causal explanations.

## Forecast evidence
Rolling annual forecasts use only filings public at the origin date. Flat-revenue WAPE: 15.00%; trailing-growth WAPE: 4.16%. Evaluation targets use latest available restated actuals at the analysis cutoff. This is a comparison of external forecasts against reported actuals, not internal budget versus actual.

## Planning decision
Use the workbook to explore revenue growth, cost ratios and spending growth. Base/downside growth and spending assumptions are illustrative editable inputs, not management guidance. Use the AI pricing calculator to establish contribution break-even under your own customer, adoption, usage and cost assumptions before proposing a price. No default customer economics are presented as real company data.

## Missing evidence and model boundaries
Public GAAP revenue is not ARR. Customer additions, expansion/churn ARR, paid FTE, internal budgets and AI inference bills are unavailable. The ARR/headcount/AI schedules therefore have blank editable inputs and show n.a. until populated. Historical financials remain real. Cash forecast is an operating-cash-flow conversion scenario before financing, acquisitions, investments, repurchases and FX; it is not a full cash balance forecast. Annual peer fiscal ends differ; compare like durations, not calendar-year labels.

## Source trail
`annual_facts.csv` contains accession, source URL, tag, fiscal period and filed date for every normalized metric. `source_manifest.json` fingerprints the downloaded inputs. `backtest.csv` contains every forecast origin, target and error. `variance_evidence.json` owns the bridge calculations. AI generated output, when configured, selects verified observations rather than inventing narrative causes.
