"""Distribution conservation, break-even risk and price/adoption separation."""

import json
from pathlib import Path
import numpy as np
import pytest
from pricing_case import risk_analysis, usage_distribution

ROOT = Path(__file__).resolve().parents[1]


def test_equal_price_conserves_aggregate_contribution_with_uneven_usage():
    p = json.loads((ROOT / "inputs/illustrative_case.json").read_text(encoding="utf-8"))["pricing"]
    for sigma in (0, 0.5, 1.2, 2):
        result = risk_analysis(p, sigma)
        assert np.mean(usage_distribution(2000, sigma)) == pytest.approx(2000)
        assert result["baseline_flat_contribution"] == pytest.approx(8000)
        assert result["baseline_metered_contribution"] == pytest.approx(8000)
    risk = risk_analysis(p)
    assert risk["top_decile_usage_share"] == pytest.approx(0.467501659)
    assert risk["top_decile_flat_mean_contribution"] < 0 < risk["top_decile_metered_mean_contribution"]
    assert risk["flat_allocated_contribution_break_even_requests"] == 2500
    assert risk["flat_variable_break_even_requests"] == 3125
    stress = next(
        r
        for r in risk["stress_scenarios"]
        if r["mean_usage_multiplier"] == 1 and r["metered_adoption_penalty"] == 0.2
    )
    assert stress["flat_contribution"] == 8000
    assert stress["metered_contribution"] == pytest.approx(4400)


def test_heavy_usage_stress_and_invalid_distribution():
    p = json.loads((ROOT / "inputs/illustrative_case.json").read_text(encoding="utf-8"))["pricing"]
    r = risk_analysis(p)
    stress = next(
        r
        for r in r["stress_scenarios"]
        if r["mean_usage_multiplier"] == 1.5 and r["metered_adoption_penalty"] == 0
    )
    assert stress["flat_contribution"] == -8000
    assert stress["metered_contribution"] == pytest.approx(17000)
    with pytest.raises(ValueError):
        usage_distribution(2000, -1)
    with pytest.raises(ValueError):
        risk_analysis({**p, "adoption": 0})
