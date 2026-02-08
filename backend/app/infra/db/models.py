"""SQLAlchemy 2.x async ORM models."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.domain.schemas import RunStatus


class Base(DeclarativeBase):
    pass


# --- datasets ---

class DatasetRow(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    meta_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cases: Mapped[list["DatasetCaseRow"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetCaseRow(Base):
    __tablename__ = "dataset_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("datasets.id"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(128), nullable=False)
    topic: Mapped[str] = mapped_column(String(256), nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    pressure_score: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_json: Mapped[list] = mapped_column(JSON, nullable=False)
    safe_to_answer: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped["DatasetRow"] = relationship(back_populates="cases")

    __table_args__ = (
        Index("ix_dataset_cases_dataset_case", "dataset_id", "case_id"),
    )


# --- runs ---

class RunRow(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("datasets.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default=RunStatus.PENDING)
    models_json: Mapped[list] = mapped_column(JSON, nullable=False)
    case_id: Mapped[str] = mapped_column(String(128), nullable=False)
    scoring_mode: Mapped[str] = mapped_column(
        String(32), default="deterministic", server_default="deterministic"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    case_statuses: Mapped[list["RunCaseStatusRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    messages: Mapped[list["RunMessageRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    results: Mapped[list["RunResultRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    events: Mapped[list["RunEventRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RunCaseStatusRow(Base):
    __tablename__ = "run_case_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.run_id"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=RunStatus.PENDING)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    run: Mapped["RunRow"] = relationship(back_populates="case_statuses")

    __table_args__ = (
        Index("ix_rcs_run_case_model", "run_id", "case_id", "model_key"),
    )


# --- messages ---

class RunMessageRow(Base):
    __tablename__ = "run_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.run_id"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_key: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    phase: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    round: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["RunRow"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_rm_run_case", "run_id", "case_id"),
    )


# --- results ---

class RunResultRow(Base):
    __tablename__ = "run_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.run_id"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_key: Mapped[str] = mapped_column(String(128), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(32), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_used_json: Mapped[list] = mapped_column(JSON, nullable=False)
    critical_fail_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    judge_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["RunRow"] = relationship(back_populates="results")

    __table_args__ = (
        Index("ix_rr_run_model", "run_id", "model_key"),
    )


# --- events ---

class RunEventRow(Base):
    __tablename__ = "run_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.run_id"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["RunRow"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_re_run_seq", "run_id", "seq"),
    )


# --- cache slots ---

CACHE_SLOT_TTL = timedelta(hours=24)


def _default_expires_at() -> datetime:
    return datetime.utcnow() + CACHE_SLOT_TTL


class CachedResultSetRow(Base):
    __tablename__ = "cached_result_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("datasets.id"), nullable=False
    )
    model_key: Mapped[str] = mapped_column(String(128), nullable=False)
    case_id: Mapped[str] = mapped_column(String(128), nullable=False)
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.run_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=_default_expires_at)
    last_served_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "dataset_id", "model_key", "case_id", "slot_number",
            name="uq_cache_slot",
        ),
        Index("ix_cache_dataset_model_case_exp", "dataset_id", "model_key", "case_id", "expires_at"),
    )
