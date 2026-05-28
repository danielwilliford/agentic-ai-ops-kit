# Agentic AI Ops Kit

A sanitized FastAPI and LangGraph workflow service for applied AI implementation roles.

The demo turns messy workflow intake into a controlled agentic service:

1. Resolve the workflow role.
2. Retrieve relevant policy and SOP context.
3. Run allowlisted local tools.
4. Build a structured Pydantic decision packet.
5. Evaluate citations, artifacts, and approval readiness.
6. Apply a policy gate for payment, approval, denial, and production-mutation language.
7. Pause at a human approval gate before any final action.

This repo is intentionally not a chatbot demo. It shows service boundaries, run state, traces, artifacts, eval gates, and approval controls that an implementation team can inspect.

## Stack

- Python
- FastAPI
- LangGraph StateGraph
- Pydantic
- pytest
- Docker

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
uvicorn app.main:app --reload --port 8080
```

Example request:

```bash
curl -s -X POST http://127.0.0.1:8080/runs/langgraph   -H 'content-type: application/json'   -d '{"request":"Review water damage claim CLM-1042 against the sample homeowners SOP and prepare a human approval packet."}'
```

## API

- `POST /runs` creates a deterministic baseline run.
- `POST /runs/langgraph` creates a LangGraph backed workflow run.
- `GET /runs/{run_id}` returns the run manifest.
- `GET /runs/{run_id}/trace` returns trace events.
- `GET /runs/{run_id}/artifacts` returns the decision packet, eval report, and retrieved sources.
- `POST /runs/{run_id}/approve` records a human review decision and refuses approval when no passing packet exists.
- `POST /evals/run` reruns eval checks for supplied packet data.

## Policy Gate

Requests containing payment, approval, denial, or production-mutation language are routed through a typed policy gate. High-risk requests such as `send payment`, `deny claim`, `approve without human`, or `deploy to production` stop before tool execution and return `human_review_required` with a policy-gate artifact explaining the matched terms and blocked action.

The service still allows safe review-packet creation when the request is explicitly framed as human review, but the resulting run remains pending human approval and has no autonomous mutation authority. The approval endpoint also refuses to approve any run that lacks a passing decision packet.

## Public Safety Boundary

This is a synthetic claims and policy workflow. It contains no private data, no production integrations, no finance strategy, no credentials, and no hidden mutation path.
