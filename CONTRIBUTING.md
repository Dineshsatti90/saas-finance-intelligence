# Contributing

Propose new issuers, tags or model features in an issue with the business need and supporting filing references. Keep the project focused on corporate planning and strategic finance.

1. Use a branch and make a focused change.
2. Run `python -m pytest tests -q`.
3. For normalization or forecasting changes, rebuild with an explicit analysis cutoff, inspect source records and compare backtest outputs.
4. For workbook changes, recalculate affected cases, verify missing-input behavior and review exported sheets.
5. Describe validation and remaining limitations in the pull request.

Do not commit credentials, dependency folders, raw bulk downloads or databases. Preserve distinctions between reported actuals, externally generated forecasts and illustrative operating assumptions. Do not substitute GAAP revenue for ARR or label an external forecast as an internal budget. Raise sensitive security defects privately with the repository owner; never disclose a token in a public issue.
