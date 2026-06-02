from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

from langgraph.graph import END, StateGraph

from app.models import DecisionPacket, EvalResult, PolicyGateResult, RetrievedSource, RunManifest, RunStatus, ToolCall, TraceEvent
from app.policy import evaluate_policy_gate
from app.retrieval import retrieve
from app.routing import apply_route_fields, route_request
from app.tools import build_timeline, classify_risk, extract_entities
from app.workflow import evaluate_packet, resolve_role


class ClaimReviewState(TypedDict):
    run_id: str
    request: str
    trace: list[TraceEvent]
    role: NotRequired[str]
    status: NotRequired[str]
    policy_gate: NotRequired[PolicyGateResult]
    risk_flags: NotRequired[list[str]]
    retrieved_sources: NotRequired[list[RetrievedSource]]
    citations: NotRequired[list[str]]
    plan: NotRequired[list[str]]
    tool_calls: NotRequired[list[ToolCall]]
    packet: NotRequired[DecisionPacket]
    eval: NotRequired[EvalResult]
    repair_attempts: NotRequired[int]
    approval_status: NotRequired[str]
    route: NotRequired[dict[str, object]]


def _trace(state: ClaimReviewState, event_type: str, detail: dict) -> None:
    state.setdefault("trace", []).append(TraceEvent.make(event_type, detail))


def preflight(state: ClaimReviewState) -> ClaimReviewState:
    request = state["request"]
    flags = []
    policy_gate = evaluate_policy_gate(request)
    state["policy_gate"] = policy_gate
    route = route_request(request, policy_gate)
    state["route"] = route
    if policy_gate.categories:
        flags.append("policy_gate_human_review_required")
    if policy_gate.blocks_tool_execution:
        flags.append("blocked_external_or_irreversible_action_requested")
    if len(request.strip()) < 10:
        flags.append("request_too_short")
    state["risk_flags"] = flags
    state["role"] = resolve_role(request)
    state["status"] = (
        RunStatus.HUMAN_REVIEW_REQUIRED.value
        if policy_gate.blocks_tool_execution or "request_too_short" in flags
        else "preflight_passed"
    )
    _trace(
        state,
        "graph_policy_gate",
        policy_gate.model_dump(),
    )
    _trace(state, "graph_route", route)
    _trace(state, "graph_preflight", {"role": state["role"], "risk_flags": flags})
    return state


def route_after_preflight(state: ClaimReviewState) -> Literal["retrieve_context", "human_review_required"]:
    return (
        "human_review_required"
        if state.get("status") == RunStatus.HUMAN_REVIEW_REQUIRED.value
        else "retrieve_context"
    )


def human_review_required(state: ClaimReviewState) -> ClaimReviewState:
    state["approval_status"] = "human_review_required"
    state["status"] = RunStatus.HUMAN_REVIEW_REQUIRED.value
    _trace(
        state,
        "graph_human_review_required",
        {
            "risk_flags": state.get("risk_flags", []),
            "policy_gate": state["policy_gate"].model_dump(),
        },
    )
    return state


def retrieve_context(state: ClaimReviewState) -> ClaimReviewState:
    request_l = state["request"].lower()
    if not any(term in request_l for term in ("claim", "policy", "sop", "water", "homeowners")):
        sources = []
    else:
        sources = retrieve(state["request"])
    state["retrieved_sources"] = sources
    state["citations"] = [s.source_id for s in sources]
    _trace(state, "graph_retrieve_context", {"source_ids": state["citations"]})
    return state


def plan(state: ClaimReviewState) -> ClaimReviewState:
    state["plan"] = [
        "normalize request and resolve domain role",
        "retrieve relevant policy/SOP evidence",
        "run allowlisted extraction and risk tools",
        "draft structured decision packet",
        "evaluate citation/tool/approval coverage",
        "pause for human approval before any final action",
    ]
    _trace(state, "graph_plan", {"steps": len(state["plan"])})
    return state


def execute_tools(state: ClaimReviewState) -> ClaimReviewState:
    request = state["request"]
    citations = state.get("citations", [])
    calls = [
        extract_entities(request),
        build_timeline(request),
        classify_risk(request, citations),
    ]
    state["tool_calls"] = calls
    merged_flags = list(state.get("risk_flags", []))
    for call in calls:
        for flag in call.output.get("risk_flags", []):
            if flag not in merged_flags:
                merged_flags.append(flag)
    state["risk_flags"] = merged_flags
    _trace(state, "graph_execute_tools", {"tools": [c.name for c in calls], "risk_flags": merged_flags})
    return state


def draft_packet(state: ClaimReviewState) -> ClaimReviewState:
    entity_call = next(c for c in state["tool_calls"] if c.name == "extract_entities")
    timeline_call = next(c for c in state["tool_calls"] if c.name == "build_timeline")
    packet = DecisionPacket(
        run_id=state["run_id"],
        role=state["role"],
        summary="LangGraph workflow prepared a source-backed decision packet. Final action is blocked pending human approval.",
        entities=entity_call.output,
        timeline=timeline_call.output["timeline"],
        recommendation="Escalate to human reviewer with retrieved policy/SOP evidence before any final decision.",
        citations=state.get("citations", []),
        risk_flags=state.get("risk_flags", []) or ["requires_human_approval_before_action"],
    )
    state["packet"] = packet
    _trace(state, "graph_draft_packet", {"citations": packet.citations, "risk_flags": packet.risk_flags})
    return state


def evaluate(state: ClaimReviewState) -> ClaimReviewState:
    result = evaluate_packet(state["packet"])
    state["eval"] = result
    _trace(state, "graph_evaluate", result.model_dump())
    return state


def route_after_eval(state: ClaimReviewState) -> Literal["approval_gate", "repair", "blocked"]:
    if state["eval"].passed and state["eval"].score >= 80:
        return "approval_gate"
    if state.get("repair_attempts", 0) < 1:
        return "repair"
    return "blocked"


def repair(state: ClaimReviewState) -> ClaimReviewState:
    state["repair_attempts"] = state.get("repair_attempts", 0) + 1
    if not state.get("citations"):
        fallback = RetrievedSource(
            source_id="manual_review_required",
            title="Manual Review Required",
            excerpt="No policy/SOP source matched the request. Human reviewer must request additional documents before final decision.",
            score=0.0,
        )
        state["retrieved_sources"] = [fallback]
        state["citations"] = [fallback.source_id]
    flags = state.get("risk_flags", [])
    if "repaired_missing_citations_with_manual_review" not in flags:
        flags.append("repaired_missing_citations_with_manual_review")
    state["risk_flags"] = flags
    _trace(state, "graph_repair", {"repair_attempts": state["repair_attempts"], "citations": state.get("citations", [])})
    return state


def approval_gate(state: ClaimReviewState) -> ClaimReviewState:
    state["approval_status"] = "pending"
    state["status"] = RunStatus.PENDING_HUMAN_APPROVAL.value
    _trace(state, "graph_approval_gate", {"approval_status": "pending", "blocked_action": "final_claim_decision"})
    return state


def emit_artifacts(state: ClaimReviewState) -> ClaimReviewState:
    _trace(
        state,
        "graph_emit_artifacts",
        {
            "artifact_types": ["decision_packet", "eval_report", "trace"],
            "status": state.get("status"),
        },
    )
    return state


def build_claim_review_graph():
    graph = StateGraph(ClaimReviewState)
    graph.add_node("preflight", preflight)
    graph.add_node("human_review_required", human_review_required)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("plan", plan)
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("draft_packet", draft_packet)
    graph.add_node("evaluate", evaluate)
    graph.add_node("repair", repair)
    graph.add_node("approval_gate", approval_gate)
    graph.add_node("emit_artifacts", emit_artifacts)

    graph.set_entry_point("preflight")
    graph.add_conditional_edges("preflight", route_after_preflight, {"retrieve_context": "retrieve_context", "human_review_required": "human_review_required"})
    graph.add_edge("human_review_required", "emit_artifacts")
    graph.add_edge("retrieve_context", "plan")
    graph.add_edge("plan", "execute_tools")
    graph.add_edge("execute_tools", "draft_packet")
    graph.add_edge("draft_packet", "evaluate")
    graph.add_conditional_edges("evaluate", route_after_eval, {"approval_gate": "approval_gate", "repair": "repair", "blocked": "human_review_required"})
    graph.add_edge("repair", "draft_packet")
    graph.add_edge("approval_gate", "emit_artifacts")
    graph.add_edge("emit_artifacts", END)
    return graph.compile()


def run_claim_review_graph(request: str) -> RunManifest:
    manifest = RunManifest(request=request)
    initial: ClaimReviewState = {
        "run_id": manifest.run_id,
        "request": request,
        "repair_attempts": 0,
        "trace": [TraceEvent.make("graph_run_created", {"run_id": manifest.run_id})],
    }
    final = build_claim_review_graph().invoke(initial)
    if final.get("status") == RunStatus.PENDING_HUMAN_APPROVAL.value:
        manifest.status = RunStatus.PENDING_HUMAN_APPROVAL
    elif final.get("status") == RunStatus.HUMAN_REVIEW_REQUIRED.value:
        manifest.status = RunStatus.HUMAN_REVIEW_REQUIRED
    else:
        manifest.status = RunStatus.ESCALATED
    manifest.policy_gate = final.get("policy_gate")
    if "route" in final:
        apply_route_fields(manifest, final["route"])
    manifest.retrieved_sources = final.get("retrieved_sources", [])
    manifest.tool_calls = final.get("tool_calls", [])
    manifest.packet = final.get("packet")
    manifest.eval = final.get("eval")
    manifest.trace = final.get("trace", [])
    if final.get("status") == RunStatus.HUMAN_REVIEW_REQUIRED.value and manifest.packet is None:
        manifest.human_decision = "system: policy gate requires human review before tool execution"
    return manifest
