"""Generate service (orchestration).

Mirrors docs/spec/cli.md#generate.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.types import (
    Context,
    ModelClientProtocol,
    Question,
    Session,
    SessionStoreProtocol,
)
from qnagym.contracts.validation import FlowError, VagueMaterialError
from qnagym.domain.questions import build_question_bank, parse_generate_response, validate_material
from qnagym.domain.session import create_session


class GenerateError(Exception):
    """Error during generate operation."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def generate_service(
    client: ModelClientProtocol,
    store: SessionStoreProtocol,
    material: str,
    question_count: int | None = None,
    duration_minutes: int | None = None,
    difficulty: str = "medium",
    language: str = "en",
) -> Session:
    """Generate Q&A bank from material.

    Args:
        client: Model client for generation
        store: Session store for persistence
        material: Source material/topic/URL
        question_count: Explicit number of questions (overrides duration)
        duration_minutes: Session duration for auto question count
        difficulty: Difficulty level (easy/medium/hard)
        language: Language code

    Returns:
        Created session in 'prepared' state

    Raises:
        GenerateError: On validation error, model error, or flow error
    """
    # Validate material
    try:
        validate_material(material)
    except VagueMaterialError as exc:
        raise GenerateError(
            "Material too vague. Clarifying questions:\n"
            + "\n".join(f"  - {q}" for q in exc.questions),
            exit_code=4,
        ) from exc

    # Determine question count
    from qnagym.contracts.validation import question_count as calc_question_count

    n = question_count if question_count is not None else calc_question_count(duration_minutes)

    # Build context
    context = Context(
        duration_minutes=duration_minutes,
        difficulty=difficulty,
        language=language,
    )

    # Build messages
    from qnagym.contracts.validation import build_generate_messages

    messages = build_generate_messages(material, context, n)

    # Call model
    try:
        response = client.chat_json(messages)
    except Exception as exc:
        raise GenerateError(f"Model error: {exc}", exit_code=1) from exc

    # Parse response
    try:
        generate_response = parse_generate_response(response)
    except Exception as exc:
        raise GenerateError(f"Invalid model response: {exc}", exit_code=1) from exc

    # Build question bank
    try:
        gen_questions = build_question_bank(generate_response, n)
    except VagueMaterialError as exc:
        raise GenerateError(
            "Material too vague. Clarifying questions:\n"
            + "\n".join(f"  - {q}" for q in exc.questions),
            exit_code=4,
        ) from exc
    except FlowError as exc:
        raise GenerateError(str(exc), exit_code=2) from exc

    # Convert GenerateQuestion to Question
    questions = [
        Question(id=q.id or f"q{i}", prompt=q.prompt, agreed_answer=q.model_answer)
        for i, q in enumerate(gen_questions, start=1)
    ]

    # Create session
    session_id = store.new_session_id()
    session = create_session(session_id, material, questions, context)

    # Save session
    store.save(session)
    return session


def get_generate_display_data(session: Session) -> dict[str, Any]:
    """Get formatted generate data for display.

    Pure function - no side effects.

    Args:
        session: Session with generated questions

    Returns:
        Display dict
    """
    return {
        "id": session.id,
        "material": session.material,
        "question_count": session.question_count,
        "status": session.status,
        "questions": [
            {
                "id": q.id,
                "prompt": q.prompt,
                "agreed_answer": q.agreed_answer,
            }
            for q in session.questions
        ],
    }
