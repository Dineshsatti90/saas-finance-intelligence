# AI feature pricing: illustrative investment decision

## Recommendation
In this illustrative case, prefer metered pricing at $0.015/request: it contributes $18,000/month versus $8,000 for the $25 add-on. If choosing the add-on, cap included requests at 2,500 per adopting account to avoid negative contribution under unchanged costs.

## Assumptions and calibration
This is **IllustrativeCo, a fictional operating case**, not Salesforce customer/ARR/AI-cost data. It assumes 10,000 eligible accounts, 20% adoption, 2,000 requests per adopting account each month, 2,000 input/500 output tokens per request, $2/$8 per million input/output tokens, and $10,000 incremental fixed cost per month. Token rates are scenario inputs, not current provider quotations. Core MRR is assumed $100/account; the reported Salesforce gross margin (77.68%) calibrates the simplified core retention calculation.

## Calculated economics
At these assumptions inference costs $32,000/month. The subscription break-even price is $21.00/adopting account/month. Metered break-even is $0.0105/request. $25 subscription revenue contributes $8,000/month after incremental fixed cost; $0.015/request contributes $18,000/month. Bundling costs $42,000/month without direct feature revenue.

Bundling would need approximately 541 additional accounts retained for a full year, or 5.41 percentage points of annual churn improvement in the entire 10,000-account base, to cover that cost under the simplified retention model. No such retention benefit has been observed.

## Decision conditions
Use metered pricing as the initial test hypothesis. Revisit it if demand elasticity or adoption differs across pricing options, or if support, safety, hosting, payment fees, taxes or token-mix costs change. Run an instrumented pricing test before approving an investment based on these assumptions. See `pricing_case.json` and `inputs/illustrative_case.json` for the full calculation trail.
