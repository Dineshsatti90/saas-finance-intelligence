"""Evaluate the finance data-contract scope gate without any model or network access.

* **Gate only** on every case set, including the held-out v3 set: unsupported
  refusal and supported false refusal.
* **Replay** of the recorded raw-model runs: a case the gate refuses becomes a
  refusal; every other case keeps the model's recorded output unchanged. No
  model output is re-generated or edited.

Usage::

    python evaluate_gate.py
    python evaluate_gate.py --cases my_blind_cases.json   # gate-only, any set
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scope_gate import scope_decision

ROOT = Path(__file__).resolve().parent
CASES_V2 = ROOT / "eval/adversarial_cases_v2.json"
HOLDOUT = ROOT / "eval/holdout_cases_v3.json"
RUNS = {
    "qwen2.5:3b": ROOT / "eval/runs/qwen3b_references_v2.json",
    "llama3:8b": ROOT / "eval/runs/llama8b_references_v2.json",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate_only(cases: list[dict]) -> dict:
    rows = []
    for case in cases:
        allowed, reason = scope_decision(case["question"])
        unsupported = case["expected"] == "unsupported"
        rows.append(
            {
                "id": case["id"],
                "expected": case["expected"],
                "allowed": allowed,
                "reason": reason,
                "correct": allowed != unsupported,
            }
        )
    unsupported = [r for r in rows if r["expected"] == "unsupported"]
    supported = [r for r in rows if r["expected"] != "unsupported"]
    return {
        "cases": len(rows),
        "unsupported_refusal_rate": sum(not r["allowed"] for r in unsupported) / max(1, len(unsupported)),
        "supported_false_refusal_rate": sum(not r["allowed"] for r in supported) / max(1, len(supported)),
        "misses": [r for r in rows if not r["correct"]],
        "decisions": {str(r["id"]): r["reason"] for r in rows},
    }


def replay(run_path: Path, split: str) -> dict:
    run = json.loads(run_path.read_text(encoding="utf-8"))
    if run.get("cases_sha256") != sha(CASES_V2):
        raise ValueError(f"{run_path} was recorded on different cases")
    rows = [r for r in run["results"] if r["split"] == split]
    raw_pass = gated_pass = raw_refused = gated_refused = n_unsupported = 0
    raw_shown = gated_shown = 0
    for row in rows:
        allowed, _ = scope_decision(row["question"])
        unsupported = row["expected"] == "unsupported"
        status = row.get("output", {}).get("status")
        raw_pass += bool(row["passed"])
        if unsupported:
            n_unsupported += 1
            raw_refused += status == "unsupported"
            raw_shown += status == "completed"
        if allowed:
            gated_pass += bool(row["passed"])
            if unsupported:
                gated_refused += status == "unsupported"
                gated_shown += status == "completed"
        else:
            gated_pass += unsupported
            gated_refused += unsupported
    n = len(rows)
    return {
        "run_file": str(run_path.relative_to(ROOT)).replace("\\", "/"),
        "split": split,
        "cases": n,
        "raw_pass_rate": raw_pass / n,
        "gated_pass_rate": gated_pass / n,
        "raw_unsupported_refusal_rate": raw_refused / max(1, n_unsupported),
        "gated_unsupported_refusal_rate": gated_refused / max(1, n_unsupported),
        "raw_unsupported_answers_shown": raw_shown,
        "gated_unsupported_answers_shown": gated_shown,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, help="Score the gate alone on any case file")
    args = parser.parse_args()
    if args.cases:
        result = gate_only(json.loads(args.cases.read_text(encoding="utf-8")))
        print(json.dumps({k: v for k, v in result.items() if k != "decisions"}, indent=2))
        return
    v2_cases = json.loads(CASES_V2.read_text(encoding="utf-8"))
    sets = {
        "v1_regression": ([c for c in v2_cases if c["split"] == "v1_regression"], "tuning (seen)"),
        "first_pass_v2": ([c for c in v2_cases if c["split"] == "first_pass_v2"], "tuning (seen)"),
        "holdout_v3": (json.loads(HOLDOUT.read_text(encoding="utf-8")), "held out; same author as gate"),
    }
    report = {
        "gate_source_sha256": sha(ROOT / "scope_gate.py"),
        "holdout_sha256": sha(HOLDOUT),
        "method": "Deterministic bridge-metric allowlist + documented-limitation refusals; no model or network.",
        "caveat": (
            "The gate was tuned on the v1 and v2 cases. The v3 set was written and fingerprinted before the "
            "gate code, but by the same author, who knew those questions while writing rules. Treat v3 as an "
            "upper bound, not an independent generalization estimate. Score blind cases written by someone "
            "else with --cases."
        ),
        "gate_only": {name: {"role": role, **gate_only(cases)} for name, (cases, role) in sets.items()},
        "replay_of_recorded_raw_runs": [
            {"model": model, **replay(path, split)}
            for model, path in RUNS.items()
            for split in ("v1_regression", "first_pass_v2")
        ],
    }
    out = ROOT / "reports/scope_gate_evaluation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for split, r in report["gate_only"].items():
        print(
            f"{split:14} refusal {r['unsupported_refusal_rate']:.0%}  "
            f"false refusal {r['supported_false_refusal_rate']:.0%}  ({r['role']})"
        )
    for r in report["replay_of_recorded_raw_runs"]:
        print(
            f"{r['model']:11} {r['split']:14} pass {r['raw_pass_rate']:.0%} -> {r['gated_pass_rate']:.0%}  "
            f"refusal {r['raw_unsupported_refusal_rate']:.0%} -> {r['gated_unsupported_refusal_rate']:.0%}  "
            f"unsupported shown {r['raw_unsupported_answers_shown']} -> {r['gated_unsupported_answers_shown']}"
        )


if __name__ == "__main__":
    main()
