"""Domain flow logic (pure business logic, no I/O).

Mirrors docs/spec/flow.md.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.constants import ALLOWED_TRANSITIONS, VALID_STATUSES
from qnagym.contracts.types import Session
from qnagym.contracts.validation import (
    FlowError,
    check_confirmed_or_drilling,
    check_drilling,
    check_evaluated,
    check_no_unanswered,
    check_prepared,
    enforce_transition,
    question_count,
)
from qnagym.domain.questions import build_question_bank, parse_generate_response


def generate_questions(
    generate_response: dict[str, Any],
    context_duration_minutes: int | None,
) -> list[dict[str, Any]]:
    """Extract and validate questions from generate response.

    Args:
        generate_response: Raw response from model (GenerateResponse dict)
        context_duration_minutes: Duration from context for expected count

    Returns:
        List of question dicts with id, prompt, agreed_answer

    Raises:
        VagueMaterialError: If response indicates vague material or no questions
    """

    generate_resp = parse_generate_response(generate_response)
    expected_count = question_count(context_duration_minutes)
    questions = build_question_bank(generate_resp, expected_count)
    return [{"id": q.id, "prompt": q.prompt, "agreed_answer": q.model_answer} for q in questions]


def refine_questions(
    session: Session,
    refine_response: dict[str, Any],
    comments: list[dict[str, str]],
) -> Session:
    """Apply refinement to session questions.

    Requires: status='prepared'

    Args:
        session: Session in 'prepared' state
        refine_response: Raw response from model (RefineResponse dict)
        comments: List of comment dicts with question_id and comment

    Returns:
        Updated session with refined questions

    Raises:
        FlowError: If session not in 'prepared' state
    """
    check_prepared(session)

    ok = refine_response.get("ok", True)
    raw_qs = refine_response.get("questions") or []

    if not ok:
        raise FlowError("Model refused to refine")

    by_id = {q.id: q for q in session.questions}

    for item in raw_qs:
        qid = str(item.get("id", ""))
        if qid not in by_id:
            continue
        q = by_id[qid]

        # Find comment for this question
        comment = next((c for c in comments if c.get("question_id") == qid), None)
        comment_text = comment.get("comment", "") if comment else ""

        # Record refinement history
        from qnagym.contracts.types import RefinementEntry, _now

        if "prompt" in item and item["prompt"] != q.prompt:
            q.refinement_history.append(
                RefinementEntry(
                    timestamp=_now(),
                    question_id=qid,
                    field="prompt",
                    comment=comment_text,
                    previous_value=q.prompt,
                    new_value=str(item["prompt"]),
                )
            )
            q.prompt = str(item["prompt"])

        if "model_answer" in item and item["model_answer"] != q.agreed_answer:
            q.refinement_history.append(
                RefinementEntry(
                    timestamp=_now(),
                    question_id=qid,
                    field="agreed_answer",
                    comment=comment_text,
                    previous_value=q.agreed_answer,
                    new_value=str(item["model_answer"]),
                )
            )
            q.agreed_answer = str(item["model_answer"])

    session.touch()
    return session


def confirm_session(session: Session) -> Session:
    """Confirm the Q&A bank (confirm action).

    Transitions: prepared -> confirmed

    Args:
        session: Session in 'prepared' state

    Returns:
        Updated session

    Raises:
        FlowError: If session not in 'prepared' state
    """
    check_prepared(session)
    enforce_transition(session.status, "confirmed")
    session.status = "confirmed"
    session.touch()
    return session


def record_answer(session: Session, question_id: str, answer: str) -> Session:
    """Record a user answer during drill phase.

    Transitions: confirmed -> drilling (first answer)
    Requires: status in {'confirmed', 'drilling'}

    Args:
        session: Session in 'confirmed' or 'drilling' state
        question_id: ID of question to answer
        answer: User's answer text

    Returns:
        Updated session

    Raises:
        FlowError: If session not in correct state, question not found
    """
    check_confirmed_or_drilling(session)

    found = next((q for q in session.questions if q.id == question_id), None)
    if found is None:
        raise FlowError(f"Unknown question {question_id}")

    found.user_answer = answer
    if session.status == "confirmed":
        session.status = "drilling"
    session.touch()
    return session


def apply_evaluation(
    session: Session,
    evaluate_response: dict[str, Any],
) -> Session:
    """Apply evaluation results to session.

    Transitions: drilling -> evaluated
    Requires: status='drilling', no unanswered questions

    Args:
        session: Session in 'drilling' state with all answers
        evaluate_response: Raw response from model (EvaluateResponse dict)

    Returns:
        Updated session with evaluations, progress, and next_steps

    Raises:
        FlowError: If session not in 'drilling' state or has unanswered questions
    """
    check_drilling(session)
    check_no_unanswered(session)

    by_id = {e.get("id"): e for e in evaluate_response.get("evaluations") or [] if e.get("id")}

    from qnagym.contracts.types import Alternative, Evaluation

    scores = []
    for q in session.questions:
        raw = by_id.get(q.id) or {}
        alts = [
            Alternative(summary=str(a.get("summary", "")), score=float(a.get("score", 0)))
            for a in raw.get("alternatives") or []
        ]
        q.evaluation = Evaluation(
            score=float(raw.get("score", 0)),
            confidence=float(raw.get("confidence", 0)),
            feedback=str(raw.get("feedback", "")),
            covered_points=[str(p) for p in raw.get("covered_points") or []],
            missed_points=[str(p) for p in raw.get("missed_points") or []],
            alternatives=alts,
        )
        scores.append(q.evaluation.score)

    # Update progress
    avg_score = sum(scores) / len(scores) if scores else 0.0
    previous_last = session.progress.last_score
    session.progress.attempts += 1
    session.progress.last_score = avg_score
    session.progress.best_score = max(session.progress.best_score, avg_score)
    # First attempt: no previous to compare, so improving stays True (default)
    # Subsequent attempts: improving if score > previous last_score
    if session.progress.attempts > 1:
        session.progress.improving = avg_score > previous_last

    # Break suggestion logic (per docs/spec/flow.md)
    # Suggest break if: not improving for 2+ attempts OR score < 0.3
    if session.progress.attempts >= 2 and not session.progress.improving or avg_score < 0.3:
        session.progress.break_suggested = True
    else:
        session.progress.break_suggested = False

    session.next_steps = [str(s) for s in evaluate_response.get("next_steps") or []]
    session.status = "evaluated"
    session.touch()
    return session


def repeat_session(session: Session) -> Session:
    """Repeat practice session (repeat action).

    Transitions: evaluated -> confirmed
    Clears: user answers, evaluations; preserves progress history

    Args:
        session: Session in 'evaluated' state

    Returns:
        Updated session

    Raises:
        FlowError: If session not in 'evaluated' state
    """
    check_evaluated(session)
    enforce_transition(session.status, "confirmed")

    for q in session.questions:
        q.user_answer = None
        q.evaluation = None

    session.status = "confirmed"
    session.next_steps = []
    session.touch()
    return session


def reset_session(session: Session) -> Session:
    """Reset session to prepared state (reset action).

    Transitions: drilling -> prepared, evaluated -> prepared
    Clears: user answers, evaluations, next_steps

    Args:
        session: Session in 'drilling' or 'evaluated' state

    Returns:
        Updated session

    Raises:
        FlowError: If session not in 'drilling' or 'evaluated' state
    """
    if session.status not in {"drilling", "evaluated"}:
        raise FlowError(
            f"Session must be in 'drilling' or 'evaluated' state to reset, got '{session.status}'"
        )
    enforce_transition(session.status, "prepared")

    for q in session.questions:
        q.user_answer = None
        q.evaluation = None

    session.progress.attempts = 0
    session.status = "prepared"
    session.next_steps = []
    session.touch()
    return session


def validate_transition_pure(from_status: str, to_status: str) -> bool:
    """Pure validation of status transition (no side effects)."""
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def get_allowed_transitions(status: str) -> set[str]:
    """Get allowed next statuses for a given status."""
    return ALLOWED_TRANSITIONS.get(status, set())


def is_terminal_status(status: str) -> bool:
    """Check if status is terminal (no outgoing transitions)."""
    return status in ALLOWED_TRANSITIONS and len(ALLOWED_TRANSITIONS[status]) == 0


def is_valid_status(status: str) -> bool:
    """Check if status is a valid status."""
    return status in VALID_STATUSES
