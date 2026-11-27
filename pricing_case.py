"""Equal-price economics and explicitly assumed customer-usage risk."""

from pathlib import Path
import json
import math
import numpy as np
from scipy.stats import norm
from planning import pricing

ROOT = Path(__file__).resolve().parent


def usage_distribution(mean: float, sigma: float, bins: int = 100) -> np.ndarray:
    """Conditional bin means integrate the lognormal exactly, including both tails."""
    if not math.isfinite(mean) or mean <= 0 or not math.isfinite(sigma) or sigma < 0 or bins < 10:
        raise ValueError("Positive mean, nonnegative finite sigma and at least ten bins required")
    if sigma == 0:
        return np.full(bins, mean)
    edges = norm.ppf(np.linspace(0, 1, bins + 1))
    return mean * bins * np.diff(norm.cdf(edges - sigma))


def risk_analysis(p: dict, sigma: float = 1.2, bins: int = 100) -> dict:
    """Same adoption and volume at baseline; stress changes are scenarios, not forecasts."""
    active = p["customers"] * p["adoption"]
    if active <= 0 or p["requests"] <= 0:
        raise ValueError("Positive adopters and mean usage required for per-account risk analysis")
    unit = (p["input_tokens"] * p["input_rate"] + p["output_tokens"] * p["output_rate"]) / 1e6
    if unit <= 0:
        raise ValueError("Positive variable cost required for usage thresholds")
    equal_price = p["subscription"] / p["requests"]
    fixed_per = p["fixed_cost"] / active
    usage = usage_distribution(p["requests"], sigma, bins)
    flat = p["subscription"] - usage * unit - fixed_per
    metered = usage * (equal_price - unit) - fixed_per
    limit = (p["subscription"] - fixed_per) / unit
    variable_limit = p["subscription"] / unit

    def above(threshold: float) -> float:
        if threshold <= 0:
            return 1.0
        if sigma == 0:
            return float(p["requests"] > threshold)
        return float(norm.sf((math.log(threshold / p["requests"]) + sigma**2 / 2) / sigma))

    top_share = 0.1 if sigma == 0 else float(norm.cdf(sigma - norm.ppf(0.9)))
    rows = []
    for i, (q, f, m) in enumerate(zip(usage, flat, metered, strict=True)):
        rows.append(
            {
                "usage_percentile_bin": i + 1,
                "account_share": 1 / bins,
                "requests_per_account": float(q),
                "flat_contribution_per_account": float(f),
                "metered_contribution_per_account": float(m),
            }
        )
    stress = []
    for multiplier in (0.75, 1.0, 1.25, 1.5):
        for penalty in (0.0, 0.1, 0.2, 0.3):
            mean = p["requests"] * multiplier
            stress.append(
                {
                    "mean_usage_multiplier": multiplier,
                    "metered_adoption_penalty": penalty,
                    "flat_contribution": active * (p["subscription"] - mean * unit) - p["fixed_cost"],
                    "metered_contribution": active * (1 - penalty) * mean * (equal_price - unit)
                    - p["fixed_cost"],
                }
            )
    per_adopter_margin = p["requests"] * (equal_price - unit)
    return {
        "distribution": "assumed lognormal; exact conditional quantile-bin means",
        "log_sigma": sigma,
        "bins": bins,
        "mean_requests": p["requests"],
        "equal_price_per_request": equal_price,
        "inference_cost_per_request": unit,
        "fixed_cost_per_adopter": fixed_per,
        "flat_allocated_contribution_break_even_requests": limit,
        "flat_variable_break_even_requests": variable_limit,
        "share_above_flat_allocated_break_even": above(limit),
        "top_decile_usage_share": top_share,
        "top_decile_mean_requests": p["requests"] * top_share / 0.1,
        "top_decile_flat_mean_contribution": p["subscription"]
        - p["requests"] * top_share / 0.1 * unit
        - fixed_per,
        "top_decile_metered_mean_contribution": p["requests"] * top_share / 0.1 * (equal_price - unit)
        - fixed_per,
        "baseline_flat_contribution": float(flat.mean() * active),
        "baseline_metered_contribution": float(metered.mean() * active),
        "metered_adoption_break_even": p["fixed_cost"] / (p["customers"] * per_adopter_margin)
        if per_adopter_margin > 0
        else None,
        "cohorts": rows,
        "stress_scenarios": stress,
        "limits": "Usage distribution, equal adoption and demand response are assumptions. Allocated fixed cost is not marginal cost. Metering protects variable unit margin only when price exceeds unit cost; it does not guarantee total profitability.",
    }


def calculate(case: dict, gross_margin: float) -> dict:
    p = case["pricing"]
    rows = pricing(**{k: v for k, v in p.items() if k != "core_mrr_per_account"})
    active = p["customers"] * p["adoption"]
    if active <= 0 or p["requests"] <= 0 or p["core_mrr_per_account"] <= 0 or gross_margin <= 0:
        raise ValueError("Positive activity and core margin required for break-even analysis")
    (p["input_tokens"] * p["input_rate"] + p["output_tokens"] * p["output_rate"]) / 1e6
    total = rows[0]["inference_cost"] + p["fixed_cost"]
    retained = total / (p["core_mrr_per_account"] * gross_margin)
    risk = risk_analysis(p, case.get("usage_risk", {}).get("log_sigma", 1.2))
    return {
        "label": case["label"],
        "assumptions": p,
        "results": rows,
        "addon_monthly_break_even": total / active,
        "usage_price_break_even": total / (active * p["requests"]),
        "subscription_request_cap_at_break_even": risk["flat_allocated_contribution_break_even_requests"],
        "bundling_required_retained_accounts_per_year": retained,
        "bundling_required_annual_churn_improvement_pp": retained / p["customers"] * 100,
        "calibration_gross_margin": gross_margin,
        "usage_risk": risk,
        "retention_model": "One full year of core gross profit per retained account; timing, discounting and retention effects are unobserved.",
    }


def run() -> None:
    case = json.loads((ROOT / "inputs/illustrative_case.json").read_text(encoding="utf-8"))
    actual = json.loads((ROOT / "reports/model_inputs.json").read_text())
    margin = (actual["actuals"]["revenue"] - actual["cost_of_revenue"]) / actual["actuals"]["revenue"]
    result = calculate(case, margin)
    risk = result["usage_risk"]
    result["recommendation"] = (
        "Test a capped add-on against metered pricing at an equal baseline price of $0.0125/request. "
        "Both contribute $8,000/month at 2,000 requests and equal adoption. Choose based on heavy-usage risk and measured demand response, not the previous unequal-price comparison."
    )
    (ROOT / "reports/pricing_case.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    import pandas as pd

    pd.DataFrame(risk["cohorts"]).to_csv(ROOT / "reports/usage_risk_cohorts.csv", index=False)
    pd.DataFrame(risk["stress_scenarios"]).to_csv(ROOT / "reports/pricing_stress.csv", index=False)
    memo = f"""# AI pricing: equal-price decision and usage risk

## Recommendation
{result["recommendation"]}

The former $0.015/request example billed $30 at mean usage versus $25 for the add-on. Its $10,000 extra monthly contribution was entirely a higher-price effect, not evidence that metering was superior. The default now uses $0.0125/request, equal to $25 at 2,000 requests.

## Real calibration, explicitly assumed operating case
IllustrativeCo is fictional: 10,000 eligible accounts, 20% adoption, mean 2,000 requests/month, 2,000 input and 500 output tokens/request, assumed $2/$8 per million tokens, and $10,000 monthly fixed cost. These are not observed customer records or current vendor quotations. Only the {margin:.2%} core gross-margin calibration comes from Salesforce reported financials.

## Same baseline economics
Both policies generate $50,000 monthly revenue, incur $32,000 inference cost and contribute $8,000 after fixed cost. Add-on break-even is $21/account; metered break-even is $0.0105/request. Bundling costs $42,000/month and would require about {result["bundling_required_retained_accounts_per_year"]:.0f} additional accounts retained for a full year; no such benefit has been observed.

## Uneven usage changes risk allocation
An assumed lognormal usage distribution with log-sigma 1.2 allocates {risk["top_decile_usage_share"]:.1%} of requests to the heaviest 10% of accounts. Their mean usage is {risk["top_decile_mean_requests"]:,.0f} requests/month. The flat add-on loses allocated contribution above {risk["flat_allocated_contribution_break_even_requests"]:,.0f} requests/account (including $5 allocated fixed cost); its variable-cost-only threshold is {risk["flat_variable_break_even_requests"]:,.0f}. Approximately {risk["share_above_flat_allocated_break_even"]:.1%} of accounts exceed the allocated threshold under this assumption.

At the equal price, top-decile mean contribution is ${risk["top_decile_flat_mean_contribution"]:.2f}/account for flat pricing versus ${risk["top_decile_metered_mean_contribution"]:.2f} for metering. Light users cross-subsidize heavy users under flat pricing. Metering preserves positive variable margin because $0.0125 exceeds $0.008 unit cost, but low-usage adopters may still fail to cover allocated fixed cost. Aggregate baseline contribution remains equal.

## Adoption and usage stresses
At unchanged usage, metering breaks even at {risk["metered_adoption_break_even"]:.2%} adoption of the eligible base, versus the assumed 20%. If metering reduces adoption by 20% relative, its contribution falls to $4,400/month while the unchanged flat case remains $8,000. If mean usage instead rises 50% with unchanged adoption, flat contribution is −$8,000 and metered contribution is $17,000. The latter bills more as usage rises; it is not an equal-realized-revenue comparison.

`pricing_stress.csv` crosses four assumed usage levels and four relative metered-adoption penalties. Neither price elasticity nor usage suppression is estimated from real customers. Test willingness to pay, bill shock, cost per request and paid adoption before selecting a policy. A capped add-on with separately priced overages is a test hypothesis, not a proven optimum.

## Reproduce
Run `python pricing_case.py`. `usage_risk_cohorts.csv` contains exact conditional means in 100 equally weighted percentile bins; it is an analytical distribution scenario, not synthetic historical customer data. Tail shares use the lognormal closed form. `pricing_case.json` records assumptions and thresholds.
"""
    (ROOT / "reports/pricing_decision.md").write_text(memo, encoding="utf-8")
    print(json.dumps({k: v for k, v in risk.items() if k not in ("cohorts", "stress_scenarios")}, indent=2))


if __name__ == "__main__":
    run()
