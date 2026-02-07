"""Async repository for all 7 tables. Thin persistence adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.domain.schemas import RunStatus

from .models import (
    DatasetCaseRow,
    DatasetRow,
    RunCaseStatusRow,
    RunEventRow,
    RunMessageRow,
    RunResultRow,
    RunRow,
)


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

    # ── Commit helper ────────────────────────────────────────────────────

    async def commit(self) -> None:
        await self._s.commit()
