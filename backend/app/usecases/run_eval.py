"""Run evaluation usecase – orchestrates debate + scoring for all cases."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.schemas import (
    CaseStatus,
    EventType,
    JudgeDecision,
    RunStatus,
    VerdictEnum,
)
from app.core.domain.scoring import compute_case_score
from app.infra.db.repository import Repository
from app.infra.debate.runner import DebateController
from app.infra.debate.schemas import FALLBACK_JUDGE_REASONING, MessageEvent, PhaseEvent
from app.infra.llm.factory import get_llm_client
from app.config import settings
from app.infra.sse.event_bus import EventBus, emit_and_persist

logger = logging.getLogger(__name__)


class RunEvalUsecase:
    """Execute a full evaluation run: iterate models x cases, debate, score."""

    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus,
    ) -> None:
        self._session = session
        self._repo = Repository(session)
        self._bus = event_bus

    async def execute(
        self,
        *,
        dataset_id: str,
        models: list[dict[str, str]],
        max_cases: Optional[int] = None,
        run_id: Optional[str] = None,
    ) -> str:
        """Create run, process all cases, return run_id."""
        if run_id is None:
            run_id = str(uuid.uuid4())

        models_json = [
            {"provider": m["provider"], "model_name": m["model_name"]}
            for m in models
        ]
        
        # Only create run if it doesn't exist (when run_id was provided)
        existing_run = await self._repo.get_run(run_id)
        if existing_run is None:
            await self._repo.create_run(
                run_id=run_id,
                dataset_id=dataset_id,
                models_json=models_json,
                max_cases=max_cases,
            )
        
        await self._repo.update_run_status(run_id, status=RunStatus.RUNNING)
        await self._repo.commit()

        await self._emit(run_id, EventType.RUN_STARTED, {
            "run_id": run_id,
            "dataset_id": dataset_id,
            "models": models_json,
        })

        try:
            cases = await self._repo.get_dataset_cases(dataset_id)
            if max_cases:
                cases = cases[:max_cases]

            for case_idx, case_row in enumerate(cases):
                await self._emit(run_id, EventType.CASE_STARTED, {
                    "case_id": case_row.case_id,
                    "case_index": case_idx,
                    "total_cases": len(cases),
                    "topic": case_row.topic,
                    "claim": case_row.claim,
                    "pressure_score": case_row.pressure_score,
                })

                for model_cfg in models:
                    model_key = (
                        f"{model_cfg['provider']}/{model_cfg['model_name']}"
                    )
                    await self._run_case(
                        run_id=run_id,
                        case_row=case_row,
                        model_cfg=model_cfg,
                        model_key=model_key,
                    )

                # emit progress
                await self._emit(run_id, EventType.METRICS_UPDATE, {
                    "completed": case_idx + 1,
                    "total": len(cases),
                })

            await self._repo.update_run_status(
                run_id, status=RunStatus.COMPLETED, finished_at=datetime.utcnow()
            )
            await self._repo.commit()

            # Register cache slot if caching is enabled (single-model only)
            if settings.store_result and len(models) == 1:
                mk = f"{models[0]['provider']}/{models[0]['model_name']}"
                slot_num = await self._repo.get_next_empty_slot_number(
                    dataset_id, mk, max_slots=settings.cache_results,
                )
                if slot_num is not None:
                    await self._repo.create_cache_slot(
                        dataset_id=dataset_id,
                        model_key=mk,
                        slot_number=slot_num,
                        source_run_id=run_id,
                    )
                    await self._repo.commit()

            await self._emit(run_id, EventType.RUN_FINISHED, {"run_id": run_id})

        except Exception as exc:
            logger.exception("Run %s failed", run_id)
            await self._repo.update_run_status(
                run_id, status=RunStatus.FAILED, finished_at=datetime.utcnow()
            )
            await self._repo.commit()
            await self._emit(run_id, EventType.RUN_FINISHED, {
                "run_id": run_id, "error": str(exc),
            })

        return run_id

    # ── private ──────────────────────────────────────────────────────────

    async def _run_case(
        self,
        *,
        run_id: str,
        case_row: Any,
        model_cfg: dict[str, str],
        model_key: str,
    ) -> None:
        """Run debate + score for one case / one model."""
        await self._repo.upsert_case_status(
            run_id=run_id,
            case_id=case_row.case_id,
            model_key=model_key,
            status=CaseStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        await self._repo.commit()

        try:
            llm = get_llm_client(
                provider=model_cfg["provider"],
                model_name=model_cfg["model_name"],
                api_key_env=model_cfg.get("api_key_env"),
            )
            controller = DebateController(llm, model_key)

            async def on_msg(evt: MessageEvent) -> None:
                await self._repo.add_message(
                    run_id=run_id,
                    case_id=evt.case_id,
                    model_key=model_key,
                    role=evt.role,
                    content=evt.content,
                    phase=evt.phase,
                    round=evt.round,
                )
                await self._repo.commit()
                await self._emit(run_id, EventType.AGENT_MESSAGE, {
                    "case_id": evt.case_id,
                    "model_key": model_key,
                    "role": evt.role,
                    "phase": evt.phase,
                    "round": evt.round,
                    "content": evt.content[:500],
                })

            async def on_phase(evt: PhaseEvent) -> None:
                await self._emit(run_id, EventType.CASE_PHASE_STARTED, {
                    "case_id": evt.case_id,
                    "model_key": model_key,
                    "phase": evt.phase,
                })

            debate = await controller.run(
                case_id=case_row.case_id,
                claim=case_row.claim,
                topic=case_row.topic,
                evidence_packets=case_row.evidence_json,
                on_message=on_msg,
                on_phase=on_phase,
            )

            # Score
            valid_eids = {ep["eid"] for ep in case_row.evidence_json}
            try:
                judge_decision = JudgeDecision(**debate.judge_json)
            except Exception:
                judge_decision = JudgeDecision(
                    verdict=VerdictEnum.INSUFFICIENT,
                    confidence=0.0,
                    evidence_used=[],
                    reasoning=FALLBACK_JUDGE_REASONING,
                )

            breakdown = compute_case_score(
                judge_decision,
                label=VerdictEnum(case_row.label),
                valid_eids=valid_eids,
            )

            await self._repo.add_result(
                run_id=run_id,
                case_id=case_row.case_id,
                model_key=model_key,
                verdict=judge_decision.verdict.value,
                label=case_row.label,
                passed=breakdown.passed,
                score=breakdown.total,
                confidence=judge_decision.confidence,
                evidence_used_json=judge_decision.evidence_used,
                critical_fail_reason=breakdown.critical_fail_reason,
                latency_ms=debate.total_latency_ms,
                cost_estimate=debate.total_cost,
                judge_json=debate.judge_json,
            )
            await self._repo.commit()

            await self._emit(run_id, EventType.CASE_SCORED, {
                "case_id": case_row.case_id,
                "model_key": model_key,
                "score": breakdown.total,
                "passed": breakdown.passed,
                "verdict": judge_decision.verdict.value,
            })

        except Exception as exc:
            logger.error(
                "Case %s model %s failed: %s",
                case_row.case_id, model_key, exc,
            )
            # store a zero-score result so the run can continue
            await self._repo.add_result(
                run_id=run_id,
                case_id=case_row.case_id,
                model_key=model_key,
                verdict=VerdictEnum.INSUFFICIENT.value,
                label=case_row.label,
                passed=False,
                score=0,
                confidence=0.0,
                evidence_used_json=[],
                critical_fail_reason=str(exc),
                latency_ms=0,
                cost_estimate=0.0,
                judge_json={},
            )
            await self._repo.commit()

        finally:
            await self._repo.upsert_case_status(
                run_id=run_id,
                case_id=case_row.case_id,
                model_key=model_key,
                status=CaseStatus.COMPLETED,
                finished_at=datetime.utcnow(),
            )
            await self._repo.commit()

    async def _emit(
        self, run_id: str, event_type: str, payload: dict
    ) -> None:
        await emit_and_persist(
            self._bus, self._repo, run_id, event_type, payload,
        )
