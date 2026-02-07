"""Run API routes – create, status, summary, cases, events (SSE)."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.domain.schemas import RunRequest, RunStatus
from app.infra.db.repository import Repository
from app.infra.sse.event_bus import event_bus
from app.usecases.compute_summary import compute_run_summary
from app.usecases.run_eval import RunEvalUsecase

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("")
async def create_run(
    body: RunRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Start a new evaluation run (async background task)."""
    repo = Repository(session)
    ds = await repo.get_dataset(body.dataset_id)
    if ds is None:
        raise HTTPException(404, "Dataset not found")

    usecase = RunEvalUsecase(session, event_bus)

    models = [m.model_dump() for m in body.models]

    # We need a fresh session for the background task
    from app.infra.db.session import async_session_factory

    bg_logger = logging.getLogger(__name__)

    async def _run():
        """Background task wrapper for evaluation run."""
        bg_logger.info(
            "Background task started: dataset_id=%s, models=%s, max_cases=%s",
            body.dataset_id,
            [m.get("model_name") for m in models],
            body.max_cases,
        )
        try:
            async with async_session_factory() as bg_session:
                uc = RunEvalUsecase(bg_session, event_bus)
                run_id = await uc.execute(
                    dataset_id=body.dataset_id,
                    models=models,
                    max_cases=body.max_cases,
                )
                bg_logger.info("Background task completed: run_id=%s", run_id)
        except Exception as exc:
            bg_logger.exception(
                "Background task failed: dataset_id=%s, error=%s",
                body.dataset_id, exc,
            )
            raise

    # create the run record synchronously so we can return the id
    import uuid

    run_id_preview = str(uuid.uuid4())
    # Actually let the usecase create it; we'll get the id back
    background_tasks.add_task(_run)

    return {"run_id": "starting", "status": RunStatus.PENDING.value, "message": "Run queued"}


@router.post("/start")
async def start_run_sync(
    body: RunRequest,
    session: AsyncSession = Depends(get_session),
):
    """Start run and return immediately with run_id (background execution)."""
    from app.infra.db.session import async_session_factory
    import asyncio

    models = [m.model_dump() for m in body.models]

    async def _run():
        async with async_session_factory() as bg_session:
            uc = RunEvalUsecase(bg_session, event_bus)
            return await uc.execute(
                dataset_id=body.dataset_id,
                models=models,
                max_cases=body.max_cases,
            )

    # Start as a fire-and-forget task
    task = asyncio.create_task(_run())

    # Give it a moment to create the run record
    await asyncio.sleep(0.2)

    return {"status": RunStatus.RUNNING.value, "message": "Run started in background"}


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    repo = Repository(session)
    run = await repo.get_run(run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    return {
        "run_id": run.run_id,
        "dataset_id": run.dataset_id,
        "status": run.status,
        "models": run.models_json,
        "max_cases": run.max_cases,
        "created_at": run.created_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/{run_id}/summary")
async def get_run_summary(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    summary = await compute_run_summary(session, run_id)
    return summary.model_dump()


@router.get("/{run_id}/cases")
async def get_run_cases(
    run_id: str,
    model: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    repo = Repository(session)
    results = await repo.get_run_results(run_id, model_key=model)

    if status == "pass":
        results = [r for r in results if r.passed]
    elif status == "fail":
        results = [r for r in results if not r.passed]

    total = len(results)
    page = results[skip : skip + limit]

    return {
        "total": total,
        "cases": [
            {
                "case_id": r.case_id,
                "model_key": r.model_key,
                "verdict": r.verdict,
                "label": r.label,
                "score": r.score,
                "passed": r.passed,
                "confidence": r.confidence,
                "latency_ms": r.latency_ms,
                "critical_fail_reason": r.critical_fail_reason,
            }
            for r in page
        ],
    }


@router.get("/{run_id}/cases/{case_id}")
async def get_case_replay(
    run_id: str,
    case_id: str,
    model: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    repo = Repository(session)
    messages = await repo.get_case_messages(run_id, case_id)
    results = await repo.get_run_results(run_id, case_id=case_id, model_key=model)

    if not results:
        raise HTTPException(404, "Case not found in this run")

    return {
        "case_id": case_id,
        "messages": [
            {
                "role": m.role,
                "model_key": m.model_key,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "results": [
            {
                "model_key": r.model_key,
                "verdict": r.verdict,
                "label": r.label,
                "score": r.score,
                "passed": r.passed,
                "confidence": r.confidence,
                "judge_json": r.judge_json,
                "critical_fail_reason": r.critical_fail_reason,
                "latency_ms": r.latency_ms,
                "cost_estimate": float(r.cost_estimate),
            }
            for r in results
        ],
    }


@router.get("/{run_id}/events")
async def stream_events(run_id: str):
    """SSE endpoint – streams live events for a run."""
    return StreamingResponse(
        event_bus.stream(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
