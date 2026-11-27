"""Conservative pre-model screening; not a complete prompt-injection defense."""

import re
import unicodedata

RULES = (
    ("instruction_override", r"\bignore\b.{0,60}\b(rules?|instructions?|catalog|schema|restrictions?)\b"),
    (
        "fabricated_evidence",
        r"\b(pretend|fabricate|invent|fake)\b.{0,90}\b(experiment|test|uplift|results?|metric|savings|data|ran)\b",
    ),
    (
        "authority_override",
        r"\b(cfo|ceo|system|developer|administrator)\b.{0,80}\b(authoriz|override|new job|instruct)",
    ),
    ("unsupported_causality", r"\b(prove|say|state|explain|show)\b.{0,100}\b(caused?|causal|causation)\b"),
    ("assert_as_fact", r"\bstate\b.{0,60}\bas (a )?fact\b"),
    ("executable_request", r"\b(drop\s+table|read_csv\s*\(|execute\s+(select|sql)|run\s+select)"),
    ("credential_request", r"\b(api[ _-]?keys?|credentials?|environment variables?|secrets?)\b"),
    (
        "falsify_values",
        r"\b(replace|change|alter)\b.{0,80}\b(gross_profit_change|source value|reported number)\b",
    ),
)


def preflight_reason(question: str) -> str | None:
    if not isinstance(question, str) or not question.strip():
        return "empty_question"
    normalized = unicodedata.normalize("NFKC", question).casefold()
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Cf")
    normalized = " ".join(normalized.split())
    for reason, pattern in RULES:
        if re.search(pattern, normalized):
            return reason
    return None
