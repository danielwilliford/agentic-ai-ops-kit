from __future__ import annotations

from app.models import DecisionPacket, EvalResult, RunManifest, RunStatus, TraceEvent
from app.policy import evaluate_policy_gate
from app.retrieval import retrieve
from app.tools import build_timeline, classify_risk, extract_entities


def resolve_role(request: str) -> str:
    text = request.lower()
    if "claim" in text or "policy" in text or "sop" in text:
        return "claims_policy_decision_operator"
    return "general_workflow_operator"


def create_run(request: str) -> RunManifest:
    manifest = RunManifest(request=request)
    manifest.trace.append(TraceEvent.make("run_created", {"run_id": manifest.run_id}))

    policy_gate = evaluate_policy_gate(request)
    manifest.policy_gate = policy_gate
    manifest.trace.append(TraceEvent.make("policy_gate_evaluated", policy_gate.model_dump()))
    if policy_gate.blocks_tool_execution:
        manifest.status = RunStatus.HUMAN_REVIEW_REQUIRED
        manifest.human_decision = "system: policy gate requires human review before tool execution"
        return manifest

    role = resolve_role(request)
    manifest.trace.append(TraceEvent.make("role_resolved", {"role": role}))

    sources = retrieve(request)
    manifest.retrieved_sources = sources
    manifest.trace.append(TraceEvent.make("retrieval_completed", {"source_ids": [s.source_id for s in sources]}))

    entity_call = extract_entities(request)
    timeline_call = build_timeline(request)
    citations = [s.source_id for s in sources]
    risk_call = classify_risk(request, citations)
    manifest.tool_calls = [entity_call, timeline_call, risk_call]
    manifest.trace.append(TraceEvent.make("allowlisted_tools_completed", {"tools": [c.name for c in manifest.tool_calls]}))

    packet = DecisionPacket(
        run_id=manifest.run_id,
        role=role,
        summary="Prepared a source-backed decision packet. Final action is blocked pending human approval.",
        entities=entity_call.output,
        timeline=timeline_call.output["timeline"],
        recommendation="Escalate to human reviewer with retrieved policy/SOP evidence before any final decision.",
        citations=citations,
        risk_flags=list(dict.fromkeys(risk_call.output["risk_flags"] + (["policy_gate_human_review_required"] if policy_gate.categories else []))),
    )
    manifest.packet = packet
    manifest.eval = evaluate_packet(packet)
    manifest.trace.append(TraceEvent.make("eval_completed", manifest.eval.model_dump()))
    return manifest


def evaluate_packet(packet: DecisionPacket) -> EvalResult:
    checks = {
        "requires_human_decision": packet.required_human_decision is True,
        "has_citations": len(packet.citations) > 0,
        "has_entities": bool(packet.entities),
        "has_timeline": len(packet.timeline) > 0,
        "has_recommendation": bool(packet.recommendation.strip()),
        "no_final_action_without_human": "pending human" in packet.summary.lower() or "human" in packet.recommendation.lower(),
    }
    failures = [name for name, passed in checks.items() if not passed]
    score = round(100 * sum(checks.values()) / len(checks))
    return EvalResult(passed=not failures, score=score, checks=checks, failures=failures)
