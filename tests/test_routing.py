from app.policy import evaluate_policy_gate
from app.routing import route_request


def test_bounded_intake_routes_to_small_local_worker():
    route = route_request("Classify intake ticket TCK-1001.", evaluate_policy_gate("Classify intake ticket TCK-1001."))

    assert route["selected_lane"] == "small_local_worker"
    assert route["provider_id"] == "local_small_worker_dry_run"
    assert route["estimated_cost_units"] == 1.0
    assert route["requires_human_gate"] is True


def test_complex_review_routes_to_hosted_fallback_dry_run():
    request = "Compare a complex multi document claim with conflicting policy evidence and prepare review notes."
    route = route_request(request, evaluate_policy_gate(request))

    assert route["selected_lane"] == "hosted_fallback_dry_run"
    assert route["provider_id"] == "hosted_reasoning_model_dry_run"
    assert route["estimated_cost_units"] == 10.0


def test_payment_request_routes_to_human_gate_before_tools():
    request = "Issue payment for claim CLM-1042 now."
    route = route_request(request, evaluate_policy_gate(request))

    assert route["selected_lane"] == "human_review_gate"
    assert route["provider_id"] == "human_review_required"
    assert route["blocked_action"] == "payment"
    assert route["failure_or_escalation_reason"] is not None
