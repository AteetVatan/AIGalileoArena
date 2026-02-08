"""Async repository for all 8 tables. Thin persistence adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.domain.schemas import RunStatus

from .models import (
    CachedResultSetRow,
    DatasetCaseRow,
    DatasetRow,
    RunCaseStatusRow,
    RunEventRow,
    RunMessageRow,
    RunResultRow,
    RunRow,
)

logger = logging.getLogger(__name__)


class Repository:
    """Single repository covering all tables. Keeps the PoC simple."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Datasets ─────────────────────────────────────────────────────────

    async def dataset_exists(self, dataset_id: str) -> bool:
        stmt = select(DatasetRow.id).where(DatasetRow.id == dataset_id)
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_dataset(
        self,
        *,
        dataset_id: str,
        version: str,
        description: str,
        meta_json: dict,
    ) -> None:
        row = DatasetRow(
            id=dataset_id,
            version=version,
            description=description,
            meta_json=meta_json,
        )
        self._s.add(row)
        await self._s.flush()

    async def create_dataset_case(
        self,
        *,
        dataset_id: str,
        case_id: str,
        topic: str,
        claim: str,
        pressure_score: int,
        label: str,
        evidence_json: list[dict],
    ) -> None:
        row = DatasetCaseRow(
            dataset_id=dataset_id,
            case_id=case_id,
            topic=topic,
            claim=claim,
            pressure_score=pressure_score,
            label=label,
            evidence_json=evidence_json,
        )
        self._s.add(row)
        await self._s.flush()

    async def list_datasets(self) -> list[DatasetRow]:
        stmt = (
            select(DatasetRow)
            .order_by(DatasetRow.created_at.desc())
            .options(selectinload(DatasetRow.cases))
        )
        result = await self._s.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_dataset(self, dataset_id: str) -> Optional[DatasetRow]:
        stmt = (
            select(DatasetRow)
            .where(DatasetRow.id == dataset_id)
            .options(selectinload(DatasetRow.cases))
        )
        result = await self._s.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_dataset_cases(self, dataset_id: str) -> list[DatasetCaseRow]:
        stmt = (
            select(DatasetCaseRow)
            .where(DatasetCaseRow.dataset_id == dataset_id)
            .order_by(DatasetCaseRow.id)
        )
        result = await self._s.execute(stmt)
        return list(result.scalars().all())

    # ── Runs ─────────────────────────────────────────────────────────────

    async def create_run(
        self,
        *,
        run_id: str,
        dataset_id: str,
        models_json: list[dict],
        max_cases: Optional[int],
    ) -> None:
        row = RunRow(
            run_id=run_id,
            dataset_id=dataset_id,
            models_json=models_json,
            max_cases=max_cases,
            status=RunStatus.PENDING,
        )
        self._s.add(row)
        await self._s.flush()

    async def get_run(self, run_id: str) -> Optional[RunRow]:
        stmt = select(RunRow).where(RunRow.run_id == run_id)
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none()

    async def update_run_status(
        self,
        run_id: str,
        *,
        status: str,
        finished_at: Optional[datetime] = None,
    ) -> None:
        stmt = select(RunRow).where(RunRow.run_id == run_id)
        result = await self._s.execute(stmt)
        row = result.scalar_one()
        row.status = status
        if finished_at:
            row.finished_at = finished_at
        await self._s.flush()

    # ── Run Case Status ──────────────────────────────────────────────────

    async def upsert_case_status(
        self,
        *,
        run_id: str,
        case_id: str,
        model_key: str,
        status: str,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ) -> None:
        stmt = select(RunCaseStatusRow).where(
            and_(
                RunCaseStatusRow.run_id == run_id,
                RunCaseStatusRow.case_id == case_id,
                RunCaseStatusRow.model_key == model_key,
            )
        )
        result = await self._s.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = RunCaseStatusRow(
                run_id=run_id,
                case_id=case_id,
                model_key=model_key,
                status=status,
                started_at=started_at,
            )
            self._s.add(row)
        else:
            row.status = status
            if started_at:
                row.started_at = started_at
            if finished_at:
                row.finished_at = finished_at
        await self._s.flush()

    # ── Messages ─────────────────────────────────────────────────────────

    async def add_message(
        self,
        *,
        run_id: str,
        case_id: str,
        model_key: str,
        role: str,
        content: str,
        phase: Optional[str] = None,
        round: Optional[int] = None,
    ) -> None:
        row = RunMessageRow(
            run_id=run_id,
            case_id=case_id,
            model_key=model_key,
            role=role,
            content=content,
            phase=phase,
            round=round,
        )
        self._s.add(row)
        await self._s.flush()

    async def get_case_messages(
        self, run_id: str, case_id: str
    ) -> list[RunMessageRow]:
        stmt = (
            select(RunMessageRow)
            .where(
                and_(
                    RunMessageRow.run_id == run_id,
                    RunMessageRow.case_id == case_id,
                )
            )
            .order_by(RunMessageRow.created_at)
        )
        result = await self._s.execute(stmt)
        return list(result.scalars().all())

    # ── Results ──────────────────────────────────────────────────────────

    async def add_result(self, **kwargs) -> None:
        row = RunResultRow(**kwargs)
        self._s.add(row)
        await self._s.flush()

    async def get_run_results(
        self,
        run_id: str,
        *,
        model_key: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> list[RunResultRow]:
        conditions = [RunResultRow.run_id == run_id]
        if model_key:
            conditions.append(RunResultRow.model_key == model_key)
        if case_id:
            conditions.append(RunResultRow.case_id == case_id)
        stmt = (
            select(RunResultRow)
            .where(and_(*conditions))
            .order_by(RunResultRow.created_at)
        )
        result = await self._s.execute(stmt)
        return list(result.scalars().all())

    # ── Events (SSE) ─────────────────────────────────────────────────────

    async def add_event(
        self,
        *,
        run_id: str,
        seq: int,
        event_type: str,
        payload_json: dict,
    ) -> None:
        row = RunEventRow(
            run_id=run_id,
            seq=seq,
            event_type=event_type,
            payload_json=payload_json,
        )
        self._s.add(row)
        await self._s.flush()

    async def get_events_since(
        self, run_id: str, *, from_seq: int = 0, limit: int = 200
    ) -> list[RunEventRow]:
        stmt = (
            select(RunEventRow)
            .where(
                and_(
                    RunEventRow.run_id == run_id,
                    RunEventRow.seq > from_seq,
                )
            )
            .order_by(RunEventRow.seq)
            .limit(limit)
        )
        result = await self._s.execute(stmt)
        return list(result.scalars().all())

    async def get_max_event_seq(self, run_id: str) -> int:
        stmt = (
            select(RunEventRow.seq)
            .where(RunEventRow.run_id == run_id)
            .order_by(desc(RunEventRow.seq))
            .limit(1)
        )
        result = await self._s.execute(stmt)
        return result.scalar() or 0

    # ── Cached Result Sets ───────────────────────────────────────────────

    async def get_next_cache_slot_to_serve(
        self,
        dataset_id: str,
        model_key: str,
    ) -> Optional[CachedResultSetRow]:
        """Return the next valid (non-expired) slot to replay, round-robin."""
        now = datetime.utcnow()
        stmt = (
            select(CachedResultSetRow)
            .where(
                and_(
                    CachedResultSetRow.dataset_id == dataset_id,
                    CachedResultSetRow.model_key == model_key,
                    CachedResultSetRow.expires_at > now,
                )
            )
            .order_by(
                CachedResultSetRow.last_served_at.asc().nulls_first(),
                CachedResultSetRow.slot_number.asc(),
            )
            .limit(1)
        )
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_slot_served(self, slot_id: int) -> None:
        stmt = select(CachedResultSetRow).where(
            CachedResultSetRow.id == slot_id
        )
        result = await self._s.execute(stmt)
        row = result.scalar_one()
        row.last_served_at = datetime.utcnow()
        await self._s.flush()

    async def get_next_empty_slot_number(
        self,
        dataset_id: str,
        model_key: str,
        *,
        max_slots: int,
    ) -> Optional[int]:
        """Return the first slot number in 1..max_slots not occupied by a
        valid (non-expired) slot, or None if all are full."""
        now = datetime.utcnow()
        stmt = (
            select(CachedResultSetRow.slot_number)
            .where(
                and_(
                    CachedResultSetRow.dataset_id == dataset_id,
                    CachedResultSetRow.model_key == model_key,
                    CachedResultSetRow.expires_at > now,
                )
            )
        )
        result = await self._s.execute(stmt)
        occupied = {row for row in result.scalars().all()}
        for n in range(1, max_slots + 1):
            if n not in occupied:
                return n
        return None

    async def create_cache_slot(
        self,
        *,
        dataset_id: str,
        model_key: str,
        slot_number: int,
        source_run_id: str,
    ) -> bool:
        """Insert a cache slot. Returns True on success, False on conflict."""
        from .models import _default_expires_at

        row = CachedResultSetRow(
            dataset_id=dataset_id,
            model_key=model_key,
            slot_number=slot_number,
            source_run_id=source_run_id,
            expires_at=_default_expires_at(),
        )
        self._s.add(row)
        try:
            await self._s.flush()
            return True
        except IntegrityError:
            await self._s.rollback()
            logger.warning(
                "Cache slot conflict: dataset=%s model=%s slot=%d",
                dataset_id, model_key, slot_number,
            )
            return False

    async def delete_all_cache_slots(self) -> int:
        """Delete ALL cache slots (startup cleanup). Returns count deleted."""
        stmt = delete(CachedResultSetRow)
        result = await self._s.execute(stmt)
        await self._s.flush()
        return result.rowcount  # type: ignore[return-value]

    async def delete_expired_slots(self) -> int:
        """Delete expired cache slots. Returns count deleted."""
        now = datetime.utcnow()
        stmt = delete(CachedResultSetRow).where(
            CachedResultSetRow.expires_at <= now
        )
        result = await self._s.execute(stmt)
        await self._s.flush()
        return result.rowcount  # type: ignore[return-value]

    # ── Bulk queries (for replay) ─────────────────────────────────────────

    async def get_all_run_events(self, run_id: str) -> list[RunEventRow]:
        """All events for a run, ordered by seq (no limit)."""
        stmt = (
            select(RunEventRow)
            .where(RunEventRow.run_id == run_id)
            .order_by(RunEventRow.seq)
        )
        result = await self._s.execute(stmt)
        return list(result.scalars().all())

    async def get_all_run_messages(self, run_id: str) -> list[RunMessageRow]:
        """All messages for a run, ordered by id."""
        stmt = (
            select(RunMessageRow)
            .where(RunMessageRow.run_id == run_id)
            .order_by(RunMessageRow.id)
        )
        result = await self._s.execute(stmt)
        return list(result.scalars().all())

    async def get_all_run_results(self, run_id: str) -> list[RunResultRow]:
        """All results for a run, ordered by id."""
        stmt = (
            select(RunResultRow)
            .where(RunResultRow.run_id == run_id)
            .order_by(RunResultRow.id)
        )
        result = await self._s.execute(stmt)
        return list(result.scalars().all())

    # ── Commit helper ────────────────────────────────────────────────────

    async def commit(self) -> None:
        await self._s.commit()
