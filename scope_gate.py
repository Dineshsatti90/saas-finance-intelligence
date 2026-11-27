"""Data-contract scope gate for the finance commentary assistant.

The assistant can only retrieve four calculated gross-profit bridge amounts. The
keyword preflight in ``request_policy.py`` blocked known attack phrasings and did
not generalize to the first-pass v2 questions. This gate inverts the logic:

1. **Allowlist.** A question must ask about a bridge amount (gross-profit change,
   revenue effect, margin effect or reconciliation difference).
2. **Data contract.** It is refused if it asks for anything outside retrieval of
   those amounts: causes, forecasts, budgets or plans, investment views, derived
   calculations, unavailable metrics, peer comparisons, hypothetical or altered
   values, external execution or instruction changes.

After the blind v4 run, ``investment_view`` no longer matches the bare word
"share" (it blocked "share of usage"), and ``peer_comparison`` needs a peer or
industry reference rather than any use of "compare" or "versus". Causal
questions ("why", "what drives") remain refused by design.

Deterministic, no model or network access. A question that passes can still be
answered with the wrong bridge amount; that is measured separately.
"""

from __future__ import annotations

import re
import unicodedata

IN_SCOPE = (
    r"\bgross profit\b",
    r"\bbridge\b",
    r"\brevenue (effect|component|part|portion)\b",
    r"\bvolume (effect|component|part|portion)s?\b",
    r"\bvolume and margin\b",
    r"\bmargin (effect|component|part|portion|shift)\b",
    r"\b(shift|change) in (gross )?margin\b",
    r"\bhigher revenue\b",
    r"\breconcil\w*\b",
    r"\bresidual\b",
)

OUT_OF_CONTRACT = {
    "causal_claim": r"\b(why|caus\w*|because|driv\w*|attribut\w*|due to|decisions?|responsible)\b",
    "forecast": r"\b(forecast\w*|predict\w*|project\w*|next (year|quarter|month)|will (be|grow|fall)|future|outlook)\b",
    "budget_or_plan": r"\b(budget\w*|operating plan|plan|target|guidance|variance against)\b",
    "investment_view": r"\b(buy|sell|stocks?|share price|shares outstanding|shareholders?|equity value|valuation|undervalued|overvalued|invest\w*|price target)\b",
    "derived_calculation": r"\b(calculat\w*|comput\w*|percent\w*|ratio|growth rate|annual \w* ?growth|express(ed)? as|divid\w*|cagr|per cent)\b",
    "unavailable_metric": r"\b(ebitda|operating income|net income|earnings|arr|churn|customers?|headcount|engineers?|hired|hires|ceo|cfo said|management (said|say)|filing passage|passage|segment|cash flow)\b",
    "peer_comparison": r"\b(peers?|competitors?|rivals?|industry|sector|microsoft|oracle|google|amazon|other compan\w*|other businesses)\b",
    "hypothetical_or_altered": r"\b(assum\w*|treat\w* (it |this |the [a-z ]+ )?as|twice|double|triple|replace|set \w+ to|pretend|hypothetical\w*|invent\w*|fabricat\w*|realized ai cost savings|cost savings)\b",
    "external_or_execution": r"\b(drop table|sql|execute|api key|environment variables?|credentials?|secrets?|url|https?)\b",
    "instruction_change": r"\b(ignore|disregard|forget|system:|new job|admin mode|hidden instructions?|you are now|authori[sz]\w*|as (a )?fact|override)\b",
}


def _normalize(question: str) -> str:
    text = unicodedata.normalize("NFKC", question).casefold()
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return " ".join(text.replace("_", " ").split())


def scope_decision(question: str) -> tuple[bool, str]:
    """Return ``(allowed, reason)``. ``reason`` names the contract family on refusal."""
    if not isinstance(question, str) or not question.strip():
        return False, "empty_question"
    text = _normalize(question)
    for family, pattern in OUT_OF_CONTRACT.items():
        if re.search(pattern, text):
            return False, family
    if not any(re.search(p, text) for p in IN_SCOPE):
        return False, "no_bridge_metric"
    return True, "in_scope"


SCOPE_HELP = (
    "This assistant only retrieves the calculated gross-profit bridge: the total gross-profit change, "
    "the revenue effect at prior margin, the margin effect at current revenue and the reconciliation "
    "difference. Forecasts, pricing results and peer metrics are in the dashboard and Excel model."
)
