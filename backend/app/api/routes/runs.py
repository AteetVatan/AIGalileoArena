"""Run API routes – create, status, summary, cases, events (SSE)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.core.domain.schemas import RunRequest, RunStatus
from app.infra.db.repository import Repository
from app.infra.sse.event_bus import event_bus
from app.usecases.compute_summary import compute_run_summary
from app.usecases.replay_cached import ReplayCachedUsecase
from app.usecases.run_eval import RunEvalUsecase

router = APIRouter(prefix="/runs", tags=["runs"])
_log = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _compute_total_cost(
    session: AsyncSession,
    run_id: str,
) -> float:
    """Compute total accumulated LLM cost for a run across all models and cases."""
    repo = Repository(session)
    results = await repo.get_run_results(run_id)
    total = sum(float(r.cost_estimate) for r in results)
    return round(total, 6)


async def _try_cache_slot(
    repo: Repository,
    dataset_id: str,
    models: list[dict],
) -> Optional[str]:
    """Check if a valid cache slot exists. Returns source_run_id or None.

    Only activates when STORE_RESULT=true and exactly 1 model is selected.
    """
    if not settings.store_result:
        return None
    if len(models) != 1:
        return None

    model_key = f"{models[0]['provider']}/{models[0]['model_name']}"
    slot = await repo.get_next_cache_slot_to_serve(dataset_id, model_key)
    if slot is None:
        return None

    # Validate the source run still exists and is completed
    source_run = await repo.get_run(slot.source_run_id)
    if source_run is None or source_run.status != RunStatus.COMPLETED:
        _log.warning(
            "Cache slot %d invalid (source=%s), skipping",
            slot.slot_number, slot.source_run_id,
        )
        return None

    await repo.mark_slot_served(slot.id)
    await repo.commit()
    return slot.source_run_id


# ── POST /runs ───────────────────────────────────────────────────────────────


@router.post("")
async def create_run(
    body: RunRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Start a new evaluation run (async background task)."""
    from app.infra.db.session import async_session_factory

    repo = Repository(session)
    ds = await repo.get_dataset(body.dataset_id)
    if ds is None:
        raise HTTPException(404, "Dataset not found")

    models = [m.model_dump() for m in body.models]
    effective_max_cases = settings.max_cases  # override frontend value

    run_id = str(uuid.uuid4())
    models_json = [
        {"provider": m["provider"], "model_name": m["model_name"]}
        for m in models
    ]
    await repo.create_run(
        run_id=run_id,
        dataset_id=body.dataset_id,
        models_json=models_json,
        max_cases=effective_max_cases,
    )
    await repo.commit()

    # ── Check cache ──────────────────────────────────────────────────
    source_run_id = await _try_cache_slot(repo, body.dataset_id, models)

    if source_run_id is not None:
        # Replay cached result
        _log.info(
            "Cache HIT: run_id=%s replaying source=%s", run_id, source_run_id,
        )

        async def _replay():
            async with async_session_factory() as bg_session:
                uc = ReplayCachedUsecase(
                    bg_session, event_bus,
                    run_id=run_id,
                    source_run_id=source_run_id,
                )
                await uc.execute()

        background_tasks.add_task(_replay)
    else:
        # Normal LLM path
        _log.info(
            "Cache MISS: run_id=%s, dataset=%s, models=%s, max_cases=%s",
            run_id, body.dataset_id,
            [m.get("model_name") for m in models],
            effective_max_cases,
        )

        async def _run():
            try:
                async with async_session_factory() as bg_session:
                    uc = RunEvalUsecase(bg_session, event_bus)
                    await uc.execute(
                        dataset_id=body.dataset_id,
                        models=models,
                        max_cases=effective_max_cases,
                        run_id=run_id,
                    )
                    _log.info("Background task completed: run_id=%s", run_id)
            except Exception as exc:
                _log.exception(
                    "Background task failed: run_id=%s error=%s",
                    run_id, exc,
                )
                raise

        background_tasks.add_task(_run)

    total_cost = await _compute_total_cost(session, run_id)
    return {
        "run_id": run_id,
        "status": RunStatus.PENDING.value,
        "message": "Run queued",
        "total_llm_cost": total_cost,
    }


# ── POST /runs/start ────────────────────────────────────────────────────────


@router.post("/start")
async def start_run_sync(
    body: RunRequest,
    session: AsyncSession = Depends(get_session),
):
    """Start run and return immediately with run_id (background execution)."""
    from app.infra.db.session import async_session_factory

    repo = Repository(session)
    ds = await repo.get_dataset(body.dataset_id)
    if ds is None:
        raise HTTPException(404, "Dataset not found")

    models = [m.model_dump() for m in body.models]
    effective_max_cases = settings.max_cases

    # Pre-create run record so we can return run_id immediately
    run_id = str(uuid.uuid4())
    models_json = [
        {"provider": m["provider"], "model_name": m["model_name"]}
        for m in models
    ]
    await repo.create_run(
        run_id=run_id,
        dataset_id=body.dataset_id,
        models_json=models_json,
        max_cases=effective_max_cases,
    )
    await repo.commit()

    # ── Check cache ──────────────────────────────────────────────────
    source_run_id = await _try_cache_slot(repo, body.dataset_id, models)

    if source_run_id is not None:
        _log.info(
            "Cache HIT: run_id=%s replaying source=%s", run_id, source_run_id,
        )

        async def _replay():
            async with async_session_factory() as bg_session:
                uc = ReplayCachedUsecase(
                    bg_session, event_bus,
                    run_id=run_id,
                    source_run_id=source_run_id,
                )
                await uc.execute()

        asyncio.create_task(_replay())
    else:
        _log.info(
            "Cache MISS: run_id=%s, dataset=%s, models=%s, max_cases=%s",
            run_id, body.dataset_id,
            [m.get("model_name") for m in models],
            effective_max_cases,
        )

        async def _run():
            async with async_session_factory() as bg_session:
                uc = RunEvalUsecase(bg_session, event_bus)
                await uc.execute(
                    dataset_id=body.dataset_id,
                    models=models,
                    max_cases=effective_max_cases,
                    run_id=run_id,
                )

        asyncio.create_task(_run())

    return {
        "run_id": run_id,
        "status": RunStatus.PENDING.value,
        "message": "Run started in background",
        "total_llm_cost": 0.0,
    }


# ── GET endpoints (unchanged) ───────────────────────────────────────────────


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    repo = Repository(session)
    run = await repo.get_run(run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    total_cost = await _compute_total_cost(session, run_id)
    return {
        "run_id": run.run_id,
        "dataset_id": run.dataset_id,
        "status": run.status,
        "models": run.models_json,
        "max_cases": run.max_cases,
        "created_at": run.created_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "total_llm_cost": total_cost,
        "debug_mode": settings.debug_mode,
    }


@router.get("/{run_id}/summary")
async def get_run_summary(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    summary = await compute_run_summary(session, run_id)
    total_cost = await _compute_total_cost(session, run_id)
    result = summary.model_dump()
    result["total_llm_cost"] = total_cost
    result["debug_mode"] = settings.debug_mode
    return result


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
    total_cost = await _compute_total_cost(session, run_id)

    return {
        "total": total,
        "total_llm_cost": total_cost,
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

    total_cost = await _compute_total_cost(session, run_id)

    return {
        "case_id": case_id,
        "total_llm_cost": total_cost,
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
