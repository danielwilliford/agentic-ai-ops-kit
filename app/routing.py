from __future__ import annotations

from dataclasses import dataclass

from app.models import PolicyGateResult


@dataclass(frozen=True)
class LaneContract:
    lane_id: str
    provider_id: str
    max_complexity: int
    cost_units: float
    purpose: str


LANES: dict[str, LaneContract] = {
    "small_local_worker": LaneContract(
        lane_id="small_local_worker",
        provider_id="local_small_worker_dry_run",
        max_complexity=2,
        cost_units=1.0,
        purpose="bounded intake classification and extraction",
    ),
    "local_policy_synthesis": LaneContract(
        lane_id="local_policy_synthesis",
        provider_id="local_policy_model_dry_run",
        max_complexity=7,
        cost_units=4.0,
        purpose="policy-grounded synthesis and review packet drafting",
    ),
    "hosted_fallback_dry_run": LaneContract(
        lane_id="hosted_fallback_dry_run",
        provider_id="hosted_reasoning_model_dry_run",
        max_complexity=10,
        cost_units=10.0,
        purpose="high-complexity synthesis fallback; no network call in this demo",
    ),
    "human_review_gate": LaneContract(
        lane_id="human_review_gate",
        provider_id="human_review_required",
        max_complexity=10,
        cost_units=2.0,
        purpose="policy-sensitive or unsafe requests stop before tool execution",
    ),
}


def estimate_complexity(request: str) -> int:
    text = request.lower()
    word_count = len(text.split())
    if any(term in text for term in ("complex", "multi-document", "multi document", "ambiguous", "unusual", "compare", "conflicting")):
        return 8
    if word_count >= 28:
        return 8
    if any(term in text for term in ("claim", "policy", "sop", "homeowners", "water")):
        return 5
    return 2


def classify_task(request: str) -> str:
    text = request.lower()
    if any(term in text for term in ("claim", "policy", "sop", "homeowners", "water")):
        return "claims_policy_review"
    if any(term in text for term in ("complex", "compare", "conflicting", "ambiguous")):
        return "complex_review"
    return "bounded_intake"


def _blocked_action(policy_gate: PolicyGateResult) -> str | None:
    if not policy_gate.blocks_tool_execution:
        return None
    priority = ("payment", "denial", "production_mutation", "approval")
    for category in priority:
        if category in policy_gate.categories:
            return category
    return "policy_sensitive_action"


def route_request(request: str, policy_gate: PolicyGateResult) -> dict[str, object]:
    task_class = classify_task(request)
    complexity = estimate_complexity(request)
    if policy_gate.blocks_tool_execution:
        lane = LANES["human_review_gate"]
        return {
            "task_class": task_class,
            "complexity": complexity,
            "selected_lane": lane.lane_id,
            "provider_id": lane.provider_id,
            "estimated_cost_units": lane.cost_units,
            "requires_human_gate": True,
            "blocked_action": _blocked_action(policy_gate),
            "failure_or_escalation_reason": policy_gate.reason,
            "routing_reason": "policy gate blocked tool execution before provider or tool work",
        }

    if complexity <= LANES["small_local_worker"].max_complexity:
        lane = LANES["small_local_worker"]
        reason = "bounded request fits local worker lane"
    elif complexity <= LANES["local_policy_synthesis"].max_complexity:
        lane = LANES["local_policy_synthesis"]
        reason = "policy review requires local synthesis lane"
    else:
        lane = LANES["hosted_fallback_dry_run"]
        reason = "high-complexity request exceeds local synthesis lane; hosted fallback is dry-run only"

    return {
        "task_class": task_class,
        "complexity": complexity,
        "selected_lane": lane.lane_id,
        "provider_id": lane.provider_id,
        "estimated_cost_units": lane.cost_units,
        "requires_human_gate": True,
        "blocked_action": None,
        "failure_or_escalation_reason": None,
        "routing_reason": reason,
    }


def apply_route_fields(target, route: dict[str, object]) -> None:
    for field in (
        "task_class",
        "complexity",
        "selected_lane",
        "provider_id",
        "estimated_cost_units",
        "requires_human_gate",
        "blocked_action",
        "failure_or_escalation_reason",
        "routing_reason",
    ):
        setattr(target, field, route[field])
