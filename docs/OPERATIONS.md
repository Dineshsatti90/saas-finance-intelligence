# Reproduction and model operations

## Data refresh

1. Create/activate a Python 3.10+ environment and install `requirements.txt` or the tested top-level pins in `requirements.lock.txt`.
2. Set `SEC_USER_AGENT` to your project name and real contact address. Respect SEC fair-access rules; the downloader is sequential and cached.
3. Run `python fetch.py`, `python model.py --asof 2026-11-26`, `python planning.py`, `python forecast_study.py`, `python pricing_case.py` and `python build_workbook.py` in that order.
4. Run `python -m pytest tests -q`, then `streamlit run app.py`.

Raw downloads and the DuckDB database stay local. Refreshing the company-facts files can change comparative vintages, so preserve manifests when comparing results. The fixed 2025 Q4 bulk release and subsequent company-facts annual panel have distinct purposes; their dates need not be identical. Cache replacement is a deliberate manual action, not an automatic silent redownload.

## Excel review

Open `outputs/saas-finance/saas_financial_planning.xlsx`:

1. Review reported values and filing references on Actuals.
2. Select Base or Downside using the numeric selector on Assumptions.
3. Inspect Revenue, Operating Income and Free Cash Flow on Summary; trace calculations on Forecast.
4. Review the populated, explicitly fictional IllustrativeCo assumptions on AI Pricing and ARR and Staffing. Replace them with your own assumptions if appropriate; missing required inputs remain `n.a.`.
5. Review reconciliation differences on Checks. Passing differences display as 0.00.

Blue values identify numeric inputs; working cross-sheet links are green; output numbers use dark text. Amber cells identify operating assumptions. The workbook contains formulas and an editable native chart. Microsoft Excel 16.0 performed full recalculation, scenario switching, later-period input changes and a zero-adopter boundary check. Inputs were restored and saved; see `outputs/saas-finance/native_excel_verification.json`.

Rebuild with `python build_workbook.py`, using the public XlsxWriter package in requirements. OpenPyXL is used for verification tests, not authoring. Generate an optional blank operating template with `python build_workbook.py --blank --output blank_operating_template.xlsx`. Salesforce actuals remain populated; missing operating inputs show `n.a.`. On Windows with Excel installed, `tools/verify_excel.ps1 -WorkbookPath <path>` reproduces native recalculation checks in the background.

## Optional LLM

Configure `LLM_BASE_URL`, `LLM_MODEL` and `LLM_API_KEY` as required by a trusted OpenAI-compatible JSON-mode endpoint. Run `python evaluate_ai.py` for the ten-case evaluation and Salesforce example. For local Ollama use `LLM_MODEL=qwen2.5:3b`, `LLM_BASE_URL=http://127.0.0.1:11434/v1`, `LLM_BACKEND=ollama`. Environment examples are not automatically loaded. Remote-provider requests may incur charges. The public dashboard shows saved verified outputs and does not expose model credentials.

## Troubleshooting

- **SEC 403 / blocked download:** use a descriptive User-Agent and real contact, reduce requests and respect the source service's restrictions. Do not bypass source controls.
- **Missing raw file:** complete downloads before normalization. No synthetic historical replacement is used.
- **Missing metric:** inspect the issuer filing and tag mapping. Do not fill missing financials with zero or assume custom tags have the same accounting meaning.
- **Dashboard missing model inputs:** run the normalization and planning commands first.
- **AI unavailable:** use the numerical analysis and workbook; an unconfigured model is recorded as not run.
- **Power BI:** import the report CSVs; filter to one ticker and fiscal period for the supplied measures. Never sum repeated annual/XBRL vintages as though they are separate sales.

## Publication boundary

Commit source code, docs, public financial extracts, filing citations and the workbook. Exclude raw downloads, warehouses, environments, dependency junctions and `.env`. The demo runs from committed CSVs; no database download is required. Power BI CSVs/DAX are supplied; a native `.pbix` is not included.
