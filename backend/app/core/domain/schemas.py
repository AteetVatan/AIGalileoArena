"""Core domain schemas. Pure Pydantic v2 models, no IO dependencies."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class VerdictEnum(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INSUFFICIENT = "INSUFFICIENT"


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CaseStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventType(str, Enum):
    RUN_STARTED = "run_started"
    CASE_STARTED = "case_started"
    CASE_PHASE_STARTED = "case_phase_started"
    AGENT_MESSAGE = "agent_message"
    CASE_SCORED = "case_scored"
    METRICS_UPDATE = "metrics_update"
    RUN_FINISHED = "run_finished"


class DebateRole(str, Enum):
    ORTHODOX = "Orthodox"
    HERETIC = "Heretic"
    SKEPTIC = "Skeptic"
    JUDGE = "Judge"


# ── Evidence & Dataset ───────────────────────────────────────────────────────


class EvidencePacket(BaseModel):
    eid: str
    summary: str
    source: str
    date: str


class DatasetCaseSchema(BaseModel):
    case_id: str
    topic: str
    claim: str
    pressure_score: int = Field(ge=1, le=10)
    evidence_packets: list[EvidencePacket]
    label: VerdictEnum


class DatasetSchema(BaseModel):
    id: str
    version: str
    description: str
    meta: dict[str, Any] = Field(default_factory=dict)
    cases: list[DatasetCaseSchema]


# ── Model Config ─────────────────────────────────────────────────────────────


class ModelConfig(BaseModel):
    provider: str
    model_name: str
    api_key_env: str


# ── Run Request / Response ───────────────────────────────────────────────────


class RunRequest(BaseModel):
    dataset_id: str
    models: list[ModelConfig]
    max_cases: Optional[int] = None
    mode: str = "debate"


class RunResponse(BaseModel):
    run_id: str
    status: RunStatus


# ── Judge Structured Output ──────────────────────────────────────────────────


class JudgeDecision(BaseModel):
    """Schema the Judge agent must output as strict JSON."""

    verdict: VerdictEnum
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_used: list[str]
    reasoning: str


# ── Scoring Result ───────────────────────────────────────────────────────────


class CaseScoreBreakdown(BaseModel):
    correctness: int = Field(ge=0, le=50)
    grounding: int = Field(ge=0, le=25)
    calibration: int = Field(ge=0, le=10)
    falsifiable: int = Field(ge=0, le=15)
    total: int = Field(ge=0, le=100)
    passed: bool
    critical_fail_reason: Optional[str] = None


class CaseResult(BaseModel):
    run_id: str
    case_id: str
    model_key: str
    verdict: VerdictEnum
    label: VerdictEnum
    passed: bool
    score: int = Field(ge=0, le=100)
    confidence: float
    evidence_used: list[str]
    critical_fail_reason: Optional[str] = None
    latency_ms: int
    cost_estimate: float
    judge_json: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── SSE Event Payload ────────────────────────────────────────────────────────


class SSEEventPayload(BaseModel):
    run_id: str
    seq: int
    event_type: EventType
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Metrics / Summary ────────────────────────────────────────────────────────


class ModelMetrics(BaseModel):
    model_key: str
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    critical_fails: int = 0
    pass_rate: float = 0.0
    avg_score: float = 0.0
    avg_latency_ms: float = 0.0
    total_cost: float = 0.0
    high_pressure_pass_rate: float = 0.0
    model_passes_eval: bool = False


class RunSummary(BaseModel):
    run_id: str
    status: RunStatus
    total_cases: int
    models: list[ModelMetrics]
