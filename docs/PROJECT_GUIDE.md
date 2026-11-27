# Run, rebuild and review

## Quick demo

```bash
python -m venv .venv
# Windows: .venv/Scripts/Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The demo uses committed public aggregates and requires no raw download or model key. Free Streamlit hosting can sleep after inactivity; the README preview and [walkthrough](WALKTHROUGH.md) remain available while it wakes.

## AI setup and scope

Use a local Ollama endpoint or a compatible configured model. Set `LLM_BACKEND=ollama`, `LLM_BASE_URL=http://127.0.0.1:11434/v1` and `LLM_MODEL=llama3:8b` for the native local adapter. The model selects source references; Python renders values. Explicit preflight patterns are a limited extra check, not a complete injection defense. See [evaluation protocol and failures](AI_EVALUATION.md) before interpreting scores.

## Validation

CI runs Ruff checks, committed Streamlit AppTests and focused numerical tests. [Workflow](../.github/workflows/check.yml), [tests](../tests), [method choices](METHOD_CHOICES.md), [data dictionary](DATA_DICTIONARY.md), [operations](OPERATIONS.md).

## Rebuild the real SEC analysis

Set `SEC_USER_AGENT` to a project name and real contact, then run:

```bash
python fetch.py
python model.py --asof 2026-11-26
python planning.py
python forecast_study.py
python pricing_case.py
python build_workbook.py
python -m pytest tests -q
```

The warehouse profiles 3,832,977 SEC numeric records from the full 2025 Q4 release and 171,654 company-fact observations across eight peers. Source tags, accession numbers, filing dates and fiscal periods are retained. [Annual facts](../reports/annual_facts.csv), [data terms](../DATA_LICENSE.md), [normalized peer metrics](../reports/peer_metrics.csv).

## Excel and pricing

[Download the editable workbook](../outputs/saas-finance/saas_financial_planning.xlsx). Nine sheets keep reported Salesforce financials separate from illustrative ARR, staffing and token economics. Usage Risk shows baseline tail exposure; Adoption Stress varies both policies independently across 64 cases. A separate light-user-exit scenario changes the retained usage mix. [Pricing decision](../reports/pricing_decision.md), [inputs](../inputs/illustrative_case.json), [stress CSV](../reports/pricing_stress.csv).

The public XlsxWriter generator caches formulas for review and supports `python build_workbook.py --blank --output blank_operating_template.xlsx`. Native Microsoft Excel verification exercises scenario changes, equal-price parity, both adoption penalties, dispersion and a zero-adopter boundary. [Verification](../outputs/saas-finance/native_excel_verification.json).

## Forecast evidence

The same 40 annual targets compare a fixed-penalty ridge driver model (3.99% WAPE), trailing growth (4.44%) and flat revenue (14.23%). Features and training labels were public at each origin; scoring uses restated outcomes at the cutoff. [Per-origin forecasts](../reports/driver_backtest.csv), [summary](../reports/driver_backtest_summary.json), [Power BI measures](../bi/measures.dax).

## Limitations

Eight peers form a small selected annual panel; results do not establish production monthly forecasting accuracy. Public GAAP revenue is not ARR or an internal budget. IllustrativeCo operating inputs, lognormal usage and adoption responses are assumptions, not reported customer records or current vendor quotations. No demand elasticity or retention benefit is estimated. Cash accumulation excludes financing, acquisitions, investments, repurchases and FX and is not a full cash-balance forecast. Models can return irrelevant references, so the public dashboard shows saved verified bridge outputs rather than free-form finance advice. No native Power BI `.pbix` is included.
