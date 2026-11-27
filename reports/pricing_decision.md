# AI pricing: equal-price decision and usage risk

## Recommendation
Test a capped add-on against metered pricing at an equal baseline price of $0.0125/request. Both contribute $8,000/month at 2,000 requests and equal adoption. Choose based on heavy-usage risk and measured demand response, not the previous unequal-price comparison.

The former $0.015/request example billed $30 at mean usage versus $25 for the add-on. Its $10,000 extra monthly contribution was entirely a higher-price effect, not evidence that metering was superior. The default now uses $0.0125/request, equal to $25 at 2,000 requests.

## Real calibration, explicitly assumed operating case
IllustrativeCo is fictional: 10,000 eligible accounts, 20% adoption, mean 2,000 requests/month, 2,000 input and 500 output tokens/request, assumed $2/$8 per million tokens, and $10,000 monthly fixed cost. These are not observed customer records or current vendor quotations. Only the 77.68% core gross-margin calibration comes from Salesforce reported financials.

## Same baseline economics
Both policies generate $50,000 monthly revenue, incur $32,000 inference cost and contribute $8,000 after fixed cost. Add-on break-even is $21/account; metered break-even is $0.0105/request. Bundling costs $42,000/month and would require about 541 additional accounts retained for a full year; no such benefit has been observed.

## Uneven usage changes risk allocation
An assumed lognormal usage distribution with log-sigma 1.2 allocates 46.8% of requests to the heaviest 10% of accounts. Their mean usage is 9,350 requests/month. The flat add-on loses allocated contribution above 2,500 requests/account (including $5 allocated fixed cost); its variable-cost-only threshold is 3,125. Approximately 21.6% of accounts exceed the allocated threshold under this assumption.

At the equal price, top-decile mean contribution is $-54.80/account for flat pricing versus $37.08 for metering. Light users cross-subsidize heavy users under flat pricing. Metering preserves positive variable margin because $0.0125 exceeds $0.008 unit cost, but low-usage adopters may still fail to cover allocated fixed cost. Aggregate baseline contribution remains equal.

## Adoption and usage stresses
At unchanged usage, metering breaks even at 11.11% adoption of the eligible base, versus the assumed 20%. If metering reduces adoption by 20% relative, its contribution falls to $4,400/month while the unchanged flat case remains $8,000. If mean usage instead rises 50% with unchanged adoption, flat contribution is −$8,000 and metered contribution is $17,000. The latter bills more as usage rises; it is not an equal-realized-revenue comparison.

`pricing_stress.csv` crosses four assumed usage levels and four relative metered-adoption penalties. Neither price elasticity nor usage suppression is estimated from real customers. Test willingness to pay, bill shock, cost per request and paid adoption before selecting a policy. A capped add-on with separately priced overages is a test hypothesis, not a proven optimum.

## Reproduce
Run `python pricing_case.py`. `usage_risk_cohorts.csv` contains exact conditional means in 100 equally weighted percentile bins; it is an analytical distribution scenario, not synthetic historical customer data. Tail shares use the lognormal closed form. `pricing_case.json` records assumptions and thresholds.
