"""Expanding-window, point-in-time operational-driver forecast comparison."""

from pathlib import Path
from functools import lru_cache
from datetime import date
import json

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from fetch import PEERS
from model import annual_facts, write_csv

ROOT = Path(__file__).resolve().parent
FEATURES = ["last_growth", "previous_growth", "operating_margin", "ocf_margin", "log_revenue"]


@lru_cache(maxsize=512)
def vintage(ticker: str, cutoff: str) -> list[dict]:
    return annual_facts(ticker, cutoff)


def features(ticker: str, cutoff: str, end: str) -> tuple[list[float], float] | None:
    history = sorted(
        [r for r in vintage(ticker, cutoff) if r["metric"] == "revenue" and r["period_end"] <= end],
        key=lambda r: r["period_end"],
    )
    if len(history) < 3:
        return None
    last = history[-3:]
    if any(
        not 300 <= (date.fromisoformat(b["period_end"]) - date.fromisoformat(a["period_end"])).days <= 380
        for a, b in zip(last, last[1:])
    ):
        return None
    current = last[-1]["value"]
    metrics = {r["metric"]: r["value"] for r in vintage(ticker, cutoff) if r["period_end"] == end}
    if not all(key in metrics for key in ("operating_income", "operating_cash_flow")):
        return None
    return (
        [
            current / last[-2]["value"] - 1,
            last[-2]["value"] / last[-3]["value"] - 1,
            metrics["operating_income"] / current,
            metrics["operating_cash_flow"] / current,
            float(np.log(current)),
        ],
        current,
    )


def run() -> None:
    cutoff = json.loads((ROOT / "reports/model_inputs.json").read_text())["asof"]
    candidates = []
    for ticker in PEERS:
        final = sorted(
            [r for r in vintage(ticker, cutoff) if r["metric"] == "revenue"], key=lambda r: r["period_end"]
        )
        # Freeze origin and target at their first observed publication, not later restatements.
        data = json.loads((ROOT / "data/raw" / f"{ticker}.json").read_text())["facts"]["us-gaap"]
        from model import TAGS

        for prior, target in zip(final, final[1:]):
            if (
                not 300
                <= (date.fromisoformat(target["period_end"]) - date.fromisoformat(prior["period_end"])).days
                <= 380
            ):
                continue

            def first_filed(end: str) -> str:
                return min(
                    f["filed"]
                    for tag in TAGS["revenue"]
                    for f in data.get(tag, {}).get("units", {}).get("USD", [])
                    if f.get("form") == "10-K"
                    and f.get("end") == end
                    and f.get("start")
                    and 300 <= (date.fromisoformat(f["end"]) - date.fromisoformat(f["start"])).days <= 380
                )

            origin = first_filed(prior["period_end"])
            published = first_filed(target["period_end"])
            item = features(ticker, origin, prior["period_end"])
            if item is None or origin >= target["period_end"]:
                continue
            vector, last = item
            first_actual = next(
                r["value"]
                for r in vintage(ticker, published)
                if r["metric"] == "revenue" and r["period_end"] == target["period_end"]
            )
            candidates.append(
                {
                    "ticker": ticker,
                    "origin": origin,
                    "target_end": target["period_end"],
                    "label_available": published,
                    "features": vector,
                    "last_revenue": last,
                    "training_growth": first_actual / last - 1,
                    "actual": target["value"],
                }
            )
    results = []
    for case in sorted(candidates, key=lambda x: (x["origin"], x["ticker"])):
        training = [
            x for x in candidates if x["label_available"] <= case["origin"] and x["origin"] < case["origin"]
        ]
        if len(training) < 12:
            continue
        estimator = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
        estimator.fit([x["features"] for x in training], [x["training_growth"] for x in training])
        prediction = float(np.clip(estimator.predict([case["features"]])[0], -0.5, 1.0))
        rates = {
            "flat_revenue": 0.0,
            "trailing_growth": float(np.clip(np.mean(case["features"][:2]), -0.5, 1.0)),
            "operating_driver_ridge": prediction,
        }
        for method, growth in rates.items():
            forecast = case["last_revenue"] * (1 + growth)
            results.append(
                {
                    "ticker": case["ticker"],
                    "origin": case["origin"],
                    "target_period_end": case["target_end"],
                    "training_cases": len(training),
                    "latest_training_label": max(x["label_available"] for x in training),
                    "method": method,
                    "forecast": forecast,
                    "actual": case["actual"],
                    "absolute_error": abs(forecast - case["actual"]),
                }
            )
    write_csv(ROOT / "reports/driver_backtest.csv", results)
    summary = {
        "features": FEATURES,
        "model": "StandardScaler + Ridge(alpha=10); fixed before evaluation",
        "training_rule": "Only labels filed on or before each origin; first-published training labels; minimum 12 cases",
        "target_rule": "Restated actual at the analysis cutoff; same paired targets for every method",
        "methods": {},
    }
    for method in ("flat_revenue", "trailing_growth", "operating_driver_ridge"):
        rows = [x for x in results if x["method"] == method]
        summary["methods"][method] = {
            "targets": len(rows),
            "wape": sum(x["absolute_error"] for x in rows) / sum(x["actual"] for x in rows),
        }
    winner = min(summary["methods"], key=lambda m: summary["methods"][m]["wape"])
    summary["recommendation"] = (
        f"Use {winner} as the benchmark for this paired annual panel; complexity alone does not justify replacing the best validated method."
    )
    (ROOT / "reports/driver_backtest_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
