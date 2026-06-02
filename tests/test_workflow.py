from app.models import RunStatus
from app.tools import ALLOWED_TOOLS
from app.workflow import create_run


def test_create_run_returns_source_backed_packet_pending_human_approval():
    run = create_run("Review water damage claim CLM-1042 against the sample homeowners SOP and prepare a human approval packet.")

    assert run.status == RunStatus.PENDING_HUMAN_APPROVAL
    assert run.packet is not None
    assert run.packet.required_human_decision is True
    assert run.packet.entities["claim_id"] == "CLM-1042"
    assert run.packet.citations
    assert run.eval is not None
    assert run.eval.passed is True
    assert run.eval.score == 100
    assert run.selected_lane == "local_policy_synthesis"
    assert run.provider_id == "local_policy_model_dry_run"
    assert run.estimated_cost_units == 4.0
    assert run.requires_human_gate is True


def test_workflow_uses_only_allowlisted_tools():
    run = create_run("Review water damage claim CLM-1042 against the sample homeowners SOP.")

    assert run.tool_calls
    assert {call.name for call in run.tool_calls}.issubset(ALLOWED_TOOLS)


def test_trace_contains_retrieval_tool_and_eval_events():
    run = create_run("Review water damage claim CLM-1042 against the sample homeowners SOP.")
    event_types = [event.event_type for event in run.trace]

    assert "role_resolved" in event_types
    assert "retrieval_completed" in event_types
    assert "routing_completed" in event_types
    assert "allowlisted_tools_completed" in event_types
    assert "eval_completed" in event_types
