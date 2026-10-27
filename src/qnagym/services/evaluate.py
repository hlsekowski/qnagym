"""Evaluate service (orchestration).

Mirrors docs/spec/cli.md#evaluate.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.types import ModelClientProtocol, Session, SessionStoreProtocol
from qnagym.contracts.validation import FlowError
from qnagym.domain.flow import apply_evaluation
from qnagym.domain.scoring import parse_evaluate_response


class EvaluateError(Exception):
    """Error during evaluate operation."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def evaluate_service(
    client: ModelClientProtocol,
    store: SessionStoreProtocol,
    session_id: str | None = None,
) -> Session:
    """Evaluate all answers in a session.

    Args:
        client: Model client for evaluation
        store: Session store for persistence
        session_id: Session ID or path (None for latest)

    Returns:
        Updated session with evaluations and next_steps

    Raises:
        EvaluateError: On flow error or model error
    """
    session = store.load(session_id) if session_id else store.latest()

    # Validate preconditions
    if session.status != "drilling":
        raise EvaluateError(
            f"Session must be in 'drilling' state to evaluate, got '{session.status}'",
            exit_code=2,
        )

    unanswered = [q.id for q in session.questions if not (q.user_answer or "").strip()]
    if unanswered:
        raise EvaluateError(
            f"Unanswered questions: {', '.join(unanswered)}. Finish drill first",
            exit_code=2,
        )

    # Build evaluation messages
    from qnagym.contracts.validation import build_evaluate_messages

    messages = build_evaluate_messages(session)

    # Call model
    try:
        response = client.chat_json(messages)
    except Exception as exc:
        raise EvaluateError(f"Model error: {exc}", exit_code=1) from exc

    # Parse response
    try:
        evaluate_response = parse_evaluate_response(response)
    except Exception as exc:
        raise EvaluateError(f"Invalid model response: {exc}", exit_code=1) from exc

    # Apply evaluations
    try:
        session = apply_evaluation(session, evaluate_response.to_dict())
    except FlowError as exc:
        raise EvaluateError(str(exc), exit_code=2) from exc

    store.save(session)
    return session


def get_evaluation_display_data(session: Session) -> list[dict[str, Any]]:
    """Get formatted evaluation data for display.

    Pure function - no side effects.

    Args:
        session: Session with evaluations

    Returns:
        List of evaluation display dicts
    """
    from qnagym.contracts.validation import close_alternatives, should_show_confidence

    result: list[dict[str, Any]] = []
    for q in session.questions:
        ev = q.evaluation
        if not ev:
            result.append({"id": q.id, "evaluated": False})
            continue

        item: dict[str, Any] = {
            "id": q.id,
            "evaluated": True,
            "score": ev.score,
            "confidence": ev.confidence,
            "show_confidence": should_show_confidence(ev.confidence),
            "feedback": ev.feedback,
            "covered_points": ev.covered_points,
            "missed_points": ev.missed_points,
            "alternatives": [
                {"summary": a.summary, "score": a.score}
                for a in close_alternatives(ev.score, ev.alternatives)
            ],
        }
        result.append(item)

    return result


def get_next_steps(session: Session) -> list[str]:
    """Get next steps from session.

    Pure function - no side effects.
    """
    return list(session.next_steps)


def get_progress_display_data(session: Session) -> dict[str, Any]:
    """Get formatted progress data for display.

    Pure function - no side effects.

    Args:
        session: Session with progress

    Returns:
        Progress display dict
    """
    from qnagym.domain.scoring import calculate_progress_trend, format_score

    return {
        "attempts": session.progress.attempts,
        "best_score": format_score(session.progress.best_score),
        "last_score": format_score(session.progress.last_score),
        "trend": calculate_progress_trend(session.progress),
        "improving": session.progress.improving,
        "break_suggested": session.progress.break_suggested,
    }
