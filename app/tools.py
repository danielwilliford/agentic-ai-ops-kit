from __future__ import annotations

from app.models import ToolCall

ALLOWED_TOOLS = {"extract_entities", "build_timeline", "classify_risk"}


def _ensure_allowed(name: str) -> None:
    if name not in ALLOWED_TOOLS:
        raise ValueError(f"Tool {name!r} is not allowlisted")


def extract_entities(request: str) -> ToolCall:
    _ensure_allowed("extract_entities")
    claim_id = "CLM-1042" if "CLM-1042" in request else "UNKNOWN"
    output = {
        "claim_id": claim_id,
        "loss_type": "water damage" if "water" in request.lower() else "unknown",
        "document_type": "homeowners policy/SOP",
    }
    return ToolCall(name="extract_entities", input={"request": request}, output=output)


def build_timeline(request: str) -> ToolCall:
    _ensure_allowed("build_timeline")
    output = {"timeline": ["intake_received", "policy_sections_retrieved", "human_review_required"]}
    return ToolCall(name="build_timeline", input={"request": request}, output=output)


def classify_risk(request: str, citations: list[str]) -> ToolCall:
    _ensure_allowed("classify_risk")
    flags = []
    if not citations:
        flags.append("missing_source_citations")
    if "approve" in request.lower() and "human" not in request.lower():
        flags.append("approval_language_requires_human_review")
    output = {"risk_flags": flags or ["requires_human_approval_before_action"]}
    return ToolCall(name="classify_risk", input={"request": request, "citations": citations}, output=output)
