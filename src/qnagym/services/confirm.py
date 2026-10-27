"""Confirm service (orchestration).

Mirrors docs/spec/cli.md#confirm.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.types import Session, SessionStoreProtocol
from qnagym.contracts.validation import FlowError
from qnagym.domain.flow import confirm_session


class ConfirmError(Exception):
    """Error during confirm operation."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def confirm_service(
    store: SessionStoreProtocol,
    session_id: str,
) -> Session:
    """Confirm/lock Q&A bank for practice.

    Args:
        store: Session store for persistence
        session_id: Session ID or path

    Returns:
        Updated session in 'confirmed' state

    Raises:
        ConfirmError: On flow error
    """
    session = store.load(session_id)

    # Validate preconditions
    if session.status != "prepared":
        raise ConfirmError(
            f"Session must be in 'prepared' state to confirm, got '{session.status}'",
            exit_code=2,
        )

    # Confirm session
    try:
        session = confirm_session(session)
    except FlowError as exc:
        raise ConfirmError(str(exc), exit_code=2) from exc

    store.save(session)
    return session


def get_confirm_display_data(session: Session) -> dict[str, Any]:
    """Get formatted confirm data for display.

    Pure function - no side effects.

    Args:
        session: Confirmed session

    Returns:
        Display dict
    """
    return {
        "id": session.id,
        "material": session.material,
        "status": session.status,
        "question_count": session.question_count,
        "questions": [
            {
                "id": q.id,
                "prompt": q.prompt,
                "agreed_answer": q.agreed_answer,
            }
            for q in session.questions
        ],
    }
