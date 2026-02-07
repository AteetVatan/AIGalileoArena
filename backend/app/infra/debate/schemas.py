"""Pydantic v2 models for intermediate multi-turn debate structures.

These are infra-only schemas used between debate phases.
The final Judge output still uses the core JudgeDecision schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── Phase Enum ────────────────────────────────────────────────────────────────


class DebatePhase(str, Enum):
    SETUP = "setup"
    INDEPENDENT = "independent"
    CROSS_EXAM = "cross_exam"
    REVISION = "revision"
    DISPUTE = "dispute"
    JUDGE = "judge"


VERDICT_LITERAL = Literal["SUPPORTED", "REFUTED", "INSUFFICIENT"]
ADMISSION_LITERAL = Literal["none", "insufficient", "uncertain"]
TARGET_LITERAL = Literal["Heretic", "Orthodox", "Both"]


# ── Phase 1: Independent Proposals ───────────────────────────────────────────


class Proposal(BaseModel):
    """Structured proposal from each debater in Phase 1."""

    proposed_verdict: VERDICT_LITERAL
    evidence_used: list[str] = Field(min_length=0)
    key_points: list[str] = Field(min_length=1)
    uncertainties: list[str] = Field(default_factory=list)
    what_would_change_my_mind: list[str] = Field(default_factory=list)


# ── Phase 2: Cross-Examination ───────────────────────────────────────────────


class Question(BaseModel):
    """Single cross-exam question."""

    to: TARGET_LITERAL
    q: str
    evidence_refs: list[str] = Field(default_factory=list)


class QuestionsMessage(BaseModel):
    """Wrapper for a list of cross-exam questions (exactly 2)."""

    questions: list[Question] = Field(min_length=1, max_length=2)


class Answer(BaseModel):
    """Single cross-exam answer."""

    q: str
    a: str
    evidence_refs: list[str] = Field(default_factory=list)
    admission: ADMISSION_LITERAL = "none"


class AnswersMessage(BaseModel):
    """Wrapper for a list of cross-exam answers."""

    answers: list[Answer] = Field(min_length=1, max_length=2)


# ── Phase 3: Revision ────────────────────────────────────────────────────────


class Revision(BaseModel):
    """Revised stance after seeing cross-examination results."""

    final_proposed_verdict: VERDICT_LITERAL
    evidence_used: list[str] = Field(min_length=0)
    what_i_changed: list[str] = Field(default_factory=list)
    remaining_disagreements: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


# ── Phase 3.5: Dispute Resolver ──────────────────────────────────────────────


class DisputeQuestion(BaseModel):
    """Single decisive question from Skeptic in dispute phase."""

    q: str
    evidence_refs: list[str] = Field(default_factory=list)


class DisputeQuestionsMessage(BaseModel):
    """Skeptic's final decisive question(s)."""

    questions: list[DisputeQuestion] = Field(min_length=1, max_length=1)


class DisputeAnswer(BaseModel):
    """Answer to dispute question."""

    q: str
    a: str
    evidence_refs: list[str] = Field(default_factory=list)
    admission: ADMISSION_LITERAL = "none"


class DisputeAnswersMessage(BaseModel):
    """Answers to dispute question."""

    answers: list[DisputeAnswer] = Field(min_length=1, max_length=1)


# ── Shared Memo (deterministic, no LLM call) ────────────────────────────────


@dataclass
class SharedMemo:
    """Deterministic context built from parsed debate objects."""

    all_evidence_cited: set[str]
    verdicts_by_role: dict[str, str]
    contested_points: list[str]

    def to_context_str(self) -> str:
        """Render as short context block for prompts."""
        lines = [
            "=== Shared Memo ===",
            f"Evidence cited so far: {sorted(self.all_evidence_cited)}",
            f"Current verdicts: {self.verdicts_by_role}",
        ]
        if self.contested_points:
            lines.append(
                f"Contested points: {self.contested_points[:5]}"
            )
        return "\n".join(lines)


# ── Callback Event Dataclasses ───────────────────────────────────────────────


@dataclass(frozen=True)
class MessageEvent:
    """Emitted per agent message for persistence + SSE."""

    case_id: str
    role: str
    content: str
    phase: str
    round: int


@dataclass(frozen=True)
class PhaseEvent:
    """Emitted when a debate phase starts."""

    case_id: str
    phase: str
