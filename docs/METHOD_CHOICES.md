# Explain the financial choices

**Why equal effective pricing?** $0.015 times 2,000 requests bills $30, whereas the flat add-on bills $25. Setting metering to $0.0125 removes that baseline price advantage, so the remaining comparison concerns risk allocation and demand response.

**Why lognormal usage?** It is an explicitly assumed right-skewed distribution for stress-testing a heavy tail, not an estimated customer behavior model. Exact conditional quantile-bin means conserve aggregate requests, while closed-form tail shares make the assumptions inspectable and editable.

**Why distinguish marginal and allocated losses?** Variable inference cost is $0.008/request, while allocating fixed cost adds $5 per baseline adopter. The flat variable-cost-only threshold is 3,125 requests, versus 2,500 including allocated fixed cost; only the former is a marginal unit-economics threshold.

**Why ridge alpha 10?** A fixed penalty regularizes a small annual peer panel with correlated growth and margin predictors. It was chosen before the benchmark, not tuned on reported test outcomes; 3.99% WAPE is evidence for this selected panel, not universal superiority or monthly forecasting accuracy.

**Why point-in-time labels?** A forecast origin cannot use filings published afterward. Feature vintages and training target availability are limited to that date; evaluation uses later restated outcomes and discloses that distinction.

**Why a finance AI refusal test?** Matching source keys and numbers cannot show that an answer addresses a question or is appropriate. The harder test includes unsupported budgets, causal claims and malicious instructions; its 70% aggregate pass rate and refusal failures are more informative than the original easy 10/10 contract.
