"""Run evaluation usecase -- orchestrate debate + scoring for a single case."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
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

    def __init__(self, session: AsyncSession, event_bus: EventBus) -> None:
        self._session = session
        self._repo = Repository(session)
        self._bus = event_bus

    async def execute(
        self, *,
        dataset_id: str,
        case_id: str,
        models: list[dict[str, str]],
        run_id: Optional[str] = None,
    ) -> str:
        if run_id is None:
            run_id = str(uuid.uuid4())

        models_json = [{"provider": m["provider"], "model_name": m["model_name"]} for m in models]

        # Record scoring mode for auditability / run comparison
        scoring_mode = "ml" if settings.ml_scoring_enabled else "deterministic"

        existing = await self._repo.get_run(run_id)
        if existing is None:
            await self._repo.create_run(
                run_id=run_id,
                dataset_id=dataset_id,
                case_id=case_id,
                models_json=models_json,
                scoring_mode=scoring_mode,
            )

        await self._repo.update_run_status(run_id, status=RunStatus.RUNNING)
        await self._repo.commit()

        await self._emit(run_id, EventType.RUN_STARTED, {
            "run_id": run_id, "dataset_id": dataset_id, "models": models_json,
        })

        try:
            case_row = await self._repo.get_dataset_case(dataset_id, case_id)
            if case_row is None:
                raise ValueError(f"Case {case_id} not found in dataset {dataset_id}")

            await self._emit(run_id, EventType.CASE_STARTED, {
                "case_id": case_row.case_id,
                "case_index": 0,
                "total_cases": 1,
                "topic": case_row.topic,
                "claim": case_row.claim,
                "pressure_score": case_row.pressure_score,
            })

            for model_cfg in models:
                model_key = f"{model_cfg['provider']}/{model_cfg['model_name']}"
                await self._run_case(
                    run_id=run_id, case_row=case_row,
                    model_cfg=model_cfg, model_key=model_key,
                )

            await self._emit(run_id, EventType.METRICS_UPDATE, {
                "completed": 1, "total": 1,
            })

            await self._repo.update_run_status(
                run_id, status=RunStatus.COMPLETED, finished_at=datetime.utcnow(),
            )
            await self._repo.commit()

            # register cache slot if enabled (single-model only)
            if settings.store_result and len(models) == 1:
                mk = f"{models[0]['provider']}/{models[0]['model_name']}"
                slot_num = await self._repo.get_next_empty_slot_number(
                    dataset_id, mk, case_id, max_slots=settings.cache_results,
                )
                if slot_num is not None:
                    await self._repo.create_cache_slot(
                        dataset_id=dataset_id, model_key=mk,
                        case_id=case_id, slot_number=slot_num,
                        source_run_id=run_id,
                    )
                    await self._repo.commit()

            await self._emit(run_id, EventType.RUN_FINISHED, {"run_id": run_id})

        except Exception as exc:
            logger.exception("Run %s failed", run_id)
            await self._repo.update_run_status(
                run_id, status=RunStatus.FAILED, finished_at=datetime.utcnow(),
            )
            await self._repo.commit()
            await self._emit(run_id, EventType.RUN_FINISHED, {
                "run_id": run_id, "error": str(exc),
            })

        return run_id

    async def _run_case(
        self, *, run_id: str, case_row: Any,
        model_cfg: dict[str, str], model_key: str,
    ) -> None:
        await self._repo.upsert_case_status(
            run_id=run_id, case_id=case_row.case_id,
            model_key=model_key, status=CaseStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        await self._repo.commit()

        try:
            llm = get_llm_client(
                provider=model_cfg["provider"],
                model_name=model_cfg["model_name"],
                api_key_env=model_cfg.get("api_key_env"),
            )

            if settings.use_autogen_debate:
                from app.infra.llm.autogen_model_client import GalileoModelClient
                from app.infra.debate.autogen_debate_flow import AutoGenDebateController

                autogen_client = GalileoModelClient(
                    llm,
                    model_name=model_cfg["model_name"],
                    provider=model_cfg["provider"],
                    enable_function_calling=settings.autogen_enable_tools,
                )
                controller = AutoGenDebateController(
                    autogen_client, model_key,
                    max_cross_exam_messages=settings.autogen_max_cross_exam_messages,
                    enable_tools=settings.autogen_enable_tools,
                )
            else:
                controller = DebateController(llm, model_key)

            async def on_msg(evt: MessageEvent) -> None:
                await self._repo.add_message(
                    run_id=run_id, case_id=evt.case_id,
                    model_key=model_key, role=evt.role,
                    content=evt.content, phase=evt.phase, round=evt.round,
                )
                await self._repo.commit()
                await self._emit(run_id, EventType.AGENT_MESSAGE, {
                    "case_id": evt.case_id, "model_key": model_key,
                    "role": evt.role, "phase": evt.phase,
                    "round": evt.round, "content": evt.content[:2000],
                })

            async def on_phase(evt: PhaseEvent) -> None:
                await self._emit(run_id, EventType.CASE_PHASE_STARTED, {
                    "case_id": evt.case_id, "model_key": model_key, "phase": evt.phase,
                })

            # LABEL ISOLATION: only case_id, claim, topic, and evidence are
            # passed to the debate controller.  Ground-truth label and
            # safe_to_answer are used ONLY at scoring time below.
            debate = await controller.run(
                case_id=case_row.case_id,
                claim=case_row.claim,
                topic=case_row.topic,
                evidence_packets=case_row.evidence_json,
                on_message=on_msg,
                on_phase=on_phase,
            )

            valid_eids = {ep["eid"] for ep in case_row.evidence_json}
            try:
                judge_decision = JudgeDecision(**debate.judge_json)
            except Exception:
                judge_decision = JudgeDecision(
                    verdict=VerdictEnum.INSUFFICIENT, confidence=0.0,
                    evidence_used=[], reasoning=FALLBACK_JUDGE_REASONING,
                )

            # NOTE: label is only used at scoring time -- the debate controller
            # never sees it, preserving label isolation.
            safe_flag = getattr(case_row, "safe_to_answer", True)

            # --- ML scoring (optional, non-blocking) ---
            ml_scores = None
            if settings.ml_scoring_enabled:
                from app.infra.ml.scorer import compute_ml_scores_async

                evidence_map = {
                    ep["eid"]: ep["summary"] for ep in case_row.evidence_json
                }
                ml_scores = await compute_ml_scores_async(
                    judge_decision.reasoning,
                    judge_decision.evidence_used,
                    evidence_map,
                )

            breakdown = compute_case_score(
                judge_decision,
                label=VerdictEnum(case_row.label),
                valid_eids=valid_eids,
                safe_to_answer=safe_flag if isinstance(safe_flag, bool) else True,
                ml_scores=ml_scores,
            )

            # Persist ML diagnostics in the existing judge_json column
            judge_json_out: dict[str, Any] = dict(debate.judge_json) if debate.judge_json else {}
            if ml_scores is not None:
                judge_json_out["ml_scores"] = asdict(ml_scores)
                judge_json_out["scoring_mode"] = "ml"
            else:
                judge_json_out["scoring_mode"] = "deterministic"

            await self._repo.add_result(
                run_id=run_id, case_id=case_row.case_id, model_key=model_key,
                verdict=judge_decision.verdict.value, label=case_row.label,
                passed=breakdown.passed, score=breakdown.total,
                confidence=judge_decision.confidence,
                evidence_used_json=judge_decision.evidence_used,
                critical_fail_reason=breakdown.critical_fail_reason,
                latency_ms=debate.total_latency_ms,
                cost_estimate=debate.total_cost,
                judge_json=judge_json_out,
            )
            await self._repo.commit()

            await self._emit(run_id, EventType.CASE_SCORED, {
                "case_id": case_row.case_id, "model_key": model_key,
                "score": breakdown.total, "passed": breakdown.passed,
                "verdict": judge_decision.verdict.value,
            })

        except Exception as exc:
            logger.error("case %s model %s blew up: %s", case_row.case_id, model_key, exc)
            # store a dummy result so the run can continue even if one case blows up
            await self._repo.add_result(
                run_id=run_id, case_id=case_row.case_id, model_key=model_key,
                verdict=VerdictEnum.INSUFFICIENT.value, label=case_row.label,
                passed=False, score=0, confidence=0.0,
                evidence_used_json=[], critical_fail_reason=str(exc),
                latency_ms=0, cost_estimate=0.0, judge_json={},
            )
            await self._repo.commit()

        finally:
            await self._repo.upsert_case_status(
                run_id=run_id, case_id=case_row.case_id,
                model_key=model_key, status=CaseStatus.COMPLETED,
                finished_at=datetime.utcnow(),
            )
            await self._repo.commit()

    async def _emit(self, run_id: str, event_type: str, payload: dict) -> None:
        await emit_and_persist(self._bus, self._repo, run_id, event_type, payload)
