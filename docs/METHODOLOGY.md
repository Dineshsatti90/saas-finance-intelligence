# Forecast and planning methodology

## Annual financial normalization

Only 10-K observations are eligible. Flow metrics require a 300–380 day reporting duration and USD units; cash uses instant observations separately. For a metric/period, choose the latest filing available at the requested cutoff, then resolve tag preference deterministically. This handles comparative reporting vintages without summing duplicate reported values. Mappings remain explicit rather than guessing custom tags.

The annual panel is a selected, comparable analytical subset of a much larger source population. Missing supported values stay missing. Tag availability and accounting changes mean the panel requires review before adding new peers or using additional ratios.

## Historical forecasting

At each origin, identify the original publication of the preceding annual revenue and reconstruct annual history using only facts filed by that date. Require three consecutive prior annual periods and a consecutive next annual target. Compare:

1. **Flat revenue:** last available annual revenue.
2. **Trailing growth:** last annual revenue multiplied by one plus the mean of the two preceding observed annual growth rates, bounded to −50% through +100%.

Both methods evaluate the same 58 reference targets. The target is the restated annual actual available at the analysis cutoff. This uses revised outcomes for scoring while keeping predictors point-in-time. WAPE and MAPE are reported alongside every individual forecast/error. Eight peers and annual observations are a small, selected panel; the results do not establish production monthly forecasting performance or superiority across other businesses.

## Gross-profit bridge

Let revenue be R and gross margin be M. The bridge is:

`change in gross profit = (R_current − R_prior) × M_prior + R_current × (M_current − M_prior)`.

The components are labeled revenue effect at prior margin and margin effect at current revenue. They reconcile arithmetically. They are not identified price/volume/product-mix causes.

## Forward financial model

Revenue grows from reported Salesforce annual revenue using editable illustrative rates. Cost of revenue uses an editable revenue ratio; operating expenses grow from the reported residual expense base. OCF and capex use explicit cash-conversion/intensity assumptions.

The workbook has one active case selector and one forward build. All historical actuals stay unchanged when a case changes. Its cash schedule adds projected FCF to opening cash **before** financing, acquisitions, investment trading, repurchases and FX. It is not a three-statement balance-sheet forecast or a liquidity forecast covering all cash flows.

ARR and staffing are optional operating-input schedules. Missing inputs yield `n.a.` rather than invented actuals or a plausible zero. The average ARR run-rate proxy is not a revenue-recognition schedule. Staffing cost assumes hires/exits are spread evenly; no monthly payroll proration is claimed.

## AI feature economics

`inference cost = adopting accounts × requests per account × (input tokens × input rate + output tokens × output rate) / 1,000,000`.

All prices, adoption and usage are user-entered assumptions, not disclosed Salesforce operating metrics or current provider quotations. Bundled, subscription add-on and usage-based policies share the same assumed usage/cost base. Retention benefits, demand elasticity and cross-sell effects are not estimated. Bundling has no incremental feature revenue in this calculator, so feature gross margin is undefined.

## AI reporting boundary

The optional model selects calculated observations from a financial bridge. A verifier checks metric keys, finite numeric values and numerical agreement before a deterministic renderer attaches citations. Free-form causes are rejected. The recorded local Qwen run passed this contract on ten disclosed historical cases. This is not an assessment of a complete board narrative; relevance and completeness remain human review tasks. See `AI_EVALUATION.md` and the saved raw claims.

## Additional driver-based benchmark

`forecast_study.py` compares all three models on the same 40 targets. Features are the last two annual growth rates, operating margin, OCF/revenue and log revenue. StandardScaler and Ridge(alpha=10) fit only earlier cases whose first-published target revenue was public at the prediction origin. At least 12 training cases are required. The penalty is fixed before this comparison, not selected on its test errors. Target scoring uses cutoff-restated actuals. Point-in-time source vintage and training-label availability are tested explicitly.

## Populated operating case

The workbook includes fictional IllustrativeCo inputs in `inputs/illustrative_case.json`, separate from the real Salesforce build. It assumes 10,000 accounts, $100 core MRR, explicit ARR components/staffing and AI prices/usage/costs. Core gross margin is calibrated to a reported ratio; customer economics remain assumptions. `build_workbook.py --blank` generates a separate blank operating-input template without duplicating scenario builds in the main workbook.
