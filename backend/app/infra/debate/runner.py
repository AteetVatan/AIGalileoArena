"""Multi-turn debate controller – deterministic FSM-style orchestration.

Phases:
  0 – Moderator Setup (no LLM call)
  1 – Independent Proposals (3 parallel calls)
  2 – Cross-Examination (7 sequential calls)
  3 – Revision (3 calls + early-stop check)
  3.5 – Dispute Resolver (optional: 3 calls if no convergence)
  4 – Judge Finalization (1 call, TOML-based)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.domain.schemas import DebateRole, VerdictEnum
from app.infra.llm.base import BaseLLMClient

from .prompts import (
    case_packet_text,
    cross_exam_answer_prompt,
    cross_exam_question_prompt,
    cross_exam_question_skeptic_prompt,
    dispute_answer_prompt,
    dispute_question_prompt,
    format_evidence,
    judge_prompt,
    proposal_prompt,
    proposal_retry_prompt,
    revision_prompt,
    toml_retry_suffix,
)
from .schemas import (
    AdmissionLevel,
    AnswersMessage,
    DebatePhase,
    DebateTarget,
    DisputeAnswersMessage,
    DisputeQuestionsMessage,
    FALLBACK_ANSWER,
    FALLBACK_JUDGE_REASONING,
    FALLBACK_QUESTION,
    LogMessageType,
    MessageEvent,
    PhaseEvent,
    Proposal,
    Revision,
    QuestionsMessage,
    SharedMemo,
)
from .toml_serde import dict_to_toml, toml_to_dict

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class DebateMessage:
    """One agent message in the debate transcript."""

    role: str
    content: str
    phase: str = ""
    round: int = 0


@dataclass
class DebateResult:
    """Aggregate result from a full debate."""

    messages: list[DebateMessage] = field(default_factory=list)
    judge_json: dict[str, Any] = field(default_factory=dict)
    total_latency_ms: int = 0
    total_cost: float = 0.0


# ── Callback types ───────────────────────────────────────────────────────────

OnMessageCallback = Callable[[MessageEvent], Any]
OnPhaseCallback = Callable[[PhaseEvent], Any]

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_EARLY_STOP_JACCARD = 0.4
MAX_DISPUTE_STEPS = 1  # hard cap: only one dispute round ever


# ── Controller ───────────────────────────────────────────────────────────────


class DebateController:
    """Run a full multi-turn debate for one case + one model."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        model_key: str,
        *,
        early_stop_jaccard: float = DEFAULT_EARLY_STOP_JACCARD,
    ) -> None:
        self._llm = llm_client
        self._model_key = model_key
        self._early_stop_jaccard = early_stop_jaccard

    async def run(
        self,
        *,
        case_id: str,
        claim: str,
        topic: str,
        evidence_packets: list[dict],
        on_message: Optional[OnMessageCallback] = None,
        on_phase: Optional[OnPhaseCallback] = None,
    ) -> DebateResult:
        """Execute the full multi-turn debate protocol."""
        result = DebateResult()
        t0 = time.perf_counter()
        evidence_text = format_evidence(evidence_packets)
        case_pkt = case_packet_text(
            claim=claim, topic=topic, evidence_text=evidence_text,
        )
        valid_eids = {ep["eid"] for ep in evidence_packets}

        # ── Phase 0: Moderator Setup ─────────────────────────────────────
        await self._emit_phase(on_phase, case_id, DebatePhase.SETUP)

        # ── Phase 1: Independent Proposals ───────────────────────────────
        await self._emit_phase(on_phase, case_id, DebatePhase.INDEPENDENT)
        proposals = await self._phase_independent(
            case_id=case_id,
            case_pkt=case_pkt,
            result=result,
            on_message=on_message,
        )

        # ── Phase 2: Cross-Examination ───────────────────────────────────
        await self._emit_phase(on_phase, case_id, DebatePhase.CROSS_EXAM)
        cross_exam_log = await self._phase_cross_exam(
            case_id=case_id,
            case_pkt=case_pkt,
            proposals=proposals,
            result=result,
            on_message=on_message,
        )

        # ── Phase 3: Revision ────────────────────────────────────────────
        await self._emit_phase(on_phase, case_id, DebatePhase.REVISION)
        revisions, memo = await self._phase_revision(
            case_id=case_id,
            case_pkt=case_pkt,
            proposals=proposals,
            cross_exam_log=cross_exam_log,
            result=result,
            on_message=on_message,
        )

        # ── Early-stop check ─────────────────────────────────────────────
        if not self._should_early_stop(revisions):
            await self._emit_phase(
                on_phase, case_id, DebatePhase.DISPUTE,
            )
            await self._phase_dispute(
                case_id=case_id,
                case_pkt=case_pkt,
                revisions=revisions,
                memo=memo,
                result=result,
                on_message=on_message,
            )

        # ── Phase 4: Judge ───────────────────────────────────────────────
        await self._emit_phase(on_phase, case_id, DebatePhase.JUDGE)
        await self._phase_judge(
            case_id=case_id,
            claim=claim,
            topic=topic,
            evidence_text=evidence_text,
            result=result,
            on_message=on_message,
        )

        result.total_latency_ms = int((time.perf_counter() - t0) * 1000)
        logger.info(
            "Debate completed for case_id=%s, model=%s: total_cost=%.6f, latency_ms=%d",
            case_id,
            self._model_key,
            result.total_cost,
            result.total_latency_ms,
        )
        return result

    # ── Phase 1: Independent Proposals ───────────────────────────────────

    async def _phase_independent(
        self,
        *,
        case_id: str,
        case_pkt: str,
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
    ) -> dict[str, Proposal]:
        """3 parallel independent proposals."""
        roles = [DebateRole.ORTHODOX, DebateRole.HERETIC, DebateRole.SKEPTIC]

        async def _get_proposal(role: str) -> tuple[str, Proposal, float]:
            prompt = proposal_prompt(role=role, case_packet=case_pkt)
            parsed, raw, cost = await self._call_structured(
                prompt=prompt,
                schema_cls=Proposal,
                retry_prompt_fn=lambda bad: proposal_retry_prompt(
                    role=role, case_packet=case_pkt, failed_output=bad,
                ),
            )
            return role, parsed, cost

        tasks = [_get_proposal(r) for r in roles]
        results_list = await asyncio.gather(*tasks)

        proposals: dict[str, Proposal] = {}
        for role, parsed, cost in results_list:
            # Internal storage stays JSON
            raw_json = parsed.model_dump_json()
            proposals[role] = parsed
            result.total_cost += cost
            result.messages.append(
                DebateMessage(role, raw_json, DebatePhase.INDEPENDENT, 1),
            )
            await self._emit_msg(
                on_message, case_id, role, raw_json,
                DebatePhase.INDEPENDENT, 1,
            )

        return proposals

    # ── Phase 2: Cross-Examination ───────────────────────────────────────

    async def _phase_cross_exam(
        self,
        *,
        case_id: str,
        case_pkt: str,
        proposals: dict[str, Proposal],
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
    ) -> list[dict[str, Any]]:
        """7 sequential cross-exam exchanges."""
        log: list[dict[str, Any]] = []
        memo = self._build_memo_from_proposals(proposals)
        memo_text = memo.to_context_str()

        # TOML for prompt injection
        o_toml = _model_to_toml(proposals[DebateRole.ORTHODOX])
        h_toml = _model_to_toml(proposals[DebateRole.HERETIC])
        s_toml = _model_to_toml(proposals[DebateRole.SKEPTIC])

        step = 0
        _O = DebateRole.ORTHODOX.value
        _H = DebateRole.HERETIC.value
        _S = DebateRole.SKEPTIC.value
        _BOTH = DebateTarget.BOTH.value
        _Q = LogMessageType.QUESTIONS.value
        _A = LogMessageType.ANSWERS.value

        # 2A: Orthodox asks Heretic
        step += 1
        q_oh = await self._cross_exam_step(
            case_id=case_id, case_pkt=case_pkt,
            asker=_O, target=_H,
            asker_toml=o_toml, target_toml=h_toml,
            memo_text=memo_text, result=result,
            on_message=on_message, step=step,
        )
        log.append({"from": _O, "to": _H, "type": _Q, "data": q_oh})

        # 2B: Heretic answers
        step += 1
        a_ho = await self._answer_step(
            case_id=case_id, case_pkt=case_pkt,
            answerer=_H, questions_toml=q_oh,
            own_toml=h_toml, memo_text=memo_text,
            result=result, on_message=on_message, step=step,
        )
        log.append({"from": _H, "to": _O, "type": _A, "data": a_ho})

        # 2C: Heretic asks Orthodox
        step += 1
        q_ho = await self._cross_exam_step(
            case_id=case_id, case_pkt=case_pkt,
            asker=_H, target=_O,
            asker_toml=h_toml, target_toml=o_toml,
            memo_text=memo_text, result=result,
            on_message=on_message, step=step,
        )
        log.append({"from": _H, "to": _O, "type": _Q, "data": q_ho})

        # 2D: Orthodox answers
        step += 1
        a_oh = await self._answer_step(
            case_id=case_id, case_pkt=case_pkt,
            answerer=_O, questions_toml=q_ho,
            own_toml=o_toml, memo_text=memo_text,
            result=result, on_message=on_message, step=step,
        )
        log.append({"from": _O, "to": _H, "type": _A, "data": a_oh})

        # 2E: Skeptic asks Both
        step += 1
        q_sk = await self._skeptic_question_step(
            case_id=case_id, case_pkt=case_pkt,
            orthodox_toml=o_toml, heretic_toml=h_toml,
            memo_text=memo_text, result=result,
            on_message=on_message, step=step,
        )
        log.append({"from": _S, "to": _BOTH, "type": _Q, "data": q_sk})

        # 2F: Orthodox answers Skeptic
        step += 1
        a_os = await self._answer_step(
            case_id=case_id, case_pkt=case_pkt,
            answerer=_O, questions_toml=q_sk,
            own_toml=o_toml, memo_text=memo_text,
            result=result, on_message=on_message, step=step,
        )
        log.append({"from": _O, "to": _S, "type": _A, "data": a_os})

        # 2G: Heretic answers Skeptic
        step += 1
        a_hs = await self._answer_step(
            case_id=case_id, case_pkt=case_pkt,
            answerer=_H, questions_toml=q_sk,
            own_toml=h_toml, memo_text=memo_text,
            result=result, on_message=on_message, step=step,
        )
        log.append({"from": _H, "to": _S, "type": _A, "data": a_hs})

        return log

    async def _cross_exam_step(
        self,
        *,
        case_id: str,
        case_pkt: str,
        asker: str,
        target: str,
        asker_toml: str,
        target_toml: str,
        memo_text: str,
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
        step: int,
    ) -> str:
        """One cross-exam question step; returns TOML string for prompt reuse."""
        prompt = cross_exam_question_prompt(
            asker=asker, target=target,
            case_packet=case_pkt,
            asker_proposal_toml=asker_toml,
            target_proposal_toml=target_toml,
            memo_text=memo_text,
        )
        parsed, raw, cost = await self._call_structured(
            prompt=prompt,
            schema_cls=QuestionsMessage,
        )
        # Internal storage: JSON; prompt reuse: TOML
        raw_json = parsed.model_dump_json()
        result.total_cost += cost
        result.messages.append(
            DebateMessage(asker, raw_json, DebatePhase.CROSS_EXAM, step),
        )
        await self._emit_msg(
            on_message, case_id, asker, raw_json,
            DebatePhase.CROSS_EXAM, step,
        )
        return _model_to_toml(parsed)

    async def _skeptic_question_step(
        self,
        *,
        case_id: str,
        case_pkt: str,
        orthodox_toml: str,
        heretic_toml: str,
        memo_text: str,
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
        step: int,
    ) -> str:
        """Skeptic's gap-hunting questions to both sides."""
        prompt = cross_exam_question_skeptic_prompt(
            case_packet=case_pkt,
            orthodox_proposal_toml=orthodox_toml,
            heretic_proposal_toml=heretic_toml,
            memo_text=memo_text,
        )
        parsed, raw, cost = await self._call_structured(
            prompt=prompt,
            schema_cls=QuestionsMessage,
        )
        raw_json = parsed.model_dump_json()
        result.total_cost += cost
        result.messages.append(
            DebateMessage(DebateRole.SKEPTIC, raw_json, DebatePhase.CROSS_EXAM, step),
        )
        await self._emit_msg(
            on_message, case_id, DebateRole.SKEPTIC, raw_json,
            DebatePhase.CROSS_EXAM, step,
        )
        return _model_to_toml(parsed)

    async def _answer_step(
        self,
        *,
        case_id: str,
        case_pkt: str,
        answerer: str,
        questions_toml: str,
        own_toml: str,
        memo_text: str,
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
        step: int,
    ) -> str:
        """One cross-exam answer step; returns TOML string for prompt reuse."""
        prompt = cross_exam_answer_prompt(
            answerer=answerer,
            questions_toml=questions_toml,
            case_packet=case_pkt,
            own_proposal_toml=own_toml,
            memo_text=memo_text,
        )
        parsed, raw, cost = await self._call_structured(
            prompt=prompt,
            schema_cls=AnswersMessage,
        )
        raw_json = parsed.model_dump_json()
        result.total_cost += cost
        result.messages.append(
            DebateMessage(answerer, raw_json, DebatePhase.CROSS_EXAM, step),
        )
        await self._emit_msg(
            on_message, case_id, answerer, raw_json,
            DebatePhase.CROSS_EXAM, step,
        )
        return _model_to_toml(parsed)

    # ── Phase 3: Revision ────────────────────────────────────────────────

    async def _phase_revision(
        self,
        *,
        case_id: str,
        case_pkt: str,
        proposals: dict[str, Proposal],
        cross_exam_log: list[dict[str, Any]],
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
    ) -> tuple[dict[str, Revision], SharedMemo]:
        """3 revision calls after cross-examination."""
        cross_summary = dict_to_toml({"exchange": cross_exam_log})
        memo = self._build_memo_from_proposals(proposals)
        memo_text = memo.to_context_str()

        revisions: dict[str, Revision] = {}

        for idx, role in enumerate([DebateRole.ORTHODOX, DebateRole.HERETIC, DebateRole.SKEPTIC], 1):
            prompt = revision_prompt(
                role=role,
                case_packet=case_pkt,
                own_proposal_toml=_model_to_toml(proposals[role]),
                cross_exam_summary=cross_summary,
                memo_text=memo_text,
            )
            parsed, raw, cost = await self._call_structured(
                prompt=prompt,
                schema_cls=Revision,
            )
            raw_json = parsed.model_dump_json()
            revisions[role] = parsed
            result.total_cost += cost
            result.messages.append(
                DebateMessage(role, raw_json, DebatePhase.REVISION, idx),
            )
            await self._emit_msg(
                on_message, case_id, role, raw_json,
                DebatePhase.REVISION, idx,
            )

        # Update memo with revision data
        updated_memo = self._build_memo_from_revisions(revisions)
        return revisions, updated_memo

    # ── Phase 3.5: Dispute Resolver ──────────────────────────────────────

    async def _phase_dispute(
        self,
        *,
        case_id: str,
        case_pkt: str,
        revisions: dict[str, Revision],
        memo: SharedMemo,
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
    ) -> None:
        """Skeptic asks 1 decisive question, Orthodox + Heretic answer."""
        rev_summary = dict_to_toml(
            {r: v.model_dump() for r, v in revisions.items()},
        )
        memo_text = memo.to_context_str()

        # Skeptic question
        prompt_q = dispute_question_prompt(
            case_packet=case_pkt,
            revisions_summary=rev_summary,
            memo_text=memo_text,
        )
        q_parsed, _, cost_q = await self._call_structured(
            prompt=prompt_q,
            schema_cls=DisputeQuestionsMessage,
        )
        q_json = q_parsed.model_dump_json()
        q_toml = _model_to_toml(q_parsed)
        result.total_cost += cost_q
        result.messages.append(
            DebateMessage(DebateRole.SKEPTIC, q_json, DebatePhase.DISPUTE, 1),
        )
        await self._emit_msg(
            on_message, case_id, DebateRole.SKEPTIC, q_json,
            DebatePhase.DISPUTE, 1,
        )

        # Orthodox + Heretic answer
        for step, role in enumerate([DebateRole.ORTHODOX, DebateRole.HERETIC], 2):
            prompt_a = dispute_answer_prompt(
                answerer=role,
                case_packet=case_pkt,
                dispute_question_toml=q_toml,
                own_revision_toml=_model_to_toml(revisions[role]),
                memo_text=memo_text,
            )
            a_parsed, _, cost_a = await self._call_structured(
                prompt=prompt_a,
                schema_cls=DisputeAnswersMessage,
            )
            a_json = a_parsed.model_dump_json()
            result.total_cost += cost_a
            result.messages.append(
                DebateMessage(role, a_json, DebatePhase.DISPUTE, step),
            )
            await self._emit_msg(
                on_message, case_id, role, a_json,
                DebatePhase.DISPUTE, step,
            )

    # ── Phase 4: Judge ───────────────────────────────────────────────────

    async def _phase_judge(
        self,
        *,
        case_id: str,
        claim: str,
        topic: str,
        evidence_text: str,
        result: DebateResult,
        on_message: Optional[OnMessageCallback],
    ) -> None:
        """Judge finalization – TOML-based (no API-level schema enforcement)."""
        # Build structured transcript for judge
        structured = []
        for msg in result.messages:
            structured.append({
                "role": msg.role,
                "phase": msg.phase,
                "round": msg.round,
                "content": _safe_content_parse(msg.content),
            })

        prompt = judge_prompt(
            claim=claim,
            topic=topic,
            evidence_text=evidence_text,
            structured_debate=structured,
        )
        judge_resp = await self._llm.complete(
            prompt,
            temperature=0.0,
        )
        result.total_cost += judge_resp.cost_estimate
        result.messages.append(
            DebateMessage(DebateRole.JUDGE, judge_resp.text, DebatePhase.JUDGE, 1),
        )
        await self._emit_msg(
            on_message, case_id, DebateRole.JUDGE, judge_resp.text,
            DebatePhase.JUDGE, 1,
        )

        # Parse judge output (TOML-first with JSON fallback)
        result.judge_json = _parse_judge_output(judge_resp.text)

    # ── Early-stop logic ─────────────────────────────────────────────────

    def _should_early_stop(
        self,
        revisions: dict[str, Revision],
    ) -> bool:
        """Check if debate converged and dispute step can be skipped."""
        verdicts = {r: v.final_proposed_verdict for r, v in revisions.items()}
        unique_verdicts = set(verdicts.values())

        # All three agree
        if len(unique_verdicts) == 1:
            evidence_sets = [
                set(v.evidence_used) for v in revisions.values()
            ]
            if self._jaccard(evidence_sets) >= self._early_stop_jaccard:
                return True

        # Skeptic + one side agree, dissenter has only uncertainties
        skeptic_v = verdicts.get(DebateRole.SKEPTIC)
        for ally, dissenter in [
            (DebateRole.ORTHODOX, DebateRole.HERETIC),
            (DebateRole.HERETIC, DebateRole.ORTHODOX),
        ]:
            if verdicts.get(ally) == skeptic_v and verdicts.get(dissenter) != skeptic_v:
                d_rev = revisions[dissenter]
                has_no_strong_counter = (
                    len(d_rev.remaining_disagreements) == 0
                    or all(
                        "uncertain" in pt.lower()
                        for pt in d_rev.remaining_disagreements
                    )
                )
                if has_no_strong_counter:
                    return True

        return False

    @staticmethod
    def _jaccard(sets: list[set[str]]) -> float:
        """Jaccard similarity across all sets."""
        if not sets:
            return 0.0
        union = set().union(*sets)
        if not union:
            return 0.0
        intersection = sets[0].intersection(*sets[1:])
        return len(intersection) / len(union)

    # ── SharedMemo builders ──────────────────────────────────────────────

    @staticmethod
    def _build_memo_from_proposals(
        proposals: dict[str, Proposal],
    ) -> SharedMemo:
        """Build SharedMemo from Phase 1 proposals."""
        all_eids: set[str] = set()
        verdicts: dict[str, str] = {}
        contested: list[str] = []

        for role, p in proposals.items():
            all_eids.update(p.evidence_used)
            verdicts[role] = p.proposed_verdict

        unique_verdicts = set(verdicts.values())
        if len(unique_verdicts) > 1:
            contested.append(
                f"Verdict disagreement: {verdicts}"
            )

        return SharedMemo(
            all_evidence_cited=all_eids,
            verdicts_by_role=verdicts,
            contested_points=contested,
        )

    @staticmethod
    def _build_memo_from_revisions(
        revisions: dict[str, Revision],
    ) -> SharedMemo:
        """Build SharedMemo from Phase 3 revisions."""
        all_eids: set[str] = set()
        verdicts: dict[str, str] = {}
        contested: list[str] = []

        for role, r in revisions.items():
            all_eids.update(r.evidence_used)
            verdicts[role] = r.final_proposed_verdict
            contested.extend(r.remaining_disagreements)

        return SharedMemo(
            all_evidence_cited=all_eids,
            verdicts_by_role=verdicts,
            contested_points=contested,
        )

    # ── Structured LLM call with retry ───────────────────────────────────

    async def _call_structured(
        self,
        *,
        prompt: str,
        schema_cls: type[T],
        retry_prompt_fn: Optional[Callable[[str], str]] = None,
    ) -> tuple[T, str, float]:
        """Call LLM, validate TOML via Pydantic, retry once if invalid.

        Returns (parsed_object, raw_text, total_cost).
        """
        total_cost = 0.0

        resp = await self._llm.complete(prompt, temperature=0.3)
        total_cost += resp.cost_estimate
        raw = resp.text

        parsed = _try_parse(raw, schema_cls)
        if parsed is not None:
            return parsed, raw, total_cost

        # Retry once
        logger.warning(
            "TOML validation failed for %s, retrying. Raw: %s",
            schema_cls.__name__, raw[:200],
        )
        if retry_prompt_fn:
            retry_prompt = retry_prompt_fn(raw)
        else:
            retry_prompt = prompt + toml_retry_suffix(
                failed_output=raw,
                schema_hint=str(schema_cls.model_json_schema()),
            )

        resp2 = await self._llm.complete(retry_prompt, temperature=0.0)
        total_cost += resp2.cost_estimate
        raw2 = resp2.text

        parsed2 = _try_parse(raw2, schema_cls)
        if parsed2 is not None:
            return parsed2, raw2, total_cost

        # Return a default/fallback
        logger.error(
            "TOML validation failed after retry for %s. Using defaults.",
            schema_cls.__name__,
        )
        fallback = _build_fallback(schema_cls)
        return fallback, raw2, total_cost

    # ── Emit helpers ─────────────────────────────────────────────────────

    @staticmethod
    async def _emit_msg(
        cb: Optional[OnMessageCallback],
        case_id: str,
        role: str,
        content: str,
        phase: str | DebatePhase,
        round_num: int,
    ) -> None:
        """Emit a MessageEvent through the callback."""
        if cb is None:
            return
        phase_str = phase.value if isinstance(phase, DebatePhase) else phase
        evt = MessageEvent(
            case_id=case_id,
            role=role,
            content=content,
            phase=phase_str,
            round=round_num,
        )
        await _maybe_await(cb(evt))

    @staticmethod
    async def _emit_phase(
        cb: Optional[OnPhaseCallback],
        case_id: str,
        phase: DebatePhase,
    ) -> None:
        """Emit a PhaseEvent through the callback."""
        if cb is None:
            return
        evt = PhaseEvent(case_id=case_id, phase=phase.value)
        await _maybe_await(cb(evt))


# ── Module-level helpers ─────────────────────────────────────────────────────


def _model_to_toml(model: BaseModel) -> str:
    """Serialize a Pydantic model to TOML for prompt injection."""
    return dict_to_toml(model.model_dump())


def _try_parse(raw: str, schema_cls: type[T]) -> Optional[T]:
    """Try to parse raw text as TOML and validate against Pydantic schema."""
    try:
        data = toml_to_dict(raw)
        return schema_cls.model_validate(data)
    except (ValueError, ValidationError):
        pass

    return None


def _build_fallback(schema_cls: type[T]) -> T:
    """Build a safe fallback instance for any debate schema."""
    _insuf = VerdictEnum.INSUFFICIENT.value
    _both = DebateTarget.BOTH.value
    _adm_insuf = AdmissionLevel.INSUFFICIENT.value

    if schema_cls is Proposal:
        return schema_cls.model_validate({  # type: ignore[return-value]
            "proposed_verdict": _insuf,
            "evidence_used": [],
            "key_points": [FALLBACK_JUDGE_REASONING],
            "uncertainties": [],
            "what_would_change_my_mind": [],
        })
    if schema_cls is QuestionsMessage:
        return schema_cls.model_validate({  # type: ignore[return-value]
            "questions": [
                {"to": _both, "q": FALLBACK_QUESTION, "evidence_refs": []},
            ],
        })
    if schema_cls is AnswersMessage:
        return schema_cls.model_validate({  # type: ignore[return-value]
            "answers": [
                {"q": "?", "a": FALLBACK_ANSWER, "evidence_refs": [], "admission": _adm_insuf},
            ],
        })
    if schema_cls is Revision:
        return schema_cls.model_validate({  # type: ignore[return-value]
            "final_proposed_verdict": _insuf,
            "evidence_used": [],
            "what_i_changed": [],
            "remaining_disagreements": [],
            "confidence": 0.0,
        })
    if schema_cls is DisputeQuestionsMessage:
        return schema_cls.model_validate({  # type: ignore[return-value]
            "questions": [
                {"q": FALLBACK_QUESTION, "evidence_refs": []},
            ],
        })
    if schema_cls is DisputeAnswersMessage:
        return schema_cls.model_validate({  # type: ignore[return-value]
            "answers": [
                {"q": "?", "a": FALLBACK_ANSWER, "evidence_refs": [], "admission": _adm_insuf},
            ],
        })
    # Generic last resort – should not be reached
    raise ValueError(f"No fallback defined for {schema_cls.__name__}")


def _parse_judge_output(text: str) -> dict[str, Any]:
    """Parse judge output: try TOML first, then JSON fallback."""
    # TOML-first
    try:
        return toml_to_dict(text)
    except ValueError:
        pass

    # JSON fallback (in case LLM still returns JSON despite prompt)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                return _fallback_judge()
        return _fallback_judge()


def _fallback_judge() -> dict[str, Any]:
    """Fallback when judge output is unparseable."""
    return {
        "verdict": VerdictEnum.INSUFFICIENT.value,
        "confidence": 0.0,
        "evidence_used": [],
        "reasoning": FALLBACK_JUDGE_REASONING,
    }


def _safe_content_parse(text: str) -> Any:
    """Parse stored JSON content or return raw string."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


async def _maybe_await(val: Any) -> Any:
    """Await if coroutine, otherwise no-op."""
    if asyncio.iscoroutine(val) or asyncio.isfuture(val):
        return await val
    return val
