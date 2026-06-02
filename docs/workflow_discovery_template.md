# Workflow Discovery Template

Use this template before proposing AI automation for an operational workflow. The goal is to identify where AI can safely assist, what must stay human-owned, and what evidence would prove the workflow is useful.

## 1. Workflow Frame

- Workflow name:
- Business owner:
- Technical owner:
- Primary users:
- Current trigger or intake channel:
- Current output or decision:

## 2. Business Problem

- What is slow, expensive, risky, or inconsistent today?
- What happens when the workflow fails?
- Who is affected by errors or delays?
- What would make the workflow meaningfully better?

## 3. Inputs And Source Systems

| Input/source | Owner | Access level | Freshness need | Failure mode |
|---|---|---|---|---|
| Example: policy/SOP doc | Operations | internal | current version required | stale guidance |

Questions:

- Which documents, tickets, records, databases, or APIs are required?
- Which sources are authoritative?
- Which sources are optional or supporting only?
- Which sources must never be exposed to the agent or role?

## 4. Actions And Boundaries

Allowed AI support work:

- retrieve relevant sources
- summarize bounded source material
- extract entities into a schema
- draft a review packet
- flag missing evidence or contradictions
- route to the right reviewer

Forbidden autonomous actions:

- final approval, denial, payment, or customer-impact action
- production mutation or deployment
- legal, medical, staffing, lending, or live-capital decision
- access to restricted context outside the role policy

Workflow-specific forbidden actions:

- 

## 5. Human Review Points

| Review point | Reviewer role | Required evidence | Approval outcome |
|---|---|---|---|
| Example: final packet review | operations reviewer | citations, eval report, risk flags | approve, reject, escalate |

Questions:

- Where do humans already review today?
- Which steps require more than one reviewer?
- What decisions can a reviewer approve, reject, or escalate?
- What should force a stop before tool execution?

## 6. Risk And Escalation Rules

Escalate or block when:

- evidence is missing, stale, or contradictory
- source retrieval fails
- a request asks for payment, denial, approval, or production mutation
- customer/legal/financial/medical/employment impact is possible
- the task exceeds the approved model lane or role policy
- output confidence is low or schema validation fails

Workflow-specific risk flags:

- 

## 7. Output Contract

Required artifact fields:

- summary
- entities
- timeline or relevant facts
- recommendation or review status
- citations/source IDs
- risk flags
- required human decision
- eval result
- routing decision and estimated cost

Schema or packet owner:

- 

## 8. Success Metrics

| Metric | Baseline | Target | Measurement source |
|---|---|---|---|
| Review prep time |  |  | run metrics / user study |
| Escalation correctness |  |  | reviewer disposition |
| Eval pass rate |  |  | eval artifacts |
| Cost units per run |  |  | routing metrics |

Candidate metrics:

- time saved per review packet
- fewer missed required sources
- fewer unsupported autonomous action attempts
- eval pass rate
- reviewer acceptance rate
- blocked unsafe request count
- cost units by lane
- human review latency

## 9. Pilot Scope

Start narrow:

- one workflow
- one user group
- one source set
- one packet schema
- one human approval path
- deterministic dry-run provider labels before live integrations

Pilot non-goals:

- autonomous final authority
- production mutation
- unrestricted source access
- broad cross-department rollout

## 10. Acceptance Criteria

The pilot is ready for broader review only when:

- required sources are retrieved or missing evidence is flagged
- outputs validate against the schema
- unsafe actions route to a human gate before tool execution
- run traces explain what happened and why
- metrics expose cost, eval result, blocked status, and review state
- human reviewers agree the packet is useful for the bounded workflow
