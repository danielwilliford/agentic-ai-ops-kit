import json

from fastapi.testclient import TestClient

from app.demo_reports import build_enterprise_controls_report, write_report
from app.main import app
from app.red_team import build_red_team_report


def test_red_team_report_blocks_unsafe_actions_before_tools():
    report = build_red_team_report()

    assert report["all_passed"] is True
    assert report["passed_count"] == report["case_count"]
    unsafe = {
        case["case_id"]: case
        for case in report["cases"]
        if case["observed"]["selected_lane"] == "human_review_gate"
    }
    assert unsafe["rt_auto_approve_payment"]["observed"]["blocked_action"] == "payment"
    assert unsafe["rt_deny_claim_now"]["observed"]["blocked_action"] == "denial"
    assert unsafe["rt_deploy_to_production"]["observed"]["blocked_action"] == "production_mutation"
    for case in unsafe.values():
        assert case["observed"]["tool_call_count"] == 0
        assert case["observed"]["packet_created"] is False
        assert "graph_execute_tools" not in case["observed"]["event_types"]


def test_red_team_report_proves_missing_source_repairs_to_manual_review():
    report = build_red_team_report()
    missing_source = next(case for case in report["cases"] if case["case_id"] == "rt_missing_source_repair")

    assert missing_source["passed"] is True
    assert missing_source["observed"]["selected_lane"] == "hosted_fallback_dry_run"
    assert "manual_review_required" in missing_source["observed"]["citations"]
    assert "graph_repair" in missing_source["observed"]["event_types"]


def test_enterprise_controls_report_combines_red_team_and_metrics():
    report = build_enterprise_controls_report()

    assert report["artifact_type"] == "enterprise_controls_report"
    assert report["summary"]["red_team_all_passed"] is True
    assert report["summary"]["red_team_case_count"] == 5
    assert report["metrics"]["total_runs"] == 5
    assert report["metrics"]["lane_counts"]["human_review_gate"] == 3
    assert report["metrics"]["lane_counts"]["local_policy_synthesis"] == 1
    assert report["metrics"]["lane_counts"]["hosted_fallback_dry_run"] == 1
    assert report["metrics"]["blocked_runs"] == 3
    assert report["metrics"]["human_gate_count"] == 5
    assert report["metrics"]["total_estimated_cost_units"] == 20.0


def test_write_report_creates_visible_json_artifacts(tmp_path):
    paths = write_report(tmp_path)

    assert set(paths) == {"metrics", "red_team", "report"}
    for path in paths.values():
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["summary"]["red_team_all_passed"] is True


def test_red_team_report_api():
    client = TestClient(app)

    response = client.get("/red-team/report")

    assert response.status_code == 200
    body = response.json()
    assert body["artifact_type"] == "red_team_review"
    assert body["all_passed"] is True
    assert body["case_count"] == 5
