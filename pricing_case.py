"""A concrete decision from a labeled operating scenario, not invented company actuals."""

from pathlib import Path
import json
from planning import pricing

ROOT = Path(__file__).resolve().parent


def calculate(case: dict, gross_margin: float) -> dict:
    p = case["pricing"]
    rows = pricing(**{k: v for k, v in p.items() if k != "core_mrr_per_account"})
    active = p["customers"] * p["adoption"]
    inference_per_request = (
        p["input_tokens"] * p["input_rate"] + p["output_tokens"] * p["output_rate"]
    ) / 1e6
    monthly_total = rows[0]["inference_cost"] + p["fixed_cost"]
    addon_break_even = monthly_total / active
    lost_monthly_contribution = -rows[0]["contribution"]
    annual_core_gross_profit = p["core_mrr_per_account"] * 12 * gross_margin
    retained_accounts = lost_monthly_contribution * 12 / annual_core_gross_profit
    return {
        "label": case["label"],
        "assumptions": p,
        "results": rows,
        "addon_monthly_break_even": addon_break_even,
        "usage_price_break_even": monthly_total / (active * p["requests"]),
        "subscription_request_cap_at_break_even": (p["subscription"] - p["fixed_cost"] / active)
        / inference_per_request,
        "bundling_required_retained_accounts_per_year": retained_accounts,
        "bundling_required_annual_churn_improvement_pp": retained_accounts / p["customers"] * 100,
        "calibration_gross_margin": gross_margin,
        "retention_model": "One full year of core gross profit per retained account; ignores timing, discounting and retention uncertainty.",
    }


def run() -> None:
    case = json.loads((ROOT / "inputs/illustrative_case.json").read_text(encoding="utf-8"))
    actual = json.loads((ROOT / "reports/model_inputs.json").read_text())
    margin = (actual["actuals"]["revenue"] - actual["cost_of_revenue"]) / actual["actuals"]["revenue"]
    result = calculate(case, margin)
    result["recommendation"] = (
        "In this illustrative case, prefer metered pricing at $0.015/request: it contributes $18,000/month versus $8,000 for the $25 add-on. If choosing the add-on, cap included requests at 2,500 per adopting account to avoid negative contribution under unchanged costs."
    )
    (ROOT / "reports/pricing_case.json").write_text(json.dumps(result, indent=2))
    memo = f"""# AI feature pricing: illustrative investment decision

## Recommendation
{result["recommendation"]}

## Assumptions and calibration
This is **IllustrativeCo, a fictional operating case**, not Salesforce customer/ARR/AI-cost data. It assumes 10,000 eligible accounts, 20% adoption, 2,000 requests per adopting account each month, 2,000 input/500 output tokens per request, $2/$8 per million input/output tokens, and $10,000 incremental fixed cost per month. Token rates are scenario inputs, not current provider quotations. Core MRR is assumed $100/account; the reported Salesforce gross margin ({margin:.2%}) calibrates the simplified core retention calculation.

## Calculated economics
At these assumptions inference costs $32,000/month. The subscription break-even price is ${result["addon_monthly_break_even"]:.2f}/adopting account/month. Metered break-even is ${result["usage_price_break_even"]:.4f}/request. $25 subscription revenue contributes $8,000/month after incremental fixed cost; $0.015/request contributes $18,000/month. Bundling costs $42,000/month without direct feature revenue.

Bundling would need approximately {result["bundling_required_retained_accounts_per_year"]:.0f} additional accounts retained for a full year, or {result["bundling_required_annual_churn_improvement_pp"]:.2f} percentage points of annual churn improvement in the entire 10,000-account base, to cover that cost under the simplified retention model. No such retention benefit has been observed.

## Decision conditions
Use metered pricing as the initial test hypothesis. Revisit it if demand elasticity or adoption differs across pricing options, or if support, safety, hosting, payment fees, taxes or token-mix costs change. Run an instrumented pricing test before approving an investment based on these assumptions. See `pricing_case.json` and `inputs/illustrative_case.json` for the full calculation trail.
"""
    (ROOT / "reports/pricing_decision.md").write_text(memo, encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
