# SaaS financial planning: decision memo

## Scope and observed financials
The warehouse contains 3,832,977 real SEC numeric records from the full 2025 Q4 population plus 171,654 company-fact observations across eight peers. Population size is not the number of comparable SaaS annual statements. Peer histories are normalized separately from the population, with source tags and filing dates preserved.

Salesforce latest complete annual financials available as of 2026-11-26: year ended 2026-01-31. Revenue $41.52bn. The gross-profit change versus the prior year is $3,003.0m, decomposed into a $2,802.1m revenue effect at prior margin and a $200.9m margin effect at current revenue. These are arithmetic bridge components, not proven causal explanations.

## Forecast evidence
Rolling annual forecasts use only filings public at the origin date. Flat-revenue WAPE: 15.00%; trailing-growth WAPE: 4.16%. Evaluation targets use latest available restated actuals at the analysis cutoff. This is a comparison of external forecasts against reported actuals, not internal budget versus actual.

That two-baseline study covers 58 targets. The additional expanding-window driver study compares all three methods on the same 40 eligible targets: driver WAPE 3.99%, trailing growth 4.44%, flat revenue 14.23%. Use that paired result when comparing methods; see [driver benchmark](driver_backtest_summary.json) and its per-origin forecasts.

## Planning decision
Test metered AI pricing at $0.015/request in the explicitly fictional IllustrativeCo case. At the seeded assumptions it contributes $18,000/month versus $8,000 for the $25 add-on; metered break-even is $0.0105/request. These are scenario results, not observed customer economics. See [pricing decision](pricing_decision.md) for assumptions, usage limits and the conditions that change this recommendation. Base/downside growth and spending assumptions are editable inputs, not management guidance.

## Missing evidence and model boundaries
Public GAAP revenue is not ARR. Customer additions, expansion/churn ARR, paid FTE, internal budgets and AI inference bills are unavailable. The populated ARR/headcount/AI schedules are an explicitly fictional operating case, separately labeled from real reported financials. The public builder also supports a blank template. Cash is an operating-cash-flow conversion scenario before financing, acquisitions, investments, repurchases and FX; it is not a full cash balance forecast. Annual peer fiscal ends differ; compare like durations, not calendar-year labels.

## Source trail
`annual_facts.csv` contains accession, source URL, tag, fiscal period and filed date for every normalized metric. `source_manifest.json` fingerprints the downloaded inputs. `backtest.csv` contains every forecast origin, target and error. `variance_evidence.json` owns the bridge calculations. AI generated output, when configured, selects verified observations rather than inventing narrative causes.
