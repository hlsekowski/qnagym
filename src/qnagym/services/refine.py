"""Refine service (orchestration).

Mirrors docs/spec/cli.md#refine.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.types import ModelClientProtocol, Session, SessionStoreProtocol
from qnagym.contracts.validation import FlowError
from qnagym.domain.flow import refine_questions
from qnagym.domain.scoring import parse_refine_response


class RefineError(Exception):
    """Error during refine operation."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def refine_service(
    client: ModelClientProtocol,
    store: SessionStoreProtocol,
    session_id: str,
    comments: list[dict[str, str]],
) -> Session:
    """Refine Q&A bank based on user comments.

    Args:
        client: Model client for refinement
        store: Session store for persistence
        session_id: Session ID or path
        comments: List of comment dicts with question_id and comment

    Returns:
        Updated session in 'prepared' state

    Raises:
        RefineError: On flow error or model error
    """
    session = store.load(session_id)

    # Validate preconditions
    if session.status != "prepared":
        raise RefineError(
            f"Session must be in 'prepared' state to refine, got '{session.status}'",
            exit_code=2,
        )

    if not comments:
        raise RefineError("No comments provided for refinement", exit_code=4)

    # Build messages
    from qnagym.contracts.validation import build_refine_messages

    messages = build_refine_messages(session.material, session.context, session.questions, comments)

    # Call model
    try:
        response = client.chat_json(messages)
    except Exception as exc:
        raise RefineError(f"Model error: {exc}", exit_code=1) from exc

    # Parse response
    try:
        refine_response = parse_refine_response(response)
    except Exception as exc:
        raise RefineError(f"Invalid model response: {exc}", exit_code=1) from exc

    # Apply refinement
    try:
        session = refine_questions(session, refine_response.to_dict(), comments)
    except FlowError as exc:
        raise RefineError(str(exc), exit_code=2) from exc

    store.save(session)
    return session


def get_refine_display_data(session: Session) -> dict[str, Any]:
    """Get formatted refine data for display.

    Pure function - no side effects.

    Args:
        session: Session with questions

    Returns:
        Display dict
    """
    return {
        "id": session.id,
        "material": session.material,
        "status": session.status,
        "questions": [
            {
                "id": q.id,
                "prompt": q.prompt,
                "agreed_answer": q.agreed_answer,
                "refinement_history": [
                    {
                        "timestamp": r.timestamp,
                        "field": r.field,
                        "comment": r.comment,
                        "previous_value": r.previous_value,
                        "new_value": r.new_value,
                    }
                    for r in q.refinement_history
                ],
            }
            for q in session.questions
        ],
    }
