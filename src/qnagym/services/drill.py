"""Drill service (orchestration).

Mirrors docs/spec/cli.md#drill.
"""

from __future__ import annotations

import sys
from typing import Any

from qnagym.contracts.types import Session, SessionStoreProtocol
from qnagym.contracts.validation import FlowError
from qnagym.domain.flow import record_answer
from qnagym.domain.session import all_answered, get_next_question


class DrillError(Exception):
    """Error during drill operation."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def drill_service(
    store: SessionStoreProtocol,
    session_id: str,
    question_id: str | None = None,
    answer: str | None = None,
    interactive: bool = False,
) -> Session:
    """Practice: hide answers, ask questions, record answers.

    Args:
        store: Session store for persistence
        session_id: Session ID or path
        question_id: Question ID to answer (optional, for recording answer)
        answer: User's answer text (optional, for recording answer)
        interactive: If True, run interactive loop reading from stdin

    Returns:
        Updated session

    Raises:
        DrillError: On flow error
    """
    session = store.load(session_id)

    # Validate preconditions
    if session.status not in {"confirmed", "drilling"}:
        raise DrillError(
            f"Session must be in 'confirmed' or 'drilling' state to drill, got '{session.status}'",
            exit_code=2,
        )

    # If answer provided, record it
    if question_id is not None and answer is not None:
        try:
            session = record_answer(session, question_id, answer)
        except FlowError as exc:
            raise DrillError(str(exc), exit_code=2) from exc
        store.save(session)
        return session

    # Interactive mode
    if interactive:
        return _drill_interactive(store, session)

    store.save(session)
    return session


def _drill_interactive(store: SessionStoreProtocol, session: Session) -> Session:
    """Run interactive drill loop."""
    # Validate preconditions
    if session.status not in {"confirmed", "drilling"}:
        raise DrillError(
            f"Session must be in 'confirmed' or 'drilling' state to drill, got '{session.status}'",
            exit_code=2,
        )

    while True:
        if all_answered(session):
            print(
                "All questions answered. Run 'qnagym evaluate' to see your score.", file=sys.stderr
            )
            break

        next_q = get_next_question(session)
        if next_q is None:
            print("No questions available.", file=sys.stderr)
            break

        answered_count = len([q for q in session.questions if q.user_answer])
        total_count = len(session.questions)

        print(
            f"\nSession: {session.id} | Progress: {answered_count}/{total_count}", file=sys.stderr
        )
        print(f"\nQuestion {next_q.id}: {next_q.prompt}", file=sys.stderr)
        print("Enter your answer (or 'skip' to skip, 'quit' to exit): ", end="", file=sys.stderr)
        sys.stderr.flush()

        try:
            answer = sys.stdin.readline()
            if not answer:  # EOF
                break
            answer = answer.rstrip("\n")
        except KeyboardInterrupt:
            print("\nExiting...", file=sys.stderr)
            break

        if answer.lower() == "quit":
            print("Exiting...", file=sys.stderr)
            break

        if answer.lower() == "skip":
            print("Skipped.", file=sys.stderr)
            # Record special marker to mark as answered (but skipped)
            session = record_answer(session, next_q.id, "[skipped]")
        else:
            session = record_answer(session, next_q.id, answer)
            print("Answer recorded.", file=sys.stderr)

        store.save(session)

    return session


def get_drill_display_data(session: Session) -> dict[str, Any]:
    """Get formatted drill data for display.

    Pure function - no side effects.

    Args:
        session: Session in drilling state

    Returns:
        Display dict with next question or completion status
    """
    if all_answered(session):
        return {
            "id": session.id,
            "status": session.status,
            "complete": True,
            "message": "All questions answered. Run 'qnagym evaluate' to see your score.",
        }

    next_q = get_next_question(session)
    if next_q is None:
        return {
            "id": session.id,
            "status": session.status,
            "complete": True,
            "message": "No questions available.",
        }

    answered_count = len([q for q in session.questions if q.user_answer])
    total_count = len(session.questions)

    return {
        "id": session.id,
        "status": session.status,
        "complete": False,
        "progress": f"{answered_count}/{total_count}",
        "question": {
            "id": next_q.id,
            "prompt": next_q.prompt,
        },
    }
