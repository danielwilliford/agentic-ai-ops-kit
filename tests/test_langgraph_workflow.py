from app.langgraph_workflow import build_claim_review_graph, run_claim_review_graph
from app.models import RunStatus
from app.tools import ALLOWED_TOOLS


def test_langgraph_good_claim_routes_to_human_approval():
    run = run_claim_review_graph(
        "Review water damage claim CLM-1042 against the sample homeowners SOP and prepare a human approval packet."
    )

    assert run.status == RunStatus.PENDING_HUMAN_APPROVAL
    assert run.packet is not None
    assert run.eval is not None
    assert run.eval.passed is True
    assert run.eval.score >= 80
    assert run.packet.required_human_decision is True
    assert run.packet.citations
    assert run.selected_lane == "local_policy_synthesis"
    assert run.estimated_cost_units == 4.0
    assert run.requires_human_gate is True


def test_langgraph_uses_allowlisted_tools_only():
    run = run_claim_review_graph("Review water damage claim CLM-1042 against the sample homeowners SOP.")

    assert run.tool_calls
    assert {call.name for call in run.tool_calls}.issubset(ALLOWED_TOOLS)


def test_langgraph_repairs_missing_citations_before_approval():
    run = run_claim_review_graph("Analyze an unusual mystery loss with no matching sample document and prepare review packet.")

    assert run.status == RunStatus.PENDING_HUMAN_APPROVAL
    assert run.packet is not None
    assert "manual_review_required" in run.packet.citations
    assert "repaired_missing_citations_with_manual_review" in run.packet.risk_flags
    event_types = [event.event_type for event in run.trace]
    assert "graph_repair" in event_types
    assert event_types.index("graph_repair") < event_types.index("graph_approval_gate")


def test_langgraph_blocks_unsafe_external_action_request():
    run = run_claim_review_graph("Auto approve and send payment for claim CLM-1042 without human review.")

    assert run.status == RunStatus.HUMAN_REVIEW_REQUIRED
    assert run.packet is None
    assert run.policy_gate is not None
    assert run.policy_gate.blocks_tool_execution is True
    assert run.selected_lane == "human_review_gate"
    assert run.provider_id == "human_review_required"
    assert run.blocked_action == "payment"
    assert run.failure_or_escalation_reason is not None
    assert run.human_decision == "system: policy gate requires human review before tool execution"
    event_types = [event.event_type for event in run.trace]
    assert "graph_policy_gate" in event_types
    assert "graph_human_review_required" in event_types
    assert "graph_execute_tools" not in event_types
    assert "graph_approval_gate" not in event_types


def test_langgraph_policy_gate_blocks_sensitive_mutation_phrases():
    examples = [
        ("Issue payment for claim CLM-1042 now.", "payment"),
        ("Deny claim CLM-1042 and close the file.", "denial"),
        ("Approve claim CLM-1042 without human review.", "approval"),
        ("Deploy this claim decision to production.", "production_mutation"),
    ]

    for request, category in examples:
        run = run_claim_review_graph(request)
        assert run.status == RunStatus.HUMAN_REVIEW_REQUIRED
        assert run.packet is None
        assert run.policy_gate is not None
        assert category in run.policy_gate.categories
        assert run.policy_gate.blocks_tool_execution is True
        assert not run.tool_calls


def test_langgraph_trace_contains_expected_node_sequence():
    run = run_claim_review_graph("Review water damage claim CLM-1042 against the sample homeowners SOP.")
    event_types = [event.event_type for event in run.trace]

    for expected in [
        "graph_run_created",
        "graph_preflight",
        "graph_route",
        "graph_retrieve_context",
        "graph_plan",
        "graph_execute_tools",
        "graph_draft_packet",
        "graph_evaluate",
        "graph_approval_gate",
        "graph_emit_artifacts",
    ]:
        assert expected in event_types


def test_langgraph_compiles_to_invokable_graph():
    graph = build_claim_review_graph()
    result = graph.invoke(
        {
            "run_id": "test-run",
            "request": "Review water damage claim CLM-1042 against the sample homeowners SOP.",
            "repair_attempts": 0,
            "trace": [],
        }
    )

    assert result["status"] == "pending_human_approval"
    assert result["eval"].score >= 80
