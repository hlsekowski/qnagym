"""Unit tests for domain flow logic."""

import pytest

from qnagym.contracts.types import Context, Progress, Question, Session
from qnagym.contracts.validation import FlowError, VagueMaterialError
from qnagym.domain.flow import (
    apply_evaluation,
    confirm_session,
    generate_questions,
    record_answer,
    refine_questions,
    repeat_session,
    reset_session,
    validate_transition_pure,
)


class TestGenerateQuestions:
    def test_generate_questions_ok(self):
        response = {
            "ok": True,
            "questions": [
                {"prompt": "What is photosynthesis?", "model_answer": "Process...", "id": "q1"},
                {"prompt": "What are inputs?", "model_answer": "CO2, water, light", "id": "q2"},
            ],
        }
        questions = generate_questions(response, 30)
        assert len(questions) == 2
        assert questions[0]["id"] == "q1"
        assert questions[0]["prompt"] == "What is photosynthesis?"
        assert questions[0]["agreed_answer"] == "Process..."

    def test_generate_questions_vague(self):
        response = {"ok": False, "questions": ["What topic?", "What scope?"]}
        with pytest.raises(VagueMaterialError) as exc:
            generate_questions(response, 30)
        assert exc.value.questions == ["What topic?", "What scope?"]

    def test_generate_questions_empty(self):
        response = {"ok": True, "questions": []}
        with pytest.raises(VagueMaterialError):
            generate_questions(response, 30)


class TestRefineQuestions:
    def test_refine_questions_updates_prompt_and_answer(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        response = {
            "ok": True,
            "questions": [
                {
                    "id": "q1",
                    "prompt": "What is photosynthesis?",
                    "model_answer": "Process by which plants...",
                }
            ],
        }
        comments = [{"question_id": "q1", "comment": "Make it more specific"}]

        refined = refine_questions(session, response, comments)

        assert refined.questions[0].prompt == "What is photosynthesis?"
        assert refined.questions[0].agreed_answer == "Process by which plants..."
        assert len(refined.questions[0].refinement_history) == 2  # prompt + answer changed
        assert refined.questions[0].refinement_history[0].field == "prompt"
        assert refined.questions[0].refinement_history[0].comment == "Make it more specific"

    def test_refine_questions_requires_prepared(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="confirmed",
        )
        response = {
            "ok": True,
            "questions": [{"id": "q1", "prompt": "What?", "model_answer": "Answer"}],
        }
        comments = [{"question_id": "q1", "comment": "test"}]

        with pytest.raises(FlowError, match="must be in 'prepared' state"):
            refine_questions(session, response, comments)

    def test_refine_questions_model_refused(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        response = {"ok": False, "questions": []}
        comments = [{"question_id": "q1", "comment": "test"}]

        with pytest.raises(FlowError, match="Model refused to refine"):
            refine_questions(session, response, comments)


class TestConfirmSession:
    def test_confirm_session(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        confirmed = confirm_session(session)
        assert confirmed.status == "confirmed"

    def test_confirm_session_invalid_state(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="confirmed",
        )
        with pytest.raises(FlowError, match="must be in 'prepared' state"):
            confirm_session(session)


class TestRecordAnswer:
    def test_record_answer_first(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="confirmed",
        )
        updated = record_answer(session, "q1", "My answer")
        assert updated.questions[0].user_answer == "My answer"
        assert updated.status == "drilling"

    def test_record_answer_subsequent(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="First")
            ],
            status="drilling",
        )
        updated = record_answer(session, "q1", "Second answer")
        assert updated.questions[0].user_answer == "Second answer"
        assert updated.status == "drilling"

    def test_record_answer_invalid_state(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        with pytest.raises(FlowError, match="must be in 'confirmed' or 'drilling'"):
            record_answer(session, "q1", "Answer")

    def test_record_answer_unknown_question(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="confirmed",
        )
        with pytest.raises(FlowError, match="Unknown question"):
            record_answer(session, "q99", "Answer")


class TestApplyEvaluation:
    def test_apply_evaluation(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=2,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer"),
                Question(
                    id="q2", prompt="What 2?", agreed_answer="Answer 2", user_answer="My answer 2"
                ),
            ],
            status="drilling",
        )
        response = {
            "evaluations": [
                {
                    "id": "q1",
                    "score": 0.8,
                    "confidence": 0.9,
                    "feedback": "Good",
                    "covered_points": ["a"],
                    "missed_points": ["b"],
                    "alternatives": [],
                },
                {
                    "id": "q2",
                    "score": 0.6,
                    "confidence": 0.8,
                    "feedback": "OK",
                    "covered_points": ["c"],
                    "missed_points": [],
                    "alternatives": [],
                },
            ],
            "next_steps": ["Review missed points"],
        }
        evaluated = apply_evaluation(session, response)

        assert evaluated.status == "evaluated"
        assert evaluated.questions[0].evaluation.score == 0.8
        assert evaluated.questions[1].evaluation.score == 0.6
        assert evaluated.progress.attempts == 1
        assert evaluated.progress.last_score == 0.7  # average
        assert evaluated.progress.best_score == 0.7
        assert evaluated.next_steps == ["Review missed points"]

    def test_apply_evaluation_requires_drilling(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="confirmed",
        )
        response = {
            "evaluations": [
                {
                    "id": "q1",
                    "score": 0.8,
                    "confidence": 0.9,
                    "feedback": "Good",
                    "covered_points": [],
                    "missed_points": [],
                    "alternatives": [],
                }
            ],
            "next_steps": [],
        }
        with pytest.raises(FlowError, match="must be in 'drilling' state"):
            apply_evaluation(session, response)

    def test_apply_evaluation_unanswered(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],  # no user_answer
            status="drilling",
        )
        response = {
            "evaluations": [
                {
                    "id": "q1",
                    "score": 0.8,
                    "confidence": 0.9,
                    "feedback": "Good",
                    "covered_points": [],
                    "missed_points": [],
                    "alternatives": [],
                }
            ],
            "next_steps": [],
        }
        with pytest.raises(FlowError, match="all questions must be answered"):
            apply_evaluation(session, response)


class TestRepeatSession:
    def test_repeat_session(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="evaluated",
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8, improving=True),
        )
        repeated = repeat_session(session)
        assert repeated.status == "confirmed"
        assert repeated.questions[0].user_answer is None
        assert repeated.questions[0].evaluation is None
        assert repeated.progress.attempts == 1  # preserved
        assert repeated.progress.best_score == 0.8  # preserved

    def test_repeat_session_invalid_state(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="drilling",
        )
        with pytest.raises(FlowError, match="must be in 'evaluated' state"):
            repeat_session(session)


class TestResetSession:
    def test_reset_from_drilling(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="drilling",
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8),
        )
        reset = reset_session(session)
        assert reset.status == "prepared"
        assert reset.questions[0].user_answer is None
        assert reset.progress.attempts == 0

    def test_reset_from_evaluated(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="evaluated",
            progress=Progress(attempts=2, best_score=0.9, last_score=0.7),
        )
        reset = reset_session(session)
        assert reset.status == "prepared"
        assert reset.progress.attempts == 0

    def test_reset_invalid_state(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="confirmed",
        )
        with pytest.raises(FlowError, match="must be in 'drilling' or 'evaluated'"):
            reset_session(session)


class TestTransitionValidation:
    def test_validate_transition_pure(self):
        assert validate_transition_pure("prepared", "confirmed") is True
        assert validate_transition_pure("prepared", "drilling") is False
        assert validate_transition_pure("evaluated", "prepared") is True
