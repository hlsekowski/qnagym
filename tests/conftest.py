"""Test configuration and fixtures."""

import pytest

from qnagym.contracts.types import Context, Progress, Question, Session


@pytest.fixture
def sample_context() -> Context:
    return Context(duration_minutes=30, difficulty="medium", language="en")


@pytest.fixture
def sample_questions() -> list[Question]:
    return [
        Question(
            id="q1",
            prompt="What is photosynthesis?",
            agreed_answer="Process by which plants convert light to energy",
        ),
        Question(id="q2", prompt="What are the inputs?", agreed_answer="CO2, water, light"),
    ]


@pytest.fixture
def sample_session(sample_questions: list[Question], sample_context: Context) -> Session:
    return Session(
        id="test-session-123",
        material="photosynthesis",
        question_count=2,
        context=sample_context,
        questions=sample_questions,
        status="prepared",
    )


@pytest.fixture
def sample_progress() -> Progress:
    return Progress(
        attempts=1, best_score=0.8, last_score=0.8, improving=True, break_suggested=False
    )
