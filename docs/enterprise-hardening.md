# Enterprise Hardening Notes

This repo is a deterministic public proof of an AI workflow operating layer. It is not an enterprise deployment. This document names the production concerns that would need to be implemented before using the pattern inside a real organization.

## Current Public Proof

The public demo already shows:

- request intake through FastAPI
- LangGraph workflow execution
- policy gates for approval, denial, payment, and production mutation language
- allowlisted local tool calls
- retrieval of synthetic policy/SOP context
- structured decision packets
- eval checks
- red-team review artifacts
- run traces
- dry-run lane routing and estimated cost units
- aggregate metrics
- human approval endpoints that refuse invalid approval

## Required Enterprise Additions

### 1. Identity And Access

Add:

- SSO/OIDC authentication
- reviewer, operator, admin, and auditor roles
- tenant or business-unit boundaries
- per-workflow access policies
- least-privilege service accounts

The public demo has no authentication and should not be treated as access-controlled software.

### 2. Durable Audit Storage

Replace file-based run storage with durable event and artifact tables:

- runs
- trace events
- retrieved sources
- tool calls
- route decisions
- eval results
- red-team review results
- human decisions
- metrics snapshots

Each record should include a schema version, producer, timestamp, and immutable audit identifier.

### 3. Policy And Schema Versioning

Version the contracts that govern behavior:

- policy-gate term sets
- routing lane definitions
- tool allowlists
- packet schemas
- eval criteria
- red-team fixtures
- workflow discovery records

A reviewer should be able to answer: which policy version governed this run?

### 4. Secrets And Provider Integrations

Live model or provider integrations should remain behind adapters. Add:

- secret manager integration
- no secrets in run artifacts or traces
- provider timeout and retry rules
- fallback lanes
- explicit cost attribution
- provider failure telemetry

The public demo intentionally uses dry-run provider labels only.

### 5. Monitoring And Incident Handling

Expose operational signals:

- blocked unsafe request count
- eval pass/fail rates
- missing source and repair counts
- human review latency
- route/lane distribution
- estimated cost by lane and workflow
- tool failure rates
- policy-gate false positives and false negatives from reviewer feedback

Define incident paths for unsafe pass-through, missing audit records, provider failure, and unauthorized access attempts.

### 6. Data Retention And Privacy

Define retention rules for:

- raw requests
- retrieved sources
- packet artifacts
- reviewer notes
- traces
- metrics snapshots
- red-team reports

Add redaction and deletion workflows that preserve required audit evidence without leaking sensitive content.

### 7. Human Approval Model

Keep final authority explicit:

- high-impact final decisions remain human-owned unless formally approved by business, legal, compliance, product, and engineering owners
- approval packets should record reviewer identity, rationale, allowed next step, and rejected actions
- escalation should be available when evidence is missing, contradictory, stale, or outside policy

The agentic engineer owns the evaluation, observability, access-control, and escalation design. Business and risk owners still own policy approval.

## Production Non-Goals For This Public Demo

Do not add these to the public repo:

- real claims/customer data
- payment, denial, or customer communication integrations
- broker APIs or live-capital authority
- private research strategy logic
- production service topology
- credentials or secrets
- unrestricted tool access

## Enterprise Readiness Checklist

A real deployment should not proceed until:

- users and reviewer roles are authenticated
- every generated artifact validates against versioned schemas
- unsafe requests are blocked before tool/provider execution
- human approval state is durable and auditable
- metrics expose cost, quality, blocked actions, and review latency
- red-team fixtures pass for the workflow scope
- source access is permissioned and logged
- incident response and retention rules are documented
