"""Domain session operations (pure business logic, no I/O).

Mirrors docs/spec/session.md.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.types import Context, Question, Session
from qnagym.contracts.validation import validate_question, validate_session


def create_session(
    session_id: str,
    material: str,
    questions: list[Question],
    context: Context | None = None,
) -> Session:
    """Create a new session in 'prepared' state.

    Args:
        session_id: Unique session identifier
        material: Source material/topic
        questions: List of generated questions
        context: Optional context (duration, difficulty, language)

    Returns:
        New Session object
    """
    if context is None:
        context = Context()

    session = Session(
        id=session_id,
        material=material,
        question_count=len(questions),
        context=context,
        questions=questions,
        status="prepared",
    )
    validate_session(session)
    return session


def add_question(session: Session, question: Question) -> Session:
    """Add a question to the session.

    Args:
        session: Session to add question to
        question: Question to add

    Returns:
        Updated session
    """
    validate_question(question)
    session.questions.append(question)
    session.question_count = len(session.questions)
    session.touch()
    validate_session(session)
    return session


def get_question(session: Session, question_id: str) -> Question | None:
    """Get a question by ID.

    Args:
        session: Session to search
        question_id: Question ID to find

    Returns:
        Question if found, None otherwise
    """
    return next((q for q in session.questions if q.id == question_id), None)


def update_question_prompt(session: Session, question_id: str, new_prompt: str) -> Session:
    """Update a question's prompt.

    Args:
        session: Session containing the question
        question_id: Question ID to update
        new_prompt: New prompt text

    Returns:
        Updated session

    Raises:
        ValueError: If question not found
    """
    q = get_question(session, question_id)
    if q is None:
        raise ValueError(f"Question {question_id} not found")
    q.prompt = new_prompt
    session.touch()
    return session


def update_question_answer(session: Session, question_id: str, new_answer: str) -> Session:
    """Update a question's agreed answer.

    Args:
        session: Session containing the question
        question_id: Question ID to update
        new_answer: New agreed answer text

    Returns:
        Updated session

    Raises:
        ValueError: If question not found
    """
    q = get_question(session, question_id)
    if q is None:
        raise ValueError(f"Question {question_id} not found")
    q.agreed_answer = new_answer
    session.touch()
    return session


def record_user_answer(session: Session, question_id: str, answer: str) -> Session:
    """Record user's answer for a question.

    Args:
        session: Session containing the question
        question_id: Question ID to answer
        answer: User's answer text

    Returns:
        Updated session

    Raises:
        ValueError: If question not found
    """
    q = get_question(session, question_id)
    if q is None:
        raise ValueError(f"Question {question_id} not found")
    q.user_answer = answer
    session.touch()
    return session


def set_evaluation(session: Session, question_id: str, evaluation: Any) -> Session:
    """Set evaluation for a question.

    Args:
        session: Session containing the question
        question_id: Question ID to evaluate
        evaluation: Evaluation object

    Returns:
        Updated session

    Raises:
        ValueError: If question not found
    """
    q = get_question(session, question_id)
    if q is None:
        raise ValueError(f"Question {question_id} not found")
    q.evaluation = evaluation
    session.touch()
    return session


def get_unanswered_questions(session: Session) -> list[Question]:
    """Get all unanswered questions in a session.

    Args:
        session: Session to check

    Returns:
        List of unanswered questions
    """
    return session.unanswered()


def all_answered(session: Session) -> bool:
    """Check if all questions have been answered.

    Args:
        session: Session to check

    Returns:
        True if all questions answered
    """
    return len(session.unanswered()) == 0


def calculate_average_score(session: Session) -> float:
    """Calculate average score across all evaluated questions.

    Args:
        session: Session with evaluations

    Returns:
        Average score (0.0-1.0), or 0.0 if no evaluations
    """
    evaluated = [q for q in session.questions if q.evaluation is not None]
    if not evaluated:
        return 0.0
    return sum(q.evaluation.score for q in evaluated if q.evaluation is not None) / len(evaluated)


def get_next_question(session: Session) -> Question | None:
    """Get the next unanswered question in order.

    Args:
        session: Session to check

    Returns:
        Next unanswered question, or None if all answered
    """
    unanswered = session.unanswered()
    return unanswered[0] if unanswered else None
