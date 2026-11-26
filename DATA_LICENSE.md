# Source and licensing notes

Financial data is downloaded from the US Securities and Exchange Commission's [Financial Statement Data Sets](https://www.sec.gov/dera/data/financial-statement-data-sets.html) and [EDGAR XBRL APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). The original issuers are identified by ticker and CIK; normalized facts include links to filing accession pages.

The SEC explains that its datasets are extracted from issuer filings and may contain errors. This project preserves source tags, units, period ends, publication dates and file fingerprints so users can verify values against the issuer's filings. This project is not affiliated with or endorsed by the SEC or the issuers.

Raw archives and complete company-facts downloads remain local. Published financial extracts are selected/normalized outputs; no claim of ownership over issuer disclosures is made. Observe SEC fair-access requirements when refreshing and review applicable source terms before downstream redistribution or commercial use.

No separate open-source license is applied to original application code in this release. Public GitHub visibility should not be interpreted as an unrestricted code-reuse license.
