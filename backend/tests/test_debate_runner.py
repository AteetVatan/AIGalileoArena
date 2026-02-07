"""Unit tests for the multi-turn DebateController.

Tests:
1. Turn order matches FSM spec exactly.
2. Early-stop triggers when revisions converge.
3. Hard cap enforced (never exceeds max steps).
4. TOML validation retry on invalid first response.
5. EID constraint: missing EID proceeds safely to Judge.

All LLM mock responses use TOML format (the LLM interaction format).
Internal storage assertions use JSON (the internal storage format).
"""

from __future__ import annotations

import json
from typing import Any, Optional

import pytest
import tomli_w

from app.infra.debate.runner import DebateController, DebateMessage
from app.infra.debate.schemas import (
    DebatePhase,
    MessageEvent,
    PhaseEvent,
)
from app.infra.llm.base import LLMResponse


# ── Helpers ──────────────────────────────────────────────────────────────────

# Standard valid TOML payloads for each schema type


def _to_toml(data: dict) -> str:
    """Serialize a dict to a TOML string for mock LLM responses."""
    return tomli_w.dumps(data)


VALID_PROPOSAL = _to_toml({
    "proposed_verdict": "SUPPORTED",
    "evidence_used": ["E1", "E2"],
    "key_points": ["Evidence strongly supports claim"],
    "uncertainties": ["Sample size limited"],
    "what_would_change_my_mind": ["Counter-evidence from E3"],
})

VALID_PROPOSAL_REFUTED = _to_toml({
    "proposed_verdict": "REFUTED",
    "evidence_used": ["E2"],
    "key_points": ["Evidence contradicts claim"],
    "uncertainties": [],
    "what_would_change_my_mind": ["Additional supporting data"],
})

VALID_PROPOSAL_INSUFFICIENT = _to_toml({
    "proposed_verdict": "INSUFFICIENT",
    "evidence_used": ["E1"],
    "key_points": ["Not enough evidence to determine"],
    "uncertainties": ["Both sides have gaps"],
    "what_would_change_my_mind": ["More data points"],
})

VALID_QUESTIONS = _to_toml({
    "questions": [
        {"to": "Heretic", "q": "How do you reconcile E1?", "evidence_refs": ["E1"]},
        {"to": "Heretic", "q": "What about the date gap?", "evidence_refs": ["E2"]},
    ],
})

VALID_ANSWERS = _to_toml({
    "answers": [
        {"q": "How do you reconcile E1?", "a": "E1 is contextual", "evidence_refs": ["E1"], "admission": "none"},
        {"q": "What about the date gap?", "a": "Gap is not significant", "evidence_refs": ["E2"], "admission": "none"},
    ],
})

VALID_SKEPTIC_QUESTIONS = _to_toml({
    "questions": [
        {"to": "Both", "q": "Neither side addresses E3", "evidence_refs": ["E3"]},
        {"to": "Both", "q": "What is the confidence basis?", "evidence_refs": ["E1"]},
    ],
})

VALID_REVISION_AGREE = _to_toml({
    "final_proposed_verdict": "SUPPORTED",
    "evidence_used": ["E1", "E2"],
    "what_i_changed": [],
    "remaining_disagreements": [],
    "confidence": 0.9,
})

VALID_REVISION_DISAGREE = _to_toml({
    "final_proposed_verdict": "REFUTED",
    "evidence_used": ["E2"],
    "what_i_changed": ["Reconsidered E1"],
    "remaining_disagreements": ["Verdict still differs"],
    "confidence": 0.7,
})

VALID_DISPUTE_QUESTION = _to_toml({
    "questions": [{"q": "Final decisive question", "evidence_refs": ["E1"]}],
})

VALID_DISPUTE_ANSWER = _to_toml({
    "answers": [{"q": "Final decisive question", "a": "My final answer", "evidence_refs": ["E1"], "admission": "none"}],
})

# Judge still outputs TOML in the new protocol
VALID_JUDGE = _to_toml({
    "verdict": "SUPPORTED",
    "confidence": 0.88,
    "evidence_used": ["E1", "E2"],
    "reasoning": "Evidence E1 and E2 strongly support the claim, however sample size is limited.",
})

EVIDENCE_PACKETS = [
    {"eid": "E1", "summary": "Main evidence", "source": "Source A", "date": "2024-01-01"},
    {"eid": "E2", "summary": "Supporting evidence", "source": "Source B", "date": "2024-02-01"},
    {"eid": "E3", "summary": "Contradicting evidence", "source": "Source C", "date": "2024-03-01"},
]


class MockLLMClient:
    """Mock LLM that returns responses from a pre-configured sequence."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._call_index = 0
        self.call_log: list[str] = []

    async def complete(
        self,
        prompt: str,
        *,
        json_schema: Optional[dict[str, Any]] = None,
        temperature: float = 0.0,
        timeout: int = 60,
        retries: int = 3,
    ) -> LLMResponse:
        self.call_log.append(prompt[:80])
        if self._call_index < len(self._responses):
            text = self._responses[self._call_index]
        else:
            text = VALID_JUDGE  # fallback to judge output
        self._call_index += 1
        return LLMResponse(text=text, latency_ms=50, cost_estimate=0.001)

    @property
    def total_calls(self) -> int:
        return self._call_index


def _build_converging_responses() -> list[str]:
    """Build a response sequence where all agents converge (early-stop)."""
    return [
        # Phase 1: 3 proposals (all SUPPORTED)
        VALID_PROPOSAL,
        VALID_PROPOSAL,
        VALID_PROPOSAL,
        # Phase 2: 7 cross-exam steps
        VALID_QUESTIONS,   # 2A: Orthodox asks Heretic
        VALID_ANSWERS,     # 2B: Heretic answers
        VALID_QUESTIONS,   # 2C: Heretic asks Orthodox
        VALID_ANSWERS,     # 2D: Orthodox answers
        VALID_SKEPTIC_QUESTIONS,  # 2E: Skeptic asks Both
        VALID_ANSWERS,     # 2F: Orthodox answers Skeptic
        VALID_ANSWERS,     # 2G: Heretic answers Skeptic
        # Phase 3: 3 revisions (all agree -> early stop)
        VALID_REVISION_AGREE,
        VALID_REVISION_AGREE,
        VALID_REVISION_AGREE,
        # Phase 4: Judge (no dispute phase since early stop)
        VALID_JUDGE,
    ]


def _build_diverging_responses() -> list[str]:
    """Build a response sequence where agents diverge (dispute needed)."""
    return [
        # Phase 1: 3 proposals
        VALID_PROPOSAL,
        VALID_PROPOSAL_REFUTED,
        VALID_PROPOSAL_INSUFFICIENT,
        # Phase 2: 7 cross-exam steps
        VALID_QUESTIONS,
        VALID_ANSWERS,
        VALID_QUESTIONS,
        VALID_ANSWERS,
        VALID_SKEPTIC_QUESTIONS,
        VALID_ANSWERS,
        VALID_ANSWERS,
        # Phase 3: 3 revisions (disagreement persists)
        VALID_REVISION_AGREE,       # Orthodox: SUPPORTED
        VALID_REVISION_DISAGREE,    # Heretic: REFUTED
        VALID_REVISION_AGREE,       # Skeptic: SUPPORTED (but Heretic disagrees with strong counter)
        # Phase 3.5: Dispute (3 calls)
        VALID_DISPUTE_QUESTION,     # Skeptic question
        VALID_DISPUTE_ANSWER,       # Orthodox answer
        VALID_DISPUTE_ANSWER,       # Heretic answer
        # Phase 4: Judge
        VALID_JUDGE,
    ]


# ── Test 1: Turn order matches FSM spec ──────────────────────────────────────


@pytest.mark.asyncio
async def test_turn_order_converging():
    """Verify exact message sequence for converging debate (early-stop)."""
    mock_llm = MockLLMClient(_build_converging_responses())
    controller = DebateController(mock_llm, "test/model")

    phases_seen: list[str] = []
    messages_seen: list[tuple[str, str, int]] = []

    async def on_phase(evt: PhaseEvent) -> None:
        phases_seen.append(evt.phase)

    async def on_msg(evt: MessageEvent) -> None:
        messages_seen.append((evt.role, evt.phase, evt.round))

    result = await controller.run(
        case_id="T01",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
        on_message=on_msg,
        on_phase=on_phase,
    )

    # Verify phase order
    assert phases_seen == [
        "setup", "independent", "cross_exam", "revision", "judge",
    ], f"Phase order mismatch: {phases_seen}"

    # Verify message roles in order
    roles = [m[0] for m in messages_seen]
    expected_roles = [
        # Phase 1 (parallel, but emitted in order)
        "Orthodox", "Heretic", "Skeptic",
        # Phase 2 (7 steps)
        "Orthodox", "Heretic", "Heretic", "Orthodox",
        "Skeptic", "Orthodox", "Heretic",
        # Phase 3 (3 revisions)
        "Orthodox", "Heretic", "Skeptic",
        # Phase 4: Judge
        "Judge",
    ]
    assert roles == expected_roles, f"Role order mismatch: {roles}"

    # Verify judge output parsed correctly
    assert result.judge_json["verdict"] == "SUPPORTED"
    assert result.total_cost > 0


@pytest.mark.asyncio
async def test_turn_order_diverging():
    """Verify dispute phase is included when agents diverge."""
    mock_llm = MockLLMClient(_build_diverging_responses())
    controller = DebateController(mock_llm, "test/model")

    phases_seen: list[str] = []

    async def on_phase(evt: PhaseEvent) -> None:
        phases_seen.append(evt.phase)

    result = await controller.run(
        case_id="T02",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
        on_phase=on_phase,
    )

    # Dispute phase should be present
    assert "dispute" in phases_seen, f"Dispute missing: {phases_seen}"
    assert phases_seen == [
        "setup", "independent", "cross_exam", "revision", "dispute", "judge",
    ]

    assert result.judge_json["verdict"] == "SUPPORTED"


# ── Test 2: Early-stop when revisions converge ──────────────────────────────


@pytest.mark.asyncio
async def test_early_stop_convergence():
    """When all 3 agents agree with sufficient evidence overlap, skip dispute."""
    mock_llm = MockLLMClient(_build_converging_responses())
    controller = DebateController(
        mock_llm, "test/model", early_stop_jaccard=0.4,
    )

    phases_seen: list[str] = []

    async def on_phase(evt: PhaseEvent) -> None:
        phases_seen.append(evt.phase)

    await controller.run(
        case_id="T03",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
        on_phase=on_phase,
    )

    # Dispute phase should NOT be present
    assert "dispute" not in phases_seen
    # Total LLM calls: 3 proposals + 7 cross-exam + 3 revisions + 1 judge = 14
    assert mock_llm.total_calls == 14


# ── Test 3: Hard cap enforced ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hard_cap_max_calls():
    """Total calls never exceed expected maximum (with dispute)."""
    mock_llm = MockLLMClient(_build_diverging_responses())
    controller = DebateController(mock_llm, "test/model")

    await controller.run(
        case_id="T04",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
    )

    # Max calls: 3 + 7 + 3 + 3 (dispute) + 1 (judge) = 17
    assert mock_llm.total_calls <= 17, (
        f"Exceeded hard cap: {mock_llm.total_calls} calls"
    )


# ── Test 4: TOML validation retry ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_toml_retry_on_invalid_response():
    """If first LLM response is invalid TOML, retry once and use valid result."""
    responses = [
        # Phase 1: first Orthodox response is invalid, retry succeeds
        "This is not valid TOML at all! {{{",  # invalid -> triggers retry
        VALID_PROPOSAL,                         # retry succeeds
        VALID_PROPOSAL,                         # Heretic
        VALID_PROPOSAL,                         # Skeptic
        # Phase 2
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_SKEPTIC_QUESTIONS, VALID_ANSWERS, VALID_ANSWERS,
        # Phase 3
        VALID_REVISION_AGREE, VALID_REVISION_AGREE, VALID_REVISION_AGREE,
        # Phase 4
        VALID_JUDGE,
    ]
    mock_llm = MockLLMClient(responses)
    controller = DebateController(mock_llm, "test/model")

    result = await controller.run(
        case_id="T05",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
    )

    # Should have 1 extra call due to retry
    # 3 proposals (1 retry) + 7 cross-exam + 3 revisions + 1 judge = 15
    assert mock_llm.total_calls == 15

    # Result should still be valid
    assert result.judge_json["verdict"] == "SUPPORTED"

    # Check that Orthodox message is present (retry succeeded)
    orthodox_msgs = [m for m in result.messages if m.role == "Orthodox"]
    assert len(orthodox_msgs) > 0


@pytest.mark.asyncio
async def test_double_retry_falls_back():
    """If both attempts fail, fallback is used and debate continues."""
    responses = [
        # Phase 1: Orthodox fails twice, then fallback
        "not toml {{{",     # first attempt fails
        "still not toml {{",  # retry also fails -> fallback used
        VALID_PROPOSAL,     # Heretic
        VALID_PROPOSAL,     # Skeptic
        # Phase 2
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_SKEPTIC_QUESTIONS, VALID_ANSWERS, VALID_ANSWERS,
        # Phase 3
        VALID_REVISION_AGREE, VALID_REVISION_AGREE, VALID_REVISION_AGREE,
        # Phase 4
        VALID_JUDGE,
    ]
    mock_llm = MockLLMClient(responses)
    controller = DebateController(mock_llm, "test/model")

    result = await controller.run(
        case_id="T06",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
    )

    # Debate should still complete with fallback
    assert result.judge_json["verdict"] == "SUPPORTED"
    # Orthodox message should exist (fallback proposal used)
    orthodox_msgs = [
        m for m in result.messages
        if m.role == "Orthodox" and m.phase == DebatePhase.INDEPENDENT
    ]
    assert len(orthodox_msgs) == 1


# ── Test 5: EID constraint ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_eid_proceeds_to_judge():
    """If an agent cites a non-existent EID, debate continues to Judge safely."""
    proposal_with_bad_eid = _to_toml({
        "proposed_verdict": "SUPPORTED",
        "evidence_used": ["E1", "E999"],  # E999 doesn't exist
        "key_points": ["Evidence supports claim"],
        "uncertainties": [],
        "what_would_change_my_mind": [],
    })

    responses = [
        # Phase 1: Orthodox cites bad EID
        proposal_with_bad_eid,
        VALID_PROPOSAL,
        VALID_PROPOSAL,
        # Phase 2
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_SKEPTIC_QUESTIONS, VALID_ANSWERS, VALID_ANSWERS,
        # Phase 3
        VALID_REVISION_AGREE, VALID_REVISION_AGREE, VALID_REVISION_AGREE,
        # Phase 4
        VALID_JUDGE,
    ]
    mock_llm = MockLLMClient(responses)
    controller = DebateController(mock_llm, "test/model")

    result = await controller.run(
        case_id="T07",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
    )

    # Debate should complete successfully (EID validation is in scoring, not runner)
    assert result.judge_json["verdict"] == "SUPPORTED"
    assert len(result.messages) > 0

    # The bad EID should be in the Orthodox proposal message (stored as JSON)
    orthodox_msg = next(
        m for m in result.messages
        if m.role == "Orthodox" and m.phase == DebatePhase.INDEPENDENT
    )
    content = json.loads(orthodox_msg.content)
    assert "E999" in content["evidence_used"]


# ── Test: DebateMessage includes phase and round ─────────────────────────────


@pytest.mark.asyncio
async def test_messages_have_phase_and_round():
    """All debate messages must include phase and round metadata."""
    mock_llm = MockLLMClient(_build_converging_responses())
    controller = DebateController(mock_llm, "test/model")

    result = await controller.run(
        case_id="T08",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
    )

    for msg in result.messages:
        assert msg.phase != "", f"Message from {msg.role} has empty phase"
        assert msg.round > 0, f"Message from {msg.role} has round=0"


# ── Test: Early-stop Jaccard helper ──────────────────────────────────────────


def test_jaccard_calculation():
    """Verify Jaccard similarity calculation."""
    assert DebateController._jaccard([{"a", "b"}, {"b", "c"}]) == pytest.approx(1 / 3)
    assert DebateController._jaccard([{"a", "b"}, {"a", "b"}]) == pytest.approx(1.0)
    assert DebateController._jaccard([set(), set()]) == pytest.approx(0.0)
    assert DebateController._jaccard([{"a"}, {"b"}]) == pytest.approx(0.0)
    assert DebateController._jaccard([]) == pytest.approx(0.0)


# ── Test: Internal storage stays JSON ────────────────────────────────────────


@pytest.mark.asyncio
async def test_internal_storage_is_json():
    """DebateMessage.content should be JSON even though LLM speaks TOML."""
    mock_llm = MockLLMClient(_build_converging_responses())
    controller = DebateController(mock_llm, "test/model")

    result = await controller.run(
        case_id="T09",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
    )

    # All non-Judge messages should be valid JSON
    for msg in result.messages:
        if msg.role == "Judge":
            continue  # Judge raw text may be TOML
        parsed = json.loads(msg.content)  # should not raise
        assert isinstance(parsed, dict)


# ── Test: TOML fenced output parsed correctly ────────────────────────────────


@pytest.mark.asyncio
async def test_fenced_toml_output_parsed():
    """LLM wrapping response in ```toml fences should still parse."""
    fenced_proposal = f"```toml\n{VALID_PROPOSAL}```"
    responses = [
        fenced_proposal,   # Orthodox (fenced)
        VALID_PROPOSAL,    # Heretic
        VALID_PROPOSAL,    # Skeptic
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_QUESTIONS, VALID_ANSWERS,
        VALID_SKEPTIC_QUESTIONS, VALID_ANSWERS, VALID_ANSWERS,
        VALID_REVISION_AGREE, VALID_REVISION_AGREE, VALID_REVISION_AGREE,
        VALID_JUDGE,
    ]
    mock_llm = MockLLMClient(responses)
    controller = DebateController(mock_llm, "test/model")

    result = await controller.run(
        case_id="T10",
        claim="Test claim",
        topic="Test topic",
        evidence_packets=EVIDENCE_PACKETS,
    )

    # Should succeed without retry
    assert mock_llm.total_calls == 14
    assert result.judge_json["verdict"] == "SUPPORTED"
