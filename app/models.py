from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING_HUMAN_APPROVAL = "pending_human_approval"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class RunRequest(BaseModel):
    request: str = Field(..., min_length=10)


class RetrievedSource(BaseModel):
    source_id: str
    title: str
    excerpt: str
    score: float = Field(ge=0, le=1)


class ToolCall(BaseModel):
    name: str
    input: dict[str, Any]
    output: dict[str, Any]


class PolicyGateResult(BaseModel):
    status: RunStatus
    matched_terms: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    blocks_tool_execution: bool = False
    reason: str


class DecisionPacket(BaseModel):
    run_id: str
    role: str
    summary: str
    entities: dict[str, str]
    timeline: list[str]
    recommendation: str
    required_human_decision: bool = True
    citations: list[str]
    risk_flags: list[str]


class EvalResult(BaseModel):
    passed: bool
    score: int = Field(ge=0, le=100)
    checks: dict[str, bool]
    failures: list[str]


class TraceEvent(BaseModel):
    timestamp: str
    event_type: str
    detail: dict[str, Any]

    @classmethod
    def make(cls, event_type: str, detail: dict[str, Any]) -> "TraceEvent":
        return cls(timestamp=datetime.now(timezone.utc).isoformat(), event_type=event_type, detail=detail)


class RunManifest(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: RunStatus = RunStatus.PENDING_HUMAN_APPROVAL
    request: str
    packet: DecisionPacket | None = None
    eval: EvalResult | None = None
    policy_gate: PolicyGateResult | None = None
    retrieved_sources: list[RetrievedSource] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    human_decision: str | None = None


class ApprovalRequest(BaseModel):
    decision: RunStatus
    reviewer: str = "human_operator"
    notes: str = ""
