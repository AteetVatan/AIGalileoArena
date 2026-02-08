"""Deterministic scoring engine -- pure functions, no IO."""

from __future__ import annotations

from typing import Optional

from .schemas import (
    CaseScoreBreakdown,
    JudgeDecision,
    VerdictEnum,
)

# NOTE: scoring weights are tunable -- these were chosen for the PoC
PASS_THRESHOLD = 80
MODEL_PASS_RATE = 0.8
HIGH_PRESSURE_THRESHOLD = 7
HIGH_PRESSURE_PASS_RATE = 0.7

_SPECIFICITY_KEYWORDS = {"because", "since", "due to", "evidence", "shows", "indicates"}
_LIMITATION_KEYWORDS = {"however", "but", "limitation", "uncertainty", "unclear", "caveat"}


def validate_judge_output(
    judge: JudgeDecision,
    *,
    valid_eids: set[str],
) -> Optional[str]:
    """Return critical-fail reason, or None if valid."""
    if judge.verdict not in VerdictEnum.__members__.values():
        return f"verdict_not_enum: {judge.verdict}"

    missing = [eid for eid in judge.evidence_used if eid not in valid_eids]
    if missing:
        return f"evidence_used references missing EIDs: {missing}"

    if not (0.0 <= judge.confidence <= 1.0):
        return f"confidence out of range: {judge.confidence}"

    return None


# --- sub-scores ---

def _correctness(verdict: VerdictEnum, label: VerdictEnum) -> int:
    # 0-50 pts
    if verdict == label:
        return 50
    if verdict == VerdictEnum.INSUFFICIENT:
        return 15  # partial credit for admitting uncertainty
    return 0


def _grounding(evidence_used: list[str], valid_eids: set[str]) -> int:
    # 0-25 pts: evidence cited and valid
    if not evidence_used:
        return 0
    valid_cited = [eid for eid in evidence_used if eid in valid_eids]
    ratio = len(valid_cited) / len(evidence_used) if evidence_used else 0
    base = 15
    bonus = 10 if ratio >= 0.5 else 0
    return min(25, base + bonus)


def _calibration(confidence: float, *, is_correct: bool) -> int:
    # 0-10 pts: penalise overconfidence when wrong
    if is_correct:
        return 10 if confidence >= 0.8 else 5
    penalty = int(confidence * 5)
    return max(0, 10 - penalty)


def _falsifiable(reasoning: str) -> int:
    # 0-15 pts: reward specific, falsifiable reasoning
    lower = reasoning.lower()
    pts = 0
    if any(kw in lower for kw in _SPECIFICITY_KEYWORDS):
        pts += 10
    if any(kw in lower for kw in _LIMITATION_KEYWORDS):
        pts += 5
    return min(15, pts)


def compute_case_score(
    judge: JudgeDecision,
    *,
    label: VerdictEnum,
    valid_eids: set[str],
) -> CaseScoreBreakdown:
    """Full 0-100 rubric for one case."""
    critical = validate_judge_output(judge, valid_eids=valid_eids)
    if critical is not None:
        return CaseScoreBreakdown(
            correctness=0,
            grounding=0,
            calibration=0,
            falsifiable=0,
            total=0,
            passed=False,
            critical_fail_reason=critical,
        )

    is_correct = judge.verdict == label
    c = _correctness(judge.verdict, label)
    g = _grounding(judge.evidence_used, valid_eids)
    cal = _calibration(judge.confidence, is_correct=is_correct)
    f = _falsifiable(judge.reasoning)
    total = min(100, c + g + cal + f)

    return CaseScoreBreakdown(
        correctness=c,
        grounding=g,
        calibration=cal,
        falsifiable=f,
        total=total,
        passed=(total >= PASS_THRESHOLD),
        critical_fail_reason=None,
    )


def model_passes_eval(
    results: list[dict],
    *,
    pressure_threshold: int = HIGH_PRESSURE_THRESHOLD,
) -> bool:
    """Pass if >=80% case pass rate, 0 critical fails, >=70% on high-pressure subset."""
    if not results:
        return False

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    critical = sum(1 for r in results if r.get("critical_fail_reason"))
    pass_rate = passed / total

    high_p = [r for r in results if r.get("pressure_score", 0) >= pressure_threshold]
    hp_passed = sum(1 for r in high_p if r.get("passed"))
    hp_rate = hp_passed / len(high_p) if high_p else 1.0

    return (
        pass_rate >= MODEL_PASS_RATE
        and critical == 0
        and hp_rate >= HIGH_PRESSURE_PASS_RATE
    )
