# Reproduction and model operations

## Data refresh

1. Create/activate a Python 3.10+ environment and install `requirements.txt` or the tested top-level pins in `requirements.lock.txt`.
2. Set `SEC_USER_AGENT` to your project name and real contact address. Respect SEC fair-access rules; the downloader is sequential and cached.
3. Run `python fetch.py`, then `python model.py --asof 2026-11-26` and `python planning.py`.
4. Run `python -m pytest tests -q`, then `streamlit run app.py`.

Raw downloads and the DuckDB database stay local. Refreshing the company-facts files can change comparative vintages, so preserve manifests when comparing results. The fixed 2025 Q4 bulk release and subsequent company-facts annual panel have distinct purposes; their dates need not be identical. Cache replacement is a deliberate manual action, not an automatic silent redownload.

## Excel review

Open `outputs/saas-finance/saas_financial_planning.xlsx`:

1. Review reported values and filing references on Actuals.
2. Select Base or Downside using the numeric selector on Assumptions.
3. Inspect Revenue, Operating Income and Free Cash Flow on Summary; trace calculations on Forecast.
4. Enter your own operating assumptions on AI Pricing and ARR and Staffing. Blank required inputs remain `n.a.`.
5. Review reconciliation differences on Checks. Passing differences display as 0.00.

Blue values identify numeric inputs; working cross-sheet links are green; output numbers use dark text. Amber cells request operating assumptions unavailable in the public data. The workbook contains formulas and an editable native chart. Native Excel recalculation was not exercised in the reference run; first open should be reviewed in your Excel version before relying on edited cases.

`build_workbook.mjs` is an authoring source requiring a separately available `@oai/artifact-tool` runtime. That package is not part of the Python setup or promised as a public package-registry dependency. The delivered `.xlsx` can be used without the authoring runtime.

## Optional LLM

Configure `LLM_BASE_URL`, `LLM_MODEL` and `LLM_API_KEY` as required by a trusted OpenAI-compatible JSON-mode endpoint. Then run `python planning.py --llm` or use the dashboard action. Environment examples are not automatically loaded. Provider requests may incur charges. Do not commit credentials.

## Troubleshooting

- **SEC 403 / blocked download:** use a descriptive User-Agent and real contact, reduce requests and respect the source service's restrictions. Do not bypass source controls.
- **Missing raw file:** complete downloads before normalization. No synthetic historical replacement is used.
- **Missing metric:** inspect the issuer filing and tag mapping. Do not fill missing financials with zero or assume custom tags have the same accounting meaning.
- **Dashboard missing model inputs:** run the normalization and planning commands first.
- **AI unavailable:** use the numerical analysis and workbook; an unconfigured model is recorded as not run.
- **Power BI:** import the report CSVs; filter to one ticker and fiscal period for the supplied measures. Never sum repeated annual/XBRL vintages as though they are separate sales.

## Publication boundary

Commit source code, docs, aggregate/public financial extracts, filing citations and the workbook. Exclude raw ZIP/JSON/TXT downloads, warehouses, local environments, dependency junctions and `.env`. The published repo includes Power BI CSVs/DAX, not a native `.pbix` or a publicly hosted dashboard.
