"""Unit tests for TOML serialization/deserialization utilities.

Covers:
  - Round-trip for every Pydantic debate schema shape.
  - Markdown fence stripping (```toml ... ```).
  - Extraction of TOML from mixed LLM output.
  - Edge cases: empty arrays, special characters, float precision.
"""

from __future__ import annotations

import tomllib

import pytest
import tomli_w

from app.infra.debate.toml_serde import dict_to_toml, toml_to_dict


# ── Round-trip tests for each schema shape ───────────────────────────────────


class TestRoundTripProposal:
    """Proposal: flat keys with string/list[str] fields."""

    PROPOSAL = {
        "proposed_verdict": "SUPPORTED",
        "evidence_used": ["E1", "E2"],
        "key_points": ["Evidence strongly supports claim"],
        "uncertainties": ["Sample size limited"],
        "what_would_change_my_mind": ["Counter-evidence from E3"],
    }

    def test_round_trip(self):
        toml_str = dict_to_toml(self.PROPOSAL)
        result = toml_to_dict(toml_str)
        assert result == self.PROPOSAL

    def test_toml_output_is_valid(self):
        toml_str = dict_to_toml(self.PROPOSAL)
        # Must parse without error via stdlib
        parsed = tomllib.loads(toml_str)
        assert parsed["proposed_verdict"] == "SUPPORTED"


class TestRoundTripQuestionsMessage:
    """QuestionsMessage: array-of-tables ([[questions]])."""

    QUESTIONS = {
        "questions": [
            {"to": "Heretic", "q": "How do you reconcile E1?", "evidence_refs": ["E1"]},
            {"to": "Heretic", "q": "What about the date gap?", "evidence_refs": ["E2"]},
        ],
    }

    def test_round_trip(self):
        toml_str = dict_to_toml(self.QUESTIONS)
        result = toml_to_dict(toml_str)
        assert result == self.QUESTIONS

    def test_array_of_tables_syntax(self):
        toml_str = dict_to_toml(self.QUESTIONS)
        assert "[[questions]]" in toml_str


class TestRoundTripAnswersMessage:
    """AnswersMessage: array-of-tables with admission field."""

    ANSWERS = {
        "answers": [
            {"q": "How?", "a": "E1 is contextual", "evidence_refs": ["E1"], "admission": "none"},
            {"q": "Gap?", "a": "Not significant", "evidence_refs": ["E2"], "admission": "uncertain"},
        ],
    }

    def test_round_trip(self):
        toml_str = dict_to_toml(self.ANSWERS)
        result = toml_to_dict(toml_str)
        assert result == self.ANSWERS


class TestRoundTripRevision:
    """Revision: flat keys with a float field (confidence)."""

    REVISION = {
        "final_proposed_verdict": "SUPPORTED",
        "evidence_used": ["E1", "E2"],
        "what_i_changed": [],
        "remaining_disagreements": [],
        "confidence": 0.9,
    }

    def test_round_trip(self):
        toml_str = dict_to_toml(self.REVISION)
        result = toml_to_dict(toml_str)
        assert result == self.REVISION

    def test_confidence_stays_float(self):
        """Ensure confidence = 0.9, not integer 0."""
        toml_str = dict_to_toml(self.REVISION)
        assert "0.9" in toml_str


class TestRoundTripDisputeQuestionsMessage:
    """DisputeQuestionsMessage: single-element array-of-tables."""

    DISPUTE_Q = {
        "questions": [
            {"q": "Final decisive question", "evidence_refs": ["E1"]},
        ],
    }

    def test_round_trip(self):
        toml_str = dict_to_toml(self.DISPUTE_Q)
        result = toml_to_dict(toml_str)
        assert result == self.DISPUTE_Q


class TestRoundTripDisputeAnswersMessage:
    """DisputeAnswersMessage: single-element array-of-tables."""

    DISPUTE_A = {
        "answers": [
            {"q": "Question?", "a": "My answer", "evidence_refs": ["E1"], "admission": "none"},
        ],
    }

    def test_round_trip(self):
        toml_str = dict_to_toml(self.DISPUTE_A)
        result = toml_to_dict(toml_str)
        assert result == self.DISPUTE_A


# ── Fence stripping ─────────────────────────────────────────────────────────


class TestFenceStripping:
    """LLM may wrap output in markdown fences."""

    SIMPLE = {"key": "value", "nums": [1, 2, 3]}

    def test_toml_fenced_block(self):
        inner = tomli_w.dumps(self.SIMPLE)
        fenced = f"```toml\n{inner}```"
        result = toml_to_dict(fenced)
        assert result == self.SIMPLE

    def test_generic_fenced_block(self):
        inner = tomli_w.dumps(self.SIMPLE)
        fenced = f"```\n{inner}```"
        result = toml_to_dict(fenced)
        assert result == self.SIMPLE

    def test_fenced_with_extra_whitespace(self):
        inner = tomli_w.dumps(self.SIMPLE)
        fenced = f"```toml  \n{inner}\n```"
        result = toml_to_dict(fenced)
        assert result == self.SIMPLE


# ── Mixed LLM output extraction ─────────────────────────────────────────────


class TestMixedOutputExtraction:
    """LLM may prepend preamble text before the TOML block."""

    def test_preamble_then_toml(self):
        text = (
            "Here is my analysis:\n"
            "I think the evidence supports the claim.\n"
            "\n"
            'proposed_verdict = "SUPPORTED"\n'
            'evidence_used = ["E1"]\n'
            'key_points = ["good evidence"]\n'
            "uncertainties = []\n"
            'what_would_change_my_mind = ["more data"]\n'
        )
        result = toml_to_dict(text)
        assert result["proposed_verdict"] == "SUPPORTED"
        assert result["evidence_used"] == ["E1"]

    def test_preamble_then_fenced_toml(self):
        text = (
            "Sure, here is the output:\n"
            "```toml\n"
            'verdict = "REFUTED"\n'
            "confidence = 0.75\n"
            'evidence_used = ["E2"]\n'
            'reasoning = "Evidence contradicts"\n'
            "```\n"
        )
        result = toml_to_dict(text)
        assert result["verdict"] == "REFUTED"
        assert result["confidence"] == 0.75


# ── Edge cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_arrays(self):
        data = {"items": [], "name": "test"}
        toml_str = dict_to_toml(data)
        result = toml_to_dict(toml_str)
        assert result == data

    def test_special_characters_in_strings(self):
        data = {"text": 'He said "hello" and it\'s fine', "path": "C:\\Users\\test"}
        toml_str = dict_to_toml(data)
        result = toml_to_dict(toml_str)
        assert result == data

    def test_float_precision(self):
        data = {"confidence": 0.85, "score": 1.0}
        toml_str = dict_to_toml(data)
        result = toml_to_dict(toml_str)
        assert result["confidence"] == pytest.approx(0.85)
        assert result["score"] == pytest.approx(1.0)

    def test_integer_confidence_converted_to_float(self):
        """When a dict has confidence=0 (int), it should stay 0.0 (float) in TOML."""
        data = {"confidence": 0}
        toml_str = dict_to_toml(data)
        # TOML should show 0.0, not just 0
        assert "0.0" in toml_str

    def test_none_values_stripped(self):
        data = {"key": "value", "optional": None, "nested": {"a": 1, "b": None}}
        toml_str = dict_to_toml(data)
        result = toml_to_dict(toml_str)
        assert "optional" not in result
        assert "b" not in result["nested"]

    def test_invalid_toml_raises_value_error(self):
        with pytest.raises(ValueError, match="Could not parse TOML"):
            toml_to_dict("this is not valid {{}} TOML at all }{")

    def test_empty_string_returns_empty_dict(self):
        """Empty string is valid TOML (empty document = empty dict)."""
        result = toml_to_dict("")
        assert result == {}

    def test_pure_json_not_valid_toml(self):
        """JSON objects are not valid TOML; should raise."""
        with pytest.raises(ValueError):
            toml_to_dict('{"key": "value"}')
