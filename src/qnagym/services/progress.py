"""Progress service (orchestration).

Mirrors docs/spec/cli.md#repeat.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.types import Session, SessionStoreProtocol
from qnagym.contracts.validation import FlowError
from qnagym.domain.flow import repeat_session, reset_session
from qnagym.domain.scoring import calculate_progress_trend, format_score


class ProgressError(Exception):
    """Error during progress operation."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def repeat_service(
    store: SessionStoreProtocol,
    session_id: str,
) -> Session:
    """Repeat practice session (reset for another round).

    Args:
        store: Session store for persistence
        session_id: Session ID or path

    Returns:
        Updated session in 'confirmed' state

    Raises:
        ProgressError: On flow error
    """
    session = store.load(session_id)

    # Validate preconditions
    if session.status != "evaluated":
        raise ProgressError(
            f"Session must be in 'evaluated' state to repeat, got '{session.status}'",
            exit_code=2,
        )

    # Repeat session
    try:
        session = repeat_session(session)
    except FlowError as exc:
        raise ProgressError(str(exc), exit_code=2) from exc

    store.save(session)
    return session


def reset_service(
    store: SessionStoreProtocol,
    session_id: str,
) -> Session:
    """Reset session to prepared state for refinement.

    Args:
        store: Session store for persistence
        session_id: Session ID or path

    Returns:
        Updated session in 'prepared' state

    Raises:
        ProgressError: On flow error
    """
    session = store.load(session_id)

    # Validate preconditions
    if session.status not in {"drilling", "evaluated"}:
        raise ProgressError(
            f"Session must be in 'drilling' or 'evaluated' state to reset, got '{session.status}'",
            exit_code=2,
        )

    # Reset session
    try:
        session = reset_session(session)
    except FlowError as exc:
        raise ProgressError(str(exc), exit_code=2) from exc

    store.save(session)
    return session


def get_progress_display_data(session: Session) -> dict[str, Any]:
    """Get formatted progress data for display.

    Pure function - no side effects.

    Args:
        session: Session with progress

    Returns:
        Progress display dict
    """
    return {
        "attempts": session.progress.attempts,
        "best_score": format_score(session.progress.best_score),
        "last_score": format_score(session.progress.last_score),
        "trend": calculate_progress_trend(session.progress),
        "improving": session.progress.improving,
        "break_suggested": session.progress.break_suggested,
        "next_steps": session.next_steps,
    }
