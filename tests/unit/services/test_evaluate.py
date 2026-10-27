"""Unit tests for evaluate service."""

import pytest

from qnagym.contracts.types import Context, Question, Session
from qnagym.services.evaluate import (
    EvaluateError,
    evaluate_service,
    get_evaluation_display_data,
    get_next_steps,
)
from tests.http import model_client


class TestEvaluateService:
    def test_evaluate_service_success(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
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
        store.save(session)

        client = model_client(
            {
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
        )

        evaluated = evaluate_service(client, store, "test-session")

        assert evaluated.status == "evaluated"
        assert evaluated.questions[0].evaluation.score == 0.8
        assert evaluated.questions[1].evaluation.score == 0.6
        assert evaluated.progress.attempts == 1
        assert evaluated.progress.last_score == 0.7
        assert evaluated.next_steps == ["Review missed points"]

    def test_evaluate_service_wrong_state(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="confirmed",
        )
        store.save(session)

        client = model_client({"evaluations": [], "next_steps": []})

        with pytest.raises(EvaluateError) as exc:
            evaluate_service(client, store, "test-session")
        assert exc.value.exit_code == 2

    def test_evaluate_service_unanswered(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],  # no user_answer
            status="drilling",
        )
        store.save(session)

        client = model_client({"evaluations": [], "next_steps": []})

        with pytest.raises(EvaluateError) as exc:
            evaluate_service(client, store, "test-session")
        assert exc.value.exit_code == 2

    def test_get_evaluation_display_data(self):
        from qnagym.contracts.types import Evaluation

        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=2,
            context=Context(),
            questions=[
                Question(
                    id="q1",
                    prompt="What?",
                    agreed_answer="Answer",
                    user_answer="A",
                    evaluation=Evaluation(
                        score=0.8,
                        confidence=0.9,
                        feedback="Good",
                        covered_points=["a"],
                        missed_points=["b"],
                    ),
                ),
                Question(
                    id="q2",
                    prompt="What 2?",
                    agreed_answer="Answer 2",
                    user_answer="A2",
                    evaluation=None,
                ),
            ],
            status="evaluated",
        )
        data = get_evaluation_display_data(session)
        assert len(data) == 2
        assert data[0]["evaluated"] is True
        assert data[0]["score"] == 0.8
        assert data[1]["evaluated"] is False

    def test_get_next_steps(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[],
            status="evaluated",
            next_steps=["Step 1", "Step 2"],
        )
        steps = get_next_steps(session)
        assert steps == ["Step 1", "Step 2"]
