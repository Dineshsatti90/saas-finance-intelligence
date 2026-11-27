"""Public generator, source ties, real formulas and separately labeled assumptions."""

import json
from pathlib import Path

import openpyxl
import pytest

from build_workbook import build

ROOT = Path(__file__).resolve().parents[1]


def test_public_workbook_rebuild_and_cached_calculations(tmp_path):
    output = build(tmp_path / "model.xlsx")
    formulas = openpyxl.load_workbook(output, data_only=False)
    values = openpyxl.load_workbook(output, data_only=True)
    assert len(formulas.sheetnames) == 9
    assert formulas["Forecast"]["E8"].value.startswith("=IF(")
    assert values["Forecast"]["E8"].value == pytest.approx(45_677_500_000)
    assert values["AI Pricing"]["F26"].value == 8000
    assert values["AI Pricing"]["F27"].value == 8000
    assert values["ARR and Staffing"]["E12"].value == 13_500_000
    assert values["ARR and Staffing"]["E24"].value == 5_040_000
    assert "FICTIONAL" in values["ARR and Staffing"]["C5"].value
    assert "NOT A CASH BALANCE FORECAST" in values["Summary"]["C17"].value
    assert len(formulas["Summary"]._charts) == 1
    assert values["Usage Risk"]["D20"].value == pytest.approx(8000)
    assert values["Usage Risk"]["D21"].value == pytest.approx(8000)
    assert values["Usage Risk"]["D15"].value == pytest.approx(0.467501659)
    assert (
        values["Actuals"]["D6"].value
        == json.loads((ROOT / "reports/model_inputs.json").read_text())["actuals"]["revenue"]
    )


def test_blank_operating_template_does_not_invent_zero(tmp_path):
    workbook = openpyxl.load_workbook(build(tmp_path / "blank.xlsx", blank=True), data_only=True)
    assert workbook["ARR and Staffing"]["E7"].value is None
    assert workbook["ARR and Staffing"]["E12"].value == "n.a."
    assert workbook["AI Pricing"]["D25"].value == "n.a."
    assert workbook["Actuals"]["D6"].value > 0
