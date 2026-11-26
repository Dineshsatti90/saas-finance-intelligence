# Finance AI evaluation

## Recorded protocol
Local `qwen2.5:3b`, Ollama, temperature 0, seed 42, 8,192-token context, 600-token output limit. Ten historical gross-profit bridges are selected at deterministic evenly spaced positions in the sorted eligible annual panel. The selection rule is implemented in `evaluate_ai.py`, not chosen after seeing which cases pass.

## Result
**100% contract pass across 10 cases.** Every accepted response uses valid evidence keys and finite numerical values agreeing with the source to the defined tolerance. The model's raw claims, rendered statements, source evidence and per-case timing are committed in `reports/ai_evaluation.json`. The Salesforce example is in `reports/ai_commentary.json`.

No live-model failures occurred in this ten-case run. The tests separately challenge the verifier with a fabricated cause, an incorrect value and NaN. Those are deliberate negative test inputs, not fabricated examples of actual model behavior.

## Scope
The model selects calculated observations; a deterministic renderer supplies the final text and metric-key citations. Reconciliation differences and numerical equality do not establish causal explanations or a complete board narrative. This run does not score investment quality, forecasting ability, human relevance or free-form financial writing. Source references remain visible for review.

## Reproduce
Configure `LLM_MODEL`, `LLM_BASE_URL` and optionally `LLM_API_KEY`. For local Ollama also set `LLM_BACKEND=ollama`, then run `python evaluate_ai.py`. The dashboard shows the saved evaluation without requiring credentials or a live model.
