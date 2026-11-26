import json
from pathlib import Path

import pandas as pd
import pytest

from planning import bridge, pricing, scenario
from pricing_case import calculate

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value", [-1, float("inf"), float("nan")])
def test_invalid_token_rates_are_rejected(value):
    with pytest.raises(ValueError):
        pricing(100, 0.2, 1000, 2000, 500, value, 8, 25, 0.015, 100)


def test_zero_adoption_preserves_fixed_cost_and_undefined_margin():
    rows = pricing(100, 0, 1000, 2000, 500, 2, 8, 25, 0.015, 100)
    assert all(row["contribution"] == -100 for row in rows)
    assert all(row["gross_margin"] is None for row in rows)


def test_driver_training_labels_are_available_before_origin():
    rows = pd.read_csv(ROOT / "reports/driver_backtest.csv")
    assert (rows.latest_training_label <= rows.origin).all()
    assert (rows.training_cases >= 12).all()
    targets = rows.groupby("method")[["ticker", "target_period_end"]].apply(
        lambda x: set(zip(x.ticker, x.target_period_end))
    )
    assert len(targets) == 3 and targets.iloc[0] == targets.iloc[1] == targets.iloc[2]


def test_illustrative_break_even_and_scenario_cash_conversion():
    case = json.loads((ROOT / "inputs/illustrative_case.json").read_text(encoding="utf-8"))
    result = calculate(case, 0.75)
    assert result["addon_monthly_break_even"] == 21
    assert result["usage_price_break_even"] == pytest.approx(0.0105)
    inputs = json.loads((ROOT / "reports/model_inputs.json").read_text())
    base = scenario(inputs, "base")
    down = scenario(inputs, "downside")
    assert down["operating_cash_flow"] / down["revenue"] == pytest.approx(
        base["operating_cash_flow"] / base["revenue"] - 0.03
    )


@pytest.mark.parametrize(
    "prior,current",
    [
        (dict(revenue=100, gross_profit=80), dict(revenue=120, gross_profit=70)),
        (dict(revenue=100, gross_profit=-10), dict(revenue=80, gross_profit=5)),
    ],
)
def test_bridge_with_declining_profit_or_negative_margin(prior, current):
    result = bridge(prior, current)
    assert abs(result["reconciliation_difference"]) < 1e-9
