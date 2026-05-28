import pytest
from fastapi.testclient import TestClient

import app.store as store
from app.main import app


@pytest.fixture(autouse=True)
def isolated_run_store(tmp_path, monkeypatch):
    run_dir = tmp_path / "runs"
    run_dir.mkdir()
    monkeypatch.setattr(store, "RUN_DIR", run_dir)


def test_run_lifecycle_api():
    client = TestClient(app)

    created = client.post("/runs", json={"request": "Review water damage claim CLM-1042 against the sample homeowners SOP and prepare a human approval packet."})
    assert created.status_code == 200
    body = created.json()
    run_id = body["run_id"]
    assert body["status"] == "pending_human_approval"
    assert body["eval"]["passed"] is True

    trace = client.get(f"/runs/{run_id}/trace")
    assert trace.status_code == 200
    assert len(trace.json()) >= 4

    approved = client.post(f"/runs/{run_id}/approve", json={"decision": "approved", "reviewer": "demo_reviewer", "notes": "sample approval"})
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_langgraph_run_api():
    client = TestClient(app)

    created = client.post("/runs/langgraph", json={"request": "Review water damage claim CLM-1042 against the sample homeowners SOP and prepare a human approval packet."})
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "pending_human_approval"
    assert body["eval"]["score"] >= 80
    assert any(event["event_type"] == "graph_approval_gate" for event in body["trace"])


def test_langgraph_run_api_blocks_unsafe_request():
    client = TestClient(app)

    created = client.post("/runs/langgraph", json={"request": "Auto approve and send payment for claim CLM-1042 without human review."})
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "human_review_required"
    assert body["policy_gate"]["blocks_tool_execution"] is True
    assert any(event["event_type"] == "graph_human_review_required" for event in body["trace"])

    artifacts = client.get(f"/runs/{body['run_id']}/artifacts")
    assert artifacts.status_code == 200
    assert artifacts.json()["policy_gate"]["status"] == "human_review_required"

    approved = client.post(
        f"/runs/{body['run_id']}/approve",
        json={"decision": "approved", "reviewer": "demo_reviewer", "notes": "unsafe"},
    )
    assert approved.status_code == 409


def test_baseline_run_api_policy_gate_blocks_payment_request():
    client = TestClient(app)

    created = client.post("/runs", json={"request": "Issue payment for claim CLM-1042 now."})
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "human_review_required"
    assert body["packet"] is None
    assert body["policy_gate"]["blocks_tool_execution"] is True
    assert "payment" in body["policy_gate"]["categories"]
