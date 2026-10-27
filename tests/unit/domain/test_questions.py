"""Unit tests for domain questions logic."""

import pytest

from qnagym.contracts.types import GenerateQuestion, GenerateResponse
from qnagym.contracts.validation import VagueMaterialError
from qnagym.domain.questions import (
    build_question_bank,
    calculate_question_count,
    parse_generate_response,
    validate_material,
)


class TestCalculateQuestionCount:
    def test_fallback(self):
        assert calculate_question_count(None) == 5

    def test_with_duration(self):
        assert calculate_question_count(30) == 5
        assert calculate_question_count(45) == 8
        assert calculate_question_count(90) == 15
        assert calculate_question_count(0) == 3
        assert calculate_question_count(1000) == 15


class TestValidateMaterial:
    def test_valid_material(self):
        validate_material("photosynthesis process in plants")  # Should not raise (>= 20 chars)

    def test_too_short_material(self):
        with pytest.raises(VagueMaterialError) as exc:
            validate_material("a" * 19)
        assert len(exc.value.questions) == 3

    def test_whitespace_trimmed(self):
        with pytest.raises(VagueMaterialError):
            validate_material("  short  ")


class TestParseGenerateResponse:
    def test_parse_ok(self):
        data = {
            "ok": True,
            "questions": [{"prompt": "What?", "model_answer": "Answer", "id": "q1"}],
        }
        resp = parse_generate_response(data)
        assert resp.ok is True
        assert len(resp.questions) == 1
        assert resp.questions[0].prompt == "What?"
        assert resp.questions[0].model_answer == "Answer"
        assert resp.questions[0].id == "q1"

    def test_parse_not_ok(self):
        data = {"ok": False, "questions": ["Clarifying question?"]}
        resp = parse_generate_response(data)
        assert resp.ok is False
        assert len(resp.questions) == 1
        assert resp.questions[0].prompt == "Clarifying question?"
        assert resp.questions[0].model_answer == ""


class TestBuildQuestionBank:
    def test_build_question_bank_ok(self):
        resp = GenerateResponse(
            ok=True,
            questions=[
                GenerateQuestion(prompt="What?", model_answer="Answer", id="q1"),
                GenerateQuestion(prompt="What 2?", model_answer="Answer 2", id="q2"),
            ],
        )
        questions = build_question_bank(resp, 2)
        assert len(questions) == 2
        assert questions[0].id == "q1"
        assert questions[1].id == "q2"

    def test_build_question_bank_auto_ids(self):
        resp = GenerateResponse(
            ok=True,
            questions=[
                GenerateQuestion(prompt="What?", model_answer="Answer"),
                GenerateQuestion(prompt="What 2?", model_answer="Answer 2"),
            ],
        )
        questions = build_question_bank(resp, 2)
        assert questions[0].id == "q1"
        assert questions[1].id == "q2"

    def test_build_question_bank_not_ok(self):
        resp = GenerateResponse(
            ok=False, questions=[GenerateQuestion(prompt="Clarify?", model_answer="")]
        )
        with pytest.raises(VagueMaterialError):
            build_question_bank(resp, 2)

    def test_build_question_bank_empty(self):
        resp = GenerateResponse(ok=True, questions=[])
        with pytest.raises(VagueMaterialError):
            build_question_bank(resp, 2)

    def test_build_question_bank_count_mismatch(self):
        resp = GenerateResponse(
            ok=True,
            questions=[
                GenerateQuestion(prompt="What?", model_answer="Answer", id="q1"),
            ],
        )
        # Should not raise, just log warning (tested by not raising)
        questions = build_question_bank(resp, 5)
        assert len(questions) == 1
