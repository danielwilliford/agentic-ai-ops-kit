# Public Proof Map

This map ties the public enterprise-facing claims to the files, endpoints, schemas, and tests that prove them in the deterministic demo.

| Claim | Proof surface | Verification |
|---|---|---|
| The service exposes run traces for workflow observability. | `GET /runs/{run_id}/trace`; `RunManifest.trace`; LangGraph `graph_*` events. | `tests/test_workflow.py`, `tests/test_langgraph_workflow.py`, `tests/test_api.py` |
| Unsafe payment, denial, approval, and production mutation requests stop before tool execution. | `app/policy.py`; `app/langgraph_workflow.py`; `examples/enterprise_controls/red_team_review.json`. | `tests/test_langgraph_workflow.py`, `tests/test_red_team.py` |
| Review-packet requests remain pending human approval rather than taking final action. | `DecisionPacket.required_human_decision`; `RunStatus.PENDING_HUMAN_APPROVAL`; approval endpoint guard. | `tests/test_workflow.py`, `tests/test_api.py` |
| Cost-aware routing is exposed as dry-run metadata. | `app/routing.py`; run manifest fields `selected_lane`, `provider_id`, `estimated_cost_units`; `GET /metrics`. | `tests/test_routing.py`, `tests/test_api.py`, `tests/test_red_team.py` |
| Missing source coverage repairs to manual review rather than inventing citations. | `repair()` in `app/langgraph_workflow.py`; `manual_review_required` citation; red-team missing-source case. | `tests/test_langgraph_workflow.py`, `tests/test_red_team.py` |
| Aggregate AI-ops metrics are visible. | `app/metrics.py`; `GET /metrics`; `examples/enterprise_controls/metrics_summary.json`. | `tests/test_api.py`, `tests/test_red_team.py`, `tests/test_report_schemas.py` |
| Red-team/adversarial review is an artifact, not an interview claim only. | `app/red_team.py`; `GET /red-team/report`; `examples/enterprise_controls/red_team_review.json`. | `tests/test_red_team.py`, `tests/test_report_schemas.py` |
| Public report artifacts validate against explicit contracts. | `schemas/metrics_summary.json`; `schemas/red_team_review.json`; `schemas/enterprise_controls_report.json`. | `tests/test_report_schemas.py` |
| Workflow discovery is part of the implementation pattern. | `docs/workflow_discovery_template.md`. | Documented template with owners, sources, forbidden actions, review points, risk flags, output contracts, and success metrics. |
| Enterprise hardening gaps are named without overclaiming production readiness. | `docs/enterprise-hardening.md`. | Documents identity, durable audit storage, policy versioning, secrets, monitoring, retention, approval model, and public non-goals. |

## One-Command Proof

Run the verification suite:

```bash
make verify
```

Regenerate the visible control artifacts:

```bash
make reports
```

The generated files are:

- `examples/enterprise_controls/metrics_summary.json`
- `examples/enterprise_controls/red_team_review.json`
- `examples/enterprise_controls/enterprise_controls_report.json`
