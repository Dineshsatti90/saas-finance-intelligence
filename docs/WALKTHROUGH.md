# Two-minute finance decision walkthrough

Open the [live dashboard](https://dineshsatti90-saas-finance.streamlit.app/). If it is waking, use the [overview screenshot](screenshots/overview.jpg) or [editable Excel workbook](../outputs/saas-finance/saas_financial_planning.xlsx).

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:25 | Reported financials | SEC records and source-linked Salesforce results are real. Customer counts, ARR flows and AI token bills in IllustrativeCo are separate assumptions. |
| 0:25–0:55 | Forecast evidence | The three methods share 40 targets. Training only uses labels available at each origin; driver WAPE is 3.99%, versus 4.44% trailing growth. |
| 0:55–1:30 | Illustrative AI pricing | At $0.0125/request and 2,000 requests, both policies bill $25 and contribute $8k aggregate monthly. The old $0.015 example simply charged more. |
| 1:30–2:00 | Uneven usage and stresses | Under assumed log-sigma 1.2, the top decile uses 46.8% of requests. Flat allocated contribution becomes negative above 2,500 requests; metering preserves variable margin but may reduce adoption. A 20% relative adoption penalty drops its contribution to $4.4k. |
| 2:00–2:30 | Decision & AI record; Excel Usage Risk | Test a capped add-on against equal-baseline-price metering. Show live Excel formulas and the harder AI evaluation, including refusal failures. Cash accumulation is not a full cash-balance forecast. |

Interview close: “The policy decision depends on observed usage and willingness to pay; equal baseline profit alone cannot establish which pricing structure is best.”
