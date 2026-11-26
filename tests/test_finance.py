from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from planning import bridge, pricing, validate_claims
from model import annual_facts


def test_bridge_reconciles_with_negative_margin_change():
    b = bridge({"revenue": 100, "gross_profit": 80}, {"revenue": 120, "gross_profit": 90})
    assert b["revenue_effect_at_prior_margin"] == pytest.approx(16)
    assert b["margin_effect_at_current_revenue"] == pytest.approx(-6)
    assert b["reconciliation_difference"] == pytest.approx(0)


def test_pricing_token_units_and_zero_revenue():
    rows = pricing(100, 0.5, 1000, 2000, 500, 2, 8, 20, 0.03, 100)
    assert rows[0]["inference_cost"] == pytest.approx(400)
    assert rows[0]["gross_margin"] is None
    assert rows[1]["monthly_revenue"] == 1000
    assert rows[1]["contribution"] == pytest.approx(500)


def test_commentary_rejects_correct_numbers_with_invented_cause():
    with pytest.raises(ValueError):
        validate_claims([{"metric": "growth", "value": 10, "cause": "pricing"}], {"growth": 10})
    with pytest.raises(ValueError):
        validate_claims([{"metric": "growth", "value": 12}], {"growth": 10})
    with pytest.raises(ValueError):
        validate_claims([{"metric": "growth", "value": float("nan")}], {"growth": 10})
    assert validate_claims([{"metric": "growth", "value": 10}], {"growth": 10})


def test_real_data_point_in_time_and_unique_grain():
    root = Path(__file__).resolve().parents[1]
    if not (root / "data/raw/CRM.json").exists():
        pytest.skip("Download real data for integration check")
    rows = annual_facts("CRM", "2020-04-30")
    assert rows and all(r["filed"] <= "2020-04-30" for r in rows)
    keys = [(r["ticker"], r["period_end"], r["metric"]) for r in rows]
    assert len(keys) == len(set(keys))
