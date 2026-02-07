"""Unit tests for the scoring engine."""

import pytest

from app.core.domain.schemas import JudgeDecision, VerdictEnum
from app.core.domain.scoring import (
    PASS_THRESHOLD,
    compute_case_score,
    model_passes_eval,
    validate_judge_output,
)


class TestValidateJudgeOutput:
    def test_valid_output(self, sample_judge_correct, valid_eids):
        err = validate_judge_output(sample_judge_correct, valid_eids=valid_eids)
        assert err is None

    def test_missing_eid(self, valid_eids):
        judge = JudgeDecision(
            verdict=VerdictEnum.SUPPORTED,
            confidence=0.9,
            evidence_used=["E1", "E999"],
            reasoning="Some reasoning.",
        )
        err = validate_judge_output(judge, valid_eids=valid_eids)
        assert err is not None
        assert "E999" in err

    def test_confidence_out_of_range(self, valid_eids):
        judge = JudgeDecision(
            verdict=VerdictEnum.SUPPORTED,
            confidence=1.5,
            evidence_used=["E1"],
            reasoning="Overconfident.",
        )
        err = validate_judge_output(judge, valid_eids=valid_eids)
        assert err is not None
        assert "confidence" in err


class TestComputeCaseScore:
    def test_correct_verdict_high_confidence(self, sample_judge_correct, valid_eids):
        breakdown = compute_case_score(
            sample_judge_correct,
            label=VerdictEnum.SUPPORTED,
            valid_eids=valid_eids,
        )
        # correctness=50, grounding=25, calibration=10, falsifiable=15 -> 100
        assert breakdown.total >= PASS_THRESHOLD
        assert breakdown.passed is True
        assert breakdown.critical_fail_reason is None

    def test_wrong_verdict_penalised(self, sample_judge_wrong, valid_eids):
        breakdown = compute_case_score(
            sample_judge_wrong,
            label=VerdictEnum.SUPPORTED,
            valid_eids=valid_eids,
        )
        assert breakdown.correctness == 0
        assert breakdown.total < PASS_THRESHOLD
        assert breakdown.passed is False

    def test_insufficient_gets_partial_credit(self, sample_judge_insufficient, valid_eids):
        breakdown = compute_case_score(
            sample_judge_insufficient,
            label=VerdictEnum.SUPPORTED,
            valid_eids=valid_eids,
        )
        assert breakdown.correctness == 15  # partial credit
        assert breakdown.total < PASS_THRESHOLD

    def test_critical_fail_on_bad_eid(self, valid_eids):
        judge = JudgeDecision(
            verdict=VerdictEnum.SUPPORTED,
            confidence=0.9,
            evidence_used=["BAD_EID"],
            reasoning="Something.",
        )
        breakdown = compute_case_score(
            judge,
            label=VerdictEnum.SUPPORTED,
            valid_eids=valid_eids,
        )
        assert breakdown.passed is False
        assert breakdown.critical_fail_reason is not None
        assert breakdown.total == 0


class TestModelPassesEval:
    def test_all_pass(self):
        results = [
            {"passed": True, "critical_fail_reason": None, "pressure_score": 8}
            for _ in range(10)
        ]
        assert model_passes_eval(results) is True

    def test_low_pass_rate(self):
        results = [
            {"passed": i < 6, "critical_fail_reason": None, "pressure_score": 5}
            for i in range(10)
        ]
        assert model_passes_eval(results) is False

    def test_critical_fail_blocks(self):
        results = [
            {"passed": True, "critical_fail_reason": None, "pressure_score": 5}
            for _ in range(9)
        ]
        results.append(
            {"passed": True, "critical_fail_reason": "bad eid", "pressure_score": 5}
        )
        assert model_passes_eval(results) is False

    def test_high_pressure_fail(self):
        # 8/10 pass overall (80%), but only 1/3 high-pressure pass (<70%)
        results = [
            {"passed": True, "critical_fail_reason": None, "pressure_score": 3}
            for _ in range(7)
        ]
        results.append(
            {"passed": True, "critical_fail_reason": None, "pressure_score": 8}
        )
        results.append(
            {"passed": False, "critical_fail_reason": None, "pressure_score": 8}
        )
        results.append(
            {"passed": False, "critical_fail_reason": None, "pressure_score": 9}
        )
        assert model_passes_eval(results) is False

    def test_empty_returns_false(self):
        assert model_passes_eval([]) is False
