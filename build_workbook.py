"""Rebuild the complete planning workbook using public XlsxWriter only.

Formula caches make the exported workbook reviewable before Excel recalculates.
The financial and operating cases remain separate and clearly identified.
"""

from pathlib import Path
import argparse
import json
from typing import Any

import xlsxwriter

ROOT = Path(__file__).resolve().parent


def build(output: Path | None = None, *, blank: bool = False) -> Path:
    inputs = json.loads((ROOT / "reports/model_inputs.json").read_text())
    case = json.loads((ROOT / "inputs/illustrative_case.json").read_text(encoding="utf-8"))
    pricing = json.loads((ROOT / "reports/pricing_case.json").read_text())
    output = output or ROOT / "outputs/saas-finance/saas_financial_planning.xlsx"
    output.parent.mkdir(parents=True, exist_ok=True)
    book = xlsxwriter.Workbook(output, {"use_future_functions": True})
    book.set_properties(
        {
            "title": "SaaS financial planning",
            "subject": "Reported financials and illustrative AI pricing",
            "author": "Dineshsatti90",
            "comments": "Regenerate with python build_workbook.py. Sources and assumptions are separate.",
        }
    )
    book.set_calc_mode("auto")
    base = {"font_name": "Arial", "font_size": 10, "font_color": "#172033", "valign": "vcenter"}
    number = '#,##0.0,,"m";(#,##0.0,,"m");"–"'
    styles = {
        "text": book.add_format(base),
        "title": book.add_format({**base, "font_size": 16, "bold": True}),
        "header": book.add_format(
            {**base, "bg_color": "#243B5A", "font_color": "white", "bold": True, "align": "center"}
        ),
        "money": book.add_format({**base, "num_format": number}),
        "input": book.add_format(
            {**base, "font_color": "#2457BC", "bg_color": "#FFF0C2", "num_format": "#,##0.00"}
        ),
        "input_pct": book.add_format(
            {**base, "font_color": "#2457BC", "bg_color": "#FFF0C2", "num_format": "0.0%"}
        ),
        "input_money": book.add_format({**base, "font_color": "#2457BC", "num_format": number}),
        "input_millions": book.add_format(
            {**base, "font_color": "#2457BC", "bg_color": "#FFF0C2", "num_format": number}
        ),
        "input_rate": book.add_format(
            {**base, "font_color": "#2457BC", "bg_color": "#FFF0C2", "num_format": "0.0000"}
        ),
        "rate": book.add_format({**base, "num_format": "0.0000"}),
        "link": book.add_format({**base, "font_color": "#167347", "num_format": number}),
        "pct": book.add_format({**base, "num_format": "0.0%", "italic": True, "align": "right"}),
        "whole": book.add_format({**base, "num_format": '#,##0;(#,##0);"–"'}),
        "decimal": book.add_format({**base, "num_format": "0.00"}),
        "warning": book.add_format(
            {**base, "bg_color": "#FFF0C2", "font_color": "#8A3900", "text_wrap": True, "bold": True}
        ),
        "note": book.add_format({**base, "font_color": "#526479", "italic": True, "text_wrap": True}),
        "case": book.add_format({**base, "font_color": "#167347", "bold": True}),
    }
    names = [
        "Summary",
        "Assumptions",
        "Forecast",
        "AI Pricing",
        "ARR and Staffing",
        "Actuals",
        "Checks",
        "Usage Risk",
    ]
    sheets = {name: book.add_worksheet(name) for name in names}
    cached: dict[tuple[str, str], Any] = {}

    def value(sheet: str, cell: str, item: Any, style: str = "text") -> None:
        sheets[sheet].write(cell, item, styles[style])
        cached[(sheet, cell)] = item

    def formula(sheet: str, cell: str, expression: str, result: Any, style: str = "money") -> None:
        sheets[sheet].write_formula(cell, expression, styles[style], result)
        cached[(sheet, cell)] = result

    def row(sheet: str, index: int, label: str) -> None:
        value(sheet, f"C{index}", label)

    def band(sheet: str, index: int, labels: list[str]) -> None:
        sheets[sheet].write_row(index - 1, 2, labels, styles["header"])
        sheets[sheet].set_row(index - 1, 27)

    for name, sheet in sheets.items():
        sheet.hide_gridlines(2)
        sheet.set_column("A:B", 3)
        sheet.set_column("C:C", 44)
        sheet.set_column("D:G", 19)
        sheet.set_default_row(22)
        sheet.set_landscape()
        sheet.fit_to_pages(1, 1)
        sheet.set_paper(9)
        sheet.set_margins(0.3, 0.3, 0.4, 0.4)
        sheet.print_area("C2:G34")
        value(name, "C2", "SaaS financial planning" if name == "Summary" else name, "title")
        if name not in ("Assumptions", "Actuals"):
            row(name, 4, "Active financial case")
            formula(name, "D4", "=Assumptions!E4", "Base", "case")
    sheets["Summary"].set_tab_color("#243B5A")
    sheets["Assumptions"].set_tab_color("#52729A")
    sheets["Actuals"].set_tab_color("#E8D5BA")

    # Original reported financials, with one source row per input metric.
    a = inputs["actuals"]
    raw_metrics = [
        ("Revenue", "revenue"),
        ("Cost of revenue", "cost_of_revenue"),
        ("Gross profit", "gross_profit"),
        ("Operating income", "operating_income"),
        ("Operating cash flow", "operating_cash_flow"),
        ("Capital expenditure", "capex"),
        ("Cash and equivalents", "cash"),
        ("R&D", "research_development"),
        ("Sales and marketing", "sales_marketing"),
        ("General and administrative", "general_admin"),
    ]
    value("Actuals", "C4", f"Salesforce | year ended {inputs['period_end']} | USD millions")
    band("Actuals", 5, ["Reported metric", "USD millions", "XBRL tag", "Filed", "Source filing"])
    sheets["Actuals"].set_column("E:E", 65)
    sheets["Actuals"].set_column("F:F", 15)
    sheets["Actuals"].set_column("G:G", 115)
    sheets["Actuals"].freeze_panes(5, 3)
    for r, (label, key) in enumerate(raw_metrics, 6):
        row("Actuals", r, label)
        value("Actuals", f"D{r}", a.get(key), "input_money")
        source = inputs["sources"].get(key, {})
        value("Actuals", f"E{r}", source.get("tag", "Unavailable"))
        value("Actuals", f"F{r}", source.get("filed", ""))
        if source.get("url"):
            sheets["Actuals"].write_url(f"G{r}", source["url"], string=source["url"])
    value("Actuals", "C18", f"Financial analysis cutoff: {inputs['asof']}")

    # One active assumption row per driver, one financial build.
    value("Assumptions", "C4", "Case selector: 1 Base, 2 Downside")
    value("Assumptions", "D4", 1, "input")
    sheets["Assumptions"].data_validation(
        "D4", {"validate": "integer", "criteria": "between", "minimum": 1, "maximum": 2}
    )
    formula("Assumptions", "E4", '=CHOOSE(D4,"Base","Downside")', "Base", "case")
    value("Assumptions", "C5", "Illustrative forward rates; not guidance.", "note")
    year = int(inputs["period_end"][:4])
    headers = [f"{year + i}-01-31 F" for i in (1, 2, 3)]
    band("Assumptions", 6, ["Driver", "", *headers])
    p = inputs["planning_assumptions"]
    drivers = [
        (8, "Revenue growth", p["base_growth"], p["downside_growth"]),
        (12, "Cost of revenue / revenue", p["base_cogs_ratio"], p["downside_cogs_ratio"]),
        (16, "Operating expense growth", p["base_opex_growth"], p["downside_opex_growth"]),
        (
            20,
            "Operating cash flow / revenue",
            a["operating_cash_flow"] / a["revenue"],
            a["operating_cash_flow"] / a["revenue"] - 0.03,
        ),
        (24, "Capital expenditure / revenue", a["capex"] / a["revenue"], a["capex"] / a["revenue"]),
    ]
    for r, label, base_rate, down_rate in drivers:
        row("Assumptions", r, label + " — active")
        row("Assumptions", r + 1, "Base")
        row("Assumptions", r + 2, "Downside")
        for column in "EFG":
            value("Assumptions", f"{column}{r + 1}", base_rate, "input_pct")
            value("Assumptions", f"{column}{r + 2}", down_rate, "input_pct")
            sheets["Assumptions"].data_validation(
                f"{column}{r + 1}:{column}{r + 2}",
                {
                    "validate": "decimal",
                    "criteria": "between",
                    "minimum": -0.99 if r in (8, 16) else 0,
                    "maximum": 2 if r in (8, 16) else 1,
                },
            )
            formula(
                "Assumptions",
                f"{column}{r}",
                f'=IF(CHOOSE($D$4,{column}{r + 1},{column}{r + 2})="","n.a.",CHOOSE($D$4,{column}{r + 1},{column}{r + 2}))',
                base_rate,
                "pct",
            )

    row_labels = {
        8: "Revenue",
        9: "Revenue growth",
        10: "Cost of revenue / revenue",
        11: "Cost of revenue",
        12: "Gross profit",
        13: "Gross margin",
        15: "Opening operating expense base",
        16: "Operating expense growth",
        17: "Operating expenses",
        18: "Operating income",
        20: "Operating cash flow / revenue",
        21: "Operating cash flow",
        22: "Capital expenditure / revenue",
        23: "Capital expenditure",
        24: "Free cash flow",
        26: "Opening cash and equivalents",
        27: "Accumulated cash before excluded flows",
    }
    band("Forecast", 6, ["USD millions", inputs["period_end"] + " A", *headers])
    for r, label in row_labels.items():
        row("Forecast", r, label)
    history = {
        8: (a["revenue"], "Actuals!D6"),
        10: (inputs["cost_of_revenue"] / a["revenue"], "Actuals!D7/Actuals!D6"),
        11: (inputs["cost_of_revenue"], "Actuals!D7"),
        12: (a["gross_profit"], "Actuals!D8"),
        13: (a["gross_profit"] / a["revenue"], "D12/D8"),
        17: (a["revenue"] - inputs["cost_of_revenue"] - a["operating_income"], "D8-D11-D18"),
        18: (a["operating_income"], "Actuals!D9"),
        20: (a["operating_cash_flow"] / a["revenue"], "Actuals!D10/Actuals!D6"),
        21: (a["operating_cash_flow"], "Actuals!D10"),
        22: (a["capex"] / a["revenue"], "Actuals!D11/Actuals!D6"),
        23: (a["capex"], "Actuals!D11"),
        24: (a["operating_cash_flow"] - a["capex"], "D21-D23"),
        27: (a["cash"], "Actuals!D12"),
    }
    for r, (result, expression) in history.items():
        formula(
            "Forecast",
            f"D{r}",
            "=" + expression,
            result,
            "pct" if r in (10, 13, 20, 22) else "link" if "!" in expression else "money",
        )
    from planning import scenario

    annual = []
    previous = {r: value[0] for r, value in history.items()}
    for i, column in enumerate("EFG"):
        prev = "DEF"[i]
        revenue = previous[8] * (1 + p["base_growth"])
        cost = revenue * p["base_cogs_ratio"]
        opex = previous[17] * (1 + p["base_opex_growth"])
        ocf = revenue * a["operating_cash_flow"] / a["revenue"]
        capex = revenue * a["capex"] / a["revenue"]
        current = {
            8: revenue,
            9: p["base_growth"],
            10: p["base_cogs_ratio"],
            11: cost,
            12: revenue - cost,
            13: 1 - cost / revenue,
            15: previous[17],
            16: p["base_opex_growth"],
            17: opex,
            18: revenue - cost - opex,
            20: a["operating_cash_flow"] / a["revenue"],
            21: ocf,
            22: a["capex"] / a["revenue"],
            23: capex,
            24: ocf - capex,
            26: previous[27],
            27: previous[27] + ocf - capex,
        }
        expressions = {
            9: f"Assumptions!{column}8",
            10: f"Assumptions!{column}12",
            16: f"Assumptions!{column}16",
            20: f"Assumptions!{column}20",
            22: f"Assumptions!{column}24",
            15: f"{prev}17",
            26: f"{prev}27",
        }
        operations = {
            8: f"{prev}8*(1+{column}9)",
            11: f"{column}8*{column}10",
            12: f"{column}8-{column}11",
            13: f"{column}12/{column}8",
            17: f"{column}15*(1+{column}16)",
            18: f"{column}12-{column}17",
            21: f"{column}8*{column}20",
            23: f"{column}8*{column}22",
            24: f"{column}21-{column}23",
            27: f"{column}26+{column}24",
        }
        required = {
            8: [f"{prev}8", f"{column}9"],
            11: [f"{column}8", f"{column}10"],
            12: [f"{column}8", f"{column}11"],
            13: [f"{column}12", f"{column}8"],
            17: [f"{column}15", f"{column}16"],
            18: [f"{column}12", f"{column}17"],
            21: [f"{column}8", f"{column}20"],
            23: [f"{column}8", f"{column}22"],
            24: [f"{column}21", f"{column}23"],
            27: [f"{column}26", f"{column}24"],
        }
        for r, expression in operations.items():
            guard = ",".join(f"ISNUMBER({cell})" for cell in required[r])
            expressions[r] = f'IF(AND({guard}),{expression},"n.a.")'
        for r, result in current.items():
            formula(
                "Forecast",
                f"{column}{r}",
                "=" + expressions[r],
                result,
                "pct" if r in (9, 10, 13, 16, 20, 22) else "money",
            )
        annual.append(current)
        previous = current
    assert abs(annual[0][8] - scenario(inputs)["revenue"]) < 0.01
    sheets["Forecast"].merge_range(
        "C30:G32",
        "NOT A CASH BALANCE FORECAST. Accumulation excludes financing, acquisitions, investment trading, repurchases and FX. Read as a limited cash-generation scenario only.",
        styles["warning"],
    )
    sheets["Forecast"].set_row(29, 26)

    # Populated fictional operating schedule, separate from Salesforce financials.
    operating = "ARR and Staffing"
    value(operating, "C5", "IllustrativeCo | FICTIONAL operating assumptions", "warning")
    band(operating, 6, ["USD millions / FTE", "", *headers])
    arr_labels = {
        7: "Opening ARR",
        8: "New ARR",
        9: "Expansion ARR",
        10: "Contraction ARR",
        11: "Churn ARR",
        12: "Closing ARR",
        14: "Average ARR run-rate proxy",
        19: "Opening paid FTE",
        20: "Hires, FTE",
        21: "Exits, FTE",
        22: "Closing paid FTE",
        23: "Annual loaded cost / FTE (USD)",
        24: "Payroll expense proxy",
    }
    for r, label in arr_labels.items():
        row(operating, r, label)
    prior_arr = case["arr"]["opening"]
    prior_fte = case["staffing"]["opening_fte"]
    for i, column in enumerate("EFG"):
        prev = "DEF"[i]
        for r, key in [(8, "new"), (9, "expansion"), (10, "contraction"), (11, "churn")]:
            value(operating, f"{column}{r}", None if blank else case["arr"][key][i], "input_millions")
        for r, key in [(20, "hires"), (21, "exits"), (23, "loaded_annual_cost")]:
            value(operating, f"{column}{r}", None if blank else case["staffing"][key][i], "input")
        if i == 0:
            value(operating, f"{column}7", None if blank else prior_arr, "input_millions")
            value(operating, f"{column}19", None if blank else prior_fte, "input")
        else:
            formula(
                operating,
                f"{column}7",
                f'=IF(ISNUMBER({prev}12),{prev}12,"n.a.")',
                "n.a." if blank else prior_arr,
            )
            formula(
                operating,
                f"{column}19",
                f'=IF(ISNUMBER({prev}22),{prev}22,"n.a.")',
                "n.a." if blank else prior_fte,
                "whole",
            )
        closing = (
            prior_arr
            + case["arr"]["new"][i]
            + case["arr"]["expansion"][i]
            - case["arr"]["contraction"][i]
            - case["arr"]["churn"][i]
        )
        closing_fte = prior_fte + case["staffing"]["hires"][i] - case["staffing"]["exits"][i]
        formula(
            operating,
            f"{column}12",
            f'=IF(COUNT({column}7:{column}11)=5,{column}7+{column}8+{column}9-{column}10-{column}11,"n.a.")',
            "n.a." if blank else closing,
        )
        formula(
            operating,
            f"{column}14",
            f'=IF(AND(ISNUMBER({column}7),ISNUMBER({column}12)),({column}7+{column}12)/2,"n.a.")',
            "n.a." if blank else (prior_arr + closing) / 2,
        )
        formula(
            operating,
            f"{column}22",
            f'=IF(COUNT({column}19:{column}21)=3,{column}19+{column}20-{column}21,"n.a.")',
            "n.a." if blank else closing_fte,
            "whole",
        )
        formula(
            operating,
            f"{column}24",
            f'=IF(AND(ISNUMBER({column}19),ISNUMBER({column}22),ISNUMBER({column}23)),({column}19+{column}22)/2*{column}23,"n.a.")',
            "n.a." if blank else (prior_fte + closing_fte) / 2 * case["staffing"]["loaded_annual_cost"][i],
        )
        prior_arr = closing
        prior_fte = closing_fte
    sheets[operating].merge_range(
        "C28:G30",
        "IllustrativeCo values are fictional. These schedules do not overwrite or reconcile to Salesforce actuals. ARR run-rate averages are not a GAAP revenue-recognition schedule.",
        styles["warning"],
    )

    # One cost build reused across all three pricing options.
    pricing_labels = {
        7: ("Eligible accounts", "customers"),
        8: ("Adoption", "adoption"),
        9: ("Requests / adopting account / month", "requests"),
        10: ("Input tokens / request", "input_tokens"),
        11: ("Output tokens / request", "output_tokens"),
        12: ("Input USD / million tokens", "input_rate"),
        13: ("Output USD / million tokens", "output_rate"),
        14: ("Add-on USD / account / month", "subscription"),
        15: ("Usage USD / request", "usage_price"),
        16: ("Incremental fixed monthly cost", "fixed_cost"),
    }
    value("AI Pricing", "C5", "IllustrativeCo | scenario rates, not provider quotations", "warning")
    for r, (label, key) in pricing_labels.items():
        row("AI Pricing", r, label)
        value(
            "AI Pricing",
            f"D{r}",
            None if blank else case["pricing"][key],
            "input_pct" if r == 8 else "input_rate" if r in (12, 13, 14, 15) else "input",
        )
    sheets["AI Pricing"].data_validation("D7:D16", {"validate": "decimal", "criteria": ">=", "value": 0})
    sheets["AI Pricing"].data_validation(
        "D8", {"validate": "decimal", "criteria": "between", "minimum": 0, "maximum": 1}
    )
    active = case["pricing"]["customers"] * case["pricing"]["adoption"]
    requests = active * case["pricing"]["requests"]
    unit = (
        case["pricing"]["input_tokens"] * case["pricing"]["input_rate"]
        + case["pricing"]["output_tokens"] * case["pricing"]["output_rate"]
    ) / 1e6
    for r, label, expression, result in [
        (18, "Adopting accounts", '=IF(COUNT(D7:D8)=2,D7*D8,"n.a.")', active),
        (19, "Total monthly requests", '=IF(AND(ISNUMBER(D18),ISNUMBER(D9)),D18*D9,"n.a.")', requests),
        (20, "Inference cost / request", '=IF(COUNT(D10:D13)=4,(D10*D12+D11*D13)/1000000,"n.a.")', unit),
        (
            21,
            "Monthly inference cost",
            '=IF(AND(ISNUMBER(D19),ISNUMBER(D20)),D19*D20,"n.a.")',
            requests * unit,
        ),
    ]:
        row("AI Pricing", r, label)
        formula(
            "AI Pricing", f"D{r}", expression, "n.a." if blank else result, "rate" if r == 20 else "whole"
        )
    band(
        "AI Pricing",
        24,
        ["Pricing policy", "Revenue USD", "Inference USD", "Contribution USD", "Gross margin"],
    )
    for r, result in enumerate(pricing["results"], 25):
        row("AI Pricing", r, result["strategy"])
        expression = "0" if r == 25 else "$D$18*$D$14" if r == 26 else "$D$19*$D$15"
        formula(
            "AI Pricing",
            f"D{r}",
            f'=IF(COUNT($D$7:$D$16)=10,{expression},"n.a.")',
            "n.a." if blank else result["monthly_revenue"],
            "whole",
        )
        formula("AI Pricing", f"E{r}", "=D21", "n.a." if blank else result["inference_cost"], "whole")
        formula(
            "AI Pricing",
            f"F{r}",
            f'=IF(AND(ISNUMBER(D{r}),ISNUMBER(E{r}),ISNUMBER($D$16)),D{r}-E{r}-$D$16,"n.a.")',
            "n.a." if blank else result["contribution"],
            "whole",
        )
        formula(
            "AI Pricing",
            f"G{r}",
            f'=IF(ISNUMBER(D{r}),IF(D{r}=0,"n.a.",(D{r}-E{r})/D{r}),"n.a.")',
            "n.a." if blank or result["gross_margin"] is None else result["gross_margin"],
            "pct",
        )
    row("AI Pricing", 29, "Add-on monthly break-even")
    formula(
        "AI Pricing",
        "D29",
        '=IF(AND(ISNUMBER(D18),ISNUMBER(D21),ISNUMBER(D16)),IF(D18=0,"n.a.",(D21+D16)/D18),"n.a.")',
        "n.a." if blank else pricing["addon_monthly_break_even"],
        "decimal",
    )
    sheets["AI Pricing"].merge_range(
        "C31:G33",
        "Equal baseline price: $0.0125/request = $25 at 2,000 requests. Both policies contribute $8k/month. See Usage Risk for tail exposure and adoption stresses; demand response is unobserved.",
        styles["note"],
    )

    # Equal-price risk: all formulas reference the editable AI Pricing inputs.
    risk = pricing["usage_risk"]
    value("Usage Risk", "C5", "FICTIONAL lognormal usage; not customer observations", "warning")
    risk_rows = [
        (7, "Assumed log-usage sigma", None, risk["log_sigma"], "input"),
        (8, "Mean requests / adopter", "='AI Pricing'!D9", risk["mean_requests"], "whole"),
        (9, "Adopting accounts", "='AI Pricing'!D18", active, "whole"),
        (10, "Variable cost / request, USD", "='AI Pricing'!D20", unit, "rate"),
        (11, "Flat add-on price, USD", "='AI Pricing'!D14", case["pricing"]["subscription"], "decimal"),
        (
            12,
            "Equal baseline metered price",
            '=IFERROR(D11/D8,"n.a.")',
            risk["equal_price_per_request"],
            "rate",
        ),
        (
            13,
            "Allocated fixed cost / adopter",
            "=IFERROR('AI Pricing'!D16/D9,\"n.a.\")",
            risk["fixed_cost_per_adopter"],
            "decimal",
        ),
        (
            15,
            "Top decile share of requests",
            '=IF(ISNUMBER(D7),NORM.S.DIST(D7-NORM.S.INV(0.9),TRUE),"n.a.")',
            risk["top_decile_usage_share"],
            "pct",
        ),
        (
            16,
            "Top decile mean requests",
            '=IFERROR(D8*D15/0.1,"n.a.")',
            risk["top_decile_mean_requests"],
            "whole",
        ),
        (
            17,
            "Flat allocated break-even requests",
            '=IFERROR((D11-D13)/D10,"n.a.")',
            risk["flat_allocated_contribution_break_even_requests"],
            "whole",
        ),
        (
            18,
            "Share above flat break-even",
            '=IFERROR(IF(D17<=0,1,IF(D7=0,IF(D8>D17,1,0),1-NORM.S.DIST((LN(D17/D8)+D7^2/2)/D7,TRUE))),"n.a.")',
            risk["share_above_flat_allocated_break_even"],
            "pct",
        ),
        (
            20,
            "Baseline flat contribution USD",
            '=IFERROR(D9*(D11-D8*D10)-$D$9*$D$13,"n.a.")',
            risk["baseline_flat_contribution"],
            "whole",
        ),
        (
            21,
            "Baseline equal-price metered USD",
            '=IFERROR(D9*D8*(D12-D10)-$D$9*$D$13,"n.a.")',
            risk["baseline_metered_contribution"],
            "whole",
        ),
        (
            23,
            "Top decile flat contribution / acct",
            '=IFERROR(D11-D16*D10-D13,"n.a.")',
            risk["top_decile_flat_mean_contribution"],
            "decimal",
        ),
        (
            24,
            "Top decile metered contrib / acct",
            '=IFERROR(D16*(D12-D10)-D13,"n.a.")',
            risk["top_decile_metered_mean_contribution"],
            "decimal",
        ),
    ]
    for r, label, expression, result, style in risk_rows:
        row("Usage Risk", r, label)
        if expression:
            formula("Usage Risk", f"D{r}", expression, "n.a." if blank else result, style)
        else:
            value("Usage Risk", f"D{r}", None if blank else result, style)
    sheets["Usage Risk"].data_validation(
        "D7", {"validate": "decimal", "criteria": "between", "minimum": 0, "maximum": 3}
    )
    sheets["Usage Risk"].merge_range(
        "C26:G28",
        "Baseline aggregate profit is equal. Heavy users lose money under flat pricing above the threshold; metering preserves variable margin only when price exceeds unit cost. Demand and usage responses are assumed, not measured.",
        styles["note"],
    )
    band(
        "Usage Risk",
        30,
        [
            "Mean usage multiplier",
            "Metered adoption penalty",
            "Flat contribution USD",
            "Metered contribution USD",
            "Metered less flat USD",
        ],
    )
    for r, item in enumerate(risk["stress_scenarios"], 31):
        value("Usage Risk", f"C{r}", item["mean_usage_multiplier"], "input")
        value("Usage Risk", f"D{r}", item["metered_adoption_penalty"], "input_pct")
        formula(
            "Usage Risk",
            f"E{r}",
            f'=IFERROR($D$9*($D$11-$D$8*C{r}*$D$10)-$D$9*$D$13,"n.a.")',
            "n.a." if blank else item["flat_contribution"],
            "whole",
        )
        formula(
            "Usage Risk",
            f"F{r}",
            f'=IFERROR($D$9*(1-D{r})*$D$8*C{r}*($D$12-$D$10)-$D$9*$D$13,"n.a.")',
            "n.a." if blank else item["metered_contribution"],
            "whole",
        )
        formula(
            "Usage Risk",
            f"G{r}",
            f'=IFERROR(F{r}-E{r},"n.a.")',
            "n.a." if blank else item["metered_contribution"] - item["flat_contribution"],
            "whole",
        )
    sheets["Usage Risk"].merge_range(
        "C48:G50",
        "All stresses are scenarios. Increased usage makes metering bill more; stress cases are not equal realized revenue. Fixed costs do not fall with adoption. Source: inputs/illustrative_case.json and reports/pricing_case.json.",
        styles["note"],
    )
    sheets["Usage Risk"].print_area("C2:G50")

    # Primary review: real financials above, separate illustrative pricing result below.
    value("Summary", "C5", "Salesforce actuals and planning assumptions", "note")
    band("Summary", 6, ["USD millions", inputs["period_end"] + " A", *headers])
    for r, label, source_row in [(8, "Revenue", 8), (10, "Operating income", 18), (12, "Free cash flow", 24)]:
        row("Summary", r, label)
        for column in "DEFG":
            formula(
                "Summary",
                f"{column}{r}",
                f"=Forecast!{column}{source_row}",
                cached[("Forecast", f"{column}{source_row}")],
            )
    row("Summary", 15, "Cash-generation accumulation only")
    for column in "DEFG":
        formula("Summary", f"{column}15", f"=Forecast!{column}27", cached[("Forecast", f"{column}27")])
    sheets["Summary"].merge_range(
        "C17:G19",
        "NOT A CASH BALANCE FORECAST. The accumulation above excludes financing, acquisitions, investments, repurchases and FX. Salesforce actuals are separate from the fictional operating case below.",
        styles["warning"],
    )
    value("Summary", "C22", "IllustrativeCo: monthly AI product contribution", "title")
    band(
        "Summary", 24, ["Pricing policy", "Revenue USD", "Inference USD", "Contribution USD", "Gross margin"]
    )
    for r, source in zip((25, 26, 27), (25, 26, 27), strict=True):
        row("Summary", r, pricing["results"][r - 25]["strategy"])
        for column in "DEFG":
            formula(
                "Summary",
                f"{column}{r}",
                f"='AI Pricing'!{column}{source}",
                cached[("AI Pricing", f"{column}{source}")],
                "pct" if column == "G" else "whole",
            )
    sheets["Summary"].merge_range(
        "C30:G32",
        "Test a capped add-on against equal-baseline-price metering. Tail risk and measured demand response decide; neither policy is proven superior. Operating inputs are fictional.",
        styles["note"],
    )
    sheets["Summary"].set_column("I:L", 18)
    sheets["Summary"].write_row("I25", ["Period", "Revenue USD", "Operating income USD"], styles["header"])
    for i, column in enumerate("DEFG", 26):
        value(
            "Summary", f"I{i}", inputs["period_end"] + " A" if column == "D" else headers["EFG".index(column)]
        )
        for dest, source in [("J", 8), ("K", 18)]:
            formula(
                "Summary",
                f"{dest}{i}",
                f"=Forecast!{column}{source}",
                cached[("Forecast", f"{column}{source}")],
            )
    chart = book.add_chart({"type": "column"})
    for column, label, color in [("J", "Revenue", "#245E83"), ("K", "Operating income", "#D9823B")]:
        chart.add_series(
            {
                "name": label,
                "categories": "=Summary!$I$26:$I$29",
                "values": f"=Summary!${column}$26:${column}$29",
                "fill": {"color": color},
                "border": {"none": True},
            }
        )
    chart.set_title({"name": "Revenue and operating income (USD millions)"})
    chart.set_y_axis({"num_format": '0,,"m"', "min": 0})
    chart.set_legend({"position": "bottom"})
    chart.set_size({"width": 660, "height": 340})
    sheets["Summary"].insert_chart("I6", chart)
    sheets["Summary"].print_area("C2:Q33")

    band("Checks", 6, ["Reconciliation", "Actual", "Year 1", "Year 2", "Year 3"])
    for r, label in [
        (8, "Gross profit: revenue less costs"),
        (10, "Operating income: profit less opex"),
        (12, "Free cash flow: OCF less capex"),
    ]:
        row("Checks", r, label)
        for column in "DEFG":
            expression = {
                8: f"Forecast!{column}8-Forecast!{column}11-Forecast!{column}12",
                10: f"Forecast!{column}12-Forecast!{column}17-Forecast!{column}18",
                12: f"Forecast!{column}21-Forecast!{column}23-Forecast!{column}24",
            }[r]
            formula("Checks", f"{column}{r}", "=" + expression, 0.0, "decimal")
    sheets["Checks"].conditional_format(
        "D8:G12",
        {
            "type": "formula",
            "criteria": "ABS(D8)>0.01",
            "format": book.add_format({"bg_color": "#FDE7E7", "font_color": "#B42318", "bold": True}),
        },
    )
    value("Checks", "C16", "Formula values checked against Python.", "note")
    book.close()
    metadata = {
        "generator": "XlsxWriter (public PyPI library)",
        "sheets": names,
        "populated_illustrative_case": not blank,
        "actual_period": inputs["period_end"],
        "forecast_year1_revenue": annual[0][8],
        "case_label": case["label"],
        "native_excel": "See native_excel_verification.json if available; not inferred from cached values.",
    }
    (output.parent / "verification.json").write_text(json.dumps(metadata, indent=2))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--blank", action="store_true", help="Leave operating inputs blank; preserve reported actuals."
    )
    args = parser.parse_args()
    print(build(args.output, blank=args.blank))
