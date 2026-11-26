"""Record real local-model outputs on ten disclosed historical finance cases."""

from pathlib import Path
from datetime import datetime, timezone
import json
import os
import time

import pandas as pd

from planning import bridge, commentary

ROOT = Path(__file__).resolve().parent


def run() -> None:
    frame = pd.read_csv(ROOT / "reports/annual_financials.csv").sort_values(["ticker", "period_end"])
    cases = []
    for ticker, group in frame.groupby("ticker"):
        records = group.to_dict("records")
        for prior, current in zip(records, records[1:]):
            if pd.isna(prior["gross_profit"]):
                prior["gross_profit"] = prior["revenue"] - prior["cost_of_revenue"]
            if pd.isna(current["gross_profit"]):
                current["gross_profit"] = current["revenue"] - current["cost_of_revenue"]
            if pd.notna(prior["gross_profit"]) and pd.notna(current["gross_profit"]):
                cases.append(
                    {
                        "company": ticker,
                        "period_end": str(current["period_end"]),
                        "evidence": bridge(prior, current),
                    }
                )
    # Evenly spaced deterministic cases, exposing the selection instead of cherry-picking successes.
    selected = [cases[round(i * (len(cases) - 1) / 9)] for i in range(10)]
    report = {
        "model": os.environ.get("LLM_MODEL"),
        "run_at": datetime.now(timezone.utc).isoformat(),
        "backend": os.environ.get("LLM_BACKEND", "openai-compatible"),
        "temperature": 0,
        "seed": 42,
        "evaluation": "10 deterministic historical bridge cases; exact-value/source-key contract, not narrative quality",
        "status": "running",
        "results": [],
    }
    for i, case in enumerate(selected, 1):
        started = time.perf_counter()
        try:
            output = commentary(case["evidence"])
            valid = output["status"] == "completed" and bool(output["verified_statements"])
            result = {**case, "passed": valid, "output": output}
        except Exception as error:
            result = {**case, "passed": False, "error": str(error)}
        result["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        report["results"].append(result)
        (ROOT / "reports/ai_evaluation.json").write_text(json.dumps(report, indent=2))
        print(f"Evaluated finance case {i}/10", flush=True)
    report["status"] = "completed"
    report["pass_rate"] = sum(x["passed"] for x in report["results"]) / len(report["results"])
    report["failures"] = [i + 1 for i, r in enumerate(report["results"]) if not r["passed"]]
    (ROOT / "reports/ai_evaluation.json").write_text(json.dumps(report, indent=2))
    evidence = json.loads((ROOT / "reports/variance_evidence.json").read_text())
    try:
        output = commentary(evidence)
    except Exception as error:
        output = {
            "status": "rejected",
            "model": os.environ.get("LLM_MODEL"),
            "error": str(error),
            "evidence": evidence,
        }
    (ROOT / "reports/ai_commentary.json").write_text(json.dumps(output, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    run()
