"""Unit tests for domain session operations."""

import pytest

from qnagym.contracts.types import Context, Evaluation, Question, Session
from qnagym.domain.session import (
    add_question,
    all_answered,
    calculate_average_score,
    create_session,
    get_next_question,
    get_question,
    get_unanswered_questions,
    record_user_answer,
    set_evaluation,
    update_question_answer,
    update_question_prompt,
)


class TestDomainSession:
    def test_create_session(self):
        questions = [
            Question(id="q1", prompt="What?", agreed_answer="Answer"),
            Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
        ]
        session = create_session("test-id", "photosynthesis", questions)
        assert session.id == "test-id"
        assert session.material == "photosynthesis"
        assert session.question_count == 2
        assert session.status == "prepared"
        assert len(session.questions) == 2

    def test_add_question(self):
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        new_q = Question(id="q2", prompt="What 2?", agreed_answer="Answer 2")
        session = add_question(session, new_q)
        assert session.question_count == 2
        assert len(session.questions) == 2

    def test_get_question(self):
        session = Session(
            id="test",
            material="test",
            question_count=2,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="prepared",
        )
        q = get_question(session, "q1")
        assert q is not None
        assert q.id == "q1"
        assert get_question(session, "q99") is None

    def test_update_question_prompt(self):
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        session = update_question_prompt(session, "q1", "New prompt")
        assert session.questions[0].prompt == "New prompt"

    def test_update_question_prompt_not_found(self):
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        with pytest.raises(ValueError, match="Question q99 not found"):
            update_question_prompt(session, "q99", "New prompt")

    def test_update_question_answer(self):
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        session = update_question_answer(session, "q1", "New answer")
        assert session.questions[0].agreed_answer == "New answer"

    def test_record_user_answer(self):
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="confirmed",
        )
        session = record_user_answer(session, "q1", "My answer")
        assert session.questions[0].user_answer == "My answer"

    def test_set_evaluation(self):
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="drilling",
        )
        ev = Evaluation(score=0.8, confidence=0.9, feedback="Good")
        session = set_evaluation(session, "q1", ev)
        assert session.questions[0].evaluation is not None
        assert session.questions[0].evaluation.score == 0.8

    def test_get_unanswered_questions(self):
        session = Session(
            id="test",
            material="test",
            question_count=2,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="drilling",
        )
        unanswered = get_unanswered_questions(session)
        assert len(unanswered) == 1
        assert unanswered[0].id == "q2"

    def test_all_answered(self):
        session = Session(
            id="test",
            material="test",
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
        assert all_answered(session) is True

        session.questions[1].user_answer = None
        assert all_answered(session) is False

    def test_calculate_average_score(self):
        session = Session(
            id="test",
            material="test",
            question_count=2,
            context=Context(),
            questions=[
                Question(
                    id="q1",
                    prompt="What?",
                    agreed_answer="Answer",
                    user_answer="A",
                    evaluation=Evaluation(score=0.8, confidence=0.9, feedback="Good"),
                ),
                Question(
                    id="q2",
                    prompt="What 2?",
                    agreed_answer="Answer 2",
                    user_answer="A2",
                    evaluation=Evaluation(score=0.6, confidence=0.8, feedback="OK"),
                ),
            ],
            status="evaluated",
        )
        avg = calculate_average_score(session)
        assert abs(avg - 0.7) < 0.001

    def test_calculate_average_score_no_evaluations(self):
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        avg = calculate_average_score(session)
        assert avg == 0.0

    def test_get_next_question(self):
        session = Session(
            id="test",
            material="test",
            question_count=2,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="confirmed",
        )
        next_q = get_next_question(session)
        assert next_q is not None
        assert next_q.id == "q1"

        session.questions[0].user_answer = "Answered"
        next_q = get_next_question(session)
        assert next_q.id == "q2"

        session.questions[1].user_answer = "Answered"
        next_q = get_next_question(session)
        assert next_q is None
