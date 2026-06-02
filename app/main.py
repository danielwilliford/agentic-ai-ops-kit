from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.langgraph_workflow import run_claim_review_graph
from app.metrics import summarize_runs
from app.models import ApprovalRequest, EvalResult, RunManifest, RunRequest, RunStatus
from app.red_team import build_red_team_report
from app.store import list_runs, load_run, save_run
from app.workflow import create_run, evaluate_packet

app = FastAPI(title="Agentic AI Ops Kit", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", response_model=RunManifest)
def post_run(payload: RunRequest) -> RunManifest:
    run = create_run(payload.request)
    save_run(run)
    return run


@app.post("/runs/langgraph", response_model=RunManifest)
def post_langgraph_run(payload: RunRequest) -> RunManifest:
    run = run_claim_review_graph(payload.request)
    save_run(run)
    return run


@app.get("/metrics")
def get_metrics():
    return summarize_runs(list_runs())


@app.get("/red-team/report")
def get_red_team_report():
    return build_red_team_report()


@app.get("/runs/{run_id}", response_model=RunManifest)
def get_run(run_id: str) -> RunManifest:
    try:
        return load_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="run not found")


@app.get("/runs/{run_id}/trace")
def get_trace(run_id: str):
    return get_run(run_id).trace


@app.get("/runs/{run_id}/artifacts")
def get_artifacts(run_id: str):
    run = get_run(run_id)
    return {
        "packet": run.packet,
        "eval": run.eval,
        "policy_gate": run.policy_gate,
        "retrieved_sources": run.retrieved_sources,
        "routing": {
            "task_class": run.task_class,
            "complexity": run.complexity,
            "selected_lane": run.selected_lane,
            "provider_id": run.provider_id,
            "estimated_cost_units": run.estimated_cost_units,
            "requires_human_gate": run.requires_human_gate,
            "blocked_action": run.blocked_action,
            "failure_or_escalation_reason": run.failure_or_escalation_reason,
            "routing_reason": run.routing_reason,
        },
    }


@app.post("/runs/{run_id}/approve", response_model=RunManifest)
def approve_run(run_id: str, payload: ApprovalRequest) -> RunManifest:
    if payload.decision not in {RunStatus.APPROVED, RunStatus.REJECTED, RunStatus.ESCALATED}:
        raise HTTPException(status_code=422, detail="decision must be approved, rejected, or escalated")
    run = get_run(run_id)
    if payload.decision == RunStatus.APPROVED and (run.packet is None or run.eval is None or not run.eval.passed):
        raise HTTPException(status_code=409, detail="cannot approve a run without a passing review packet")
    run.status = payload.decision
    run.human_decision = f"{payload.reviewer}: {payload.notes}"
    save_run(run)
    return run


@app.post("/evals/run", response_model=EvalResult)
def post_eval(packet: dict) -> EvalResult:
    from app.models import DecisionPacket

    return evaluate_packet(DecisionPacket.model_validate(packet))
