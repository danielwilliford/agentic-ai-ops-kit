from __future__ import annotations

import re

from app.models import PolicyGateResult, RunStatus

POLICY_TERMS: dict[str, tuple[str, ...]] = {
    "payment": ("payment", "pay", "payout", "settle", "settlement", "wire", "disburse"),
    "approval": ("approve", "approval", "authorize", "authorization"),
    "denial": ("deny", "denial", "reject", "rejection"),
    "production_mutation": (
        "production",
        "prod",
        "deploy",
        "mutation",
        "mutate",
        "replace",
        "send",
        "close claim",
    ),
}

BLOCKING_PHRASES = (
    "auto approve",
    "auto-approve",
    "without human",
    "skip human",
    "send payment",
    "issue payment",
    "pay claim",
    "deny claim",
    "close claim",
    "push to production",
    "deploy to production",
    "mutate production",
)

SAFE_HUMAN_REVIEW_PHRASES = (
    "human approval",
    "approval packet",
    "approval gate",
    "human review",
    "review packet",
)


def _contains_term(text: str, term: str) -> bool:
    if " " in term or "-" in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def evaluate_policy_gate(request: str) -> PolicyGateResult:
    text = request.lower()
    matched_terms: list[str] = []
    categories: list[str] = []
    for category, terms in POLICY_TERMS.items():
        category_matches = [term for term in terms if _contains_term(text, term)]
        if category_matches:
            categories.append(category)
            matched_terms.extend(category_matches)

    has_blocking_phrase = any(phrase in text for phrase in BLOCKING_PHRASES)
    has_safe_review_phrase = any(phrase in text for phrase in SAFE_HUMAN_REVIEW_PHRASES)
    blocks_tool_execution = has_blocking_phrase or any(
        category in categories for category in {"payment", "denial", "production_mutation"}
    )
    if categories and not blocks_tool_execution and not has_safe_review_phrase:
        blocks_tool_execution = "approval" in categories

    if categories:
        reason = (
            "policy-sensitive request requires human review before any approval, denial, "
            "payment, or production mutation"
        )
        return PolicyGateResult(
            status=RunStatus.HUMAN_REVIEW_REQUIRED,
            matched_terms=sorted(set(matched_terms)),
            categories=sorted(set(categories)),
            blocks_tool_execution=blocks_tool_execution,
            reason=reason,
        )

    return PolicyGateResult(
        status=RunStatus.PENDING_HUMAN_APPROVAL,
        matched_terms=[],
        categories=[],
        blocks_tool_execution=False,
        reason="no policy-sensitive mutation terms detected",
    )
