"""Validation & Rules (validators, guards, business rules).

Mirrors docs/spec/session.md, docs/spec/flow.md, docs/spec/prompts.md,
docs/spec/questions.md, docs/spec/config.md.
"""

from __future__ import annotations

from qnagym.contracts.constants import (
    ALLOWED_TRANSITIONS,
    ALTERNATIVE_DELTA,
    CONFIDENCE_SHOW_BELOW,
    MIN_MATERIAL_CHARS,
    VALID_STATUSES,
)
from qnagym.contracts.types import (
    Alternative,
    Config,
    Context,
    Evaluation,
    Progress,
    Question,
    Session,
)

# --- Session validation (from docs/spec/session.md) ---


def validate_session(session: Session) -> None:
    """Validate the session against the spec contract.

    Raises ValueError if any field violates the contract in
    docs/spec/session.md.
    """
    if not session.id:
        raise ValueError("session id is required")
    if session.status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {session.status}")
    if not session.material:
        raise ValueError("material is required")
    if not isinstance(session.question_count, int) or session.question_count < 1:
        raise ValueError("question_count must be a positive integer")
    if len(session.questions) != session.question_count:
        raise ValueError(
            f"question_count ({session.question_count}) != "
            f"len(questions) ({len(session.questions)})"
        )
    for q in session.questions:
        validate_question(q)


def validate_context(context: Context) -> None:
    """Validate context fields."""
    if context.difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"invalid difficulty: {context.difficulty}")
    if context.duration_minutes is not None and context.duration_minutes < 0:
        raise ValueError("duration_minutes must be non-negative")


def validate_question(question: Question) -> None:
    """Validate a single question."""
    if not question.id:
        raise ValueError("question id is required")
    if not question.prompt:
        raise ValueError(f"question {question.id} prompt is required")
    if not question.agreed_answer:
        raise ValueError(f"question {question.id} agreed_answer is required")


def validate_progress(progress: Progress) -> None:
    """Validate progress fields."""
    if progress.attempts < 0:
        raise ValueError("attempts must be non-negative")
    if not 0.0 <= progress.best_score <= 1.0:
        raise ValueError("best_score must be in [0.0, 1.0]")
    if not 0.0 <= progress.last_score <= 1.0:
        raise ValueError("last_score must be in [0.0, 1.0]")


def validate_evaluation(evaluation: Evaluation) -> None:
    """Validate evaluation fields."""
    if not 0.0 <= evaluation.score <= 1.0:
        raise ValueError("score must be in [0.0, 1.0]")
    if not 0.0 <= evaluation.confidence <= 1.0:
        raise ValueError("confidence must be in [0.0, 1.0]")


# --- Flow validation (from docs/spec/flow.md) ---


class VagueMaterialError(Exception):
    """Raised when the material is too vague to generate questions."""

    def __init__(self, questions: list[str]):
        self.questions = questions
        super().__init__("Material is too vague")


class FlowError(Exception):
    """Raised when a flow guard rule is violated."""

    pass


# State machine (see docs/spec/flow.md)
# ALLOWED_TRANSITIONS = {...}  # defined in constants.py


def validate_transition(from_status: str, to_status: str) -> bool:
    """Validate that a status transition is allowed per the state machine."""
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def enforce_transition(from_status: str, to_status: str) -> None:
    """Enforce a valid transition, raising FlowError if invalid."""
    if not validate_transition(from_status, to_status):
        raise FlowError(f"invalid transition: {from_status} -> {to_status}")


# Guard rules (see docs/spec/flow.md)
GUARD_RULES = [
    {
        "name": "generate_creates_prepared",
        "description": (
            "generate creates session in 'prepared' state; "
            "if material vague, raises VagueMaterialError"
        ),
    },
    {
        "name": "refine_requires_prepared",
        "description": (
            "refine requires status='prepared'; updates agreed_answer/prompt, "
            "records in refinement_history"
        ),
    },
    {
        "name": "confirm_requires_prepared",
        "description": "confirm requires status='prepared'; transitions to 'confirmed'",
    },
    {
        "name": "drill_requires_confirmed",
        "description": (
            "record_answer (drill) requires status in {'confirmed', 'drilling'}; "
            "first answer transitions to 'drilling'"
        ),
    },
    {
        "name": "evaluate_requires_drilling_and_answered",
        "description": (
            "evaluate requires status='drilling' and no unanswered questions; "
            "transitions to 'evaluated'"
        ),
    },
    {
        "name": "repeat_requires_evaluated",
        "description": (
            "repeat requires status='evaluated'; transitions to 'confirmed'; "
            "clears answers/evaluations; increments attempts"
        ),
    },
    {
        "name": "reset_to_prepared",
        "description": (
            "reset from 'drilling' or 'evaluated' to 'prepared'; "
            "clears answers, evaluations, next_steps"
        ),
    },
]


def check_prepared(session: Session) -> None:
    """Guard: refine/confirm require status='prepared'."""
    if session.status != "prepared":
        raise FlowError(f"session must be in 'prepared' state, got '{session.status}'")


def check_confirmed_or_drilling(session: Session) -> None:
    """Guard: drill requires status in {'confirmed', 'drilling'}."""
    if session.status not in {"confirmed", "drilling"}:
        raise FlowError(
            f"session must be in 'confirmed' or 'drilling' state, got '{session.status}'"
        )


def check_drilling(session: Session) -> None:
    """Guard: evaluate requires status='drilling'."""
    if session.status != "drilling":
        raise FlowError(f"session must be in 'drilling' state, got '{session.status}'")


def check_evaluated(session: Session) -> None:
    """Guard: repeat requires status='evaluated'."""
    if session.status != "evaluated":
        raise FlowError(f"session must be in 'evaluated' state, got '{session.status}'")


def check_no_unanswered(session: Session) -> None:
    """Guard: evaluate requires no unanswered questions."""
    if session.unanswered():
        raise FlowError("all questions must be answered before evaluate")


def check_drilling_or_evaluated(session: Session) -> None:
    """Guard: reset to prepared requires status in {'drilling', 'evaluated'}."""
    if session.status not in {"drilling", "evaluated"}:
        raise FlowError(
            f"session must be in 'drilling' or 'evaluated' state to reset, got '{session.status}'"
        )


def reset_session(session: Session) -> Session:
    """Reset session to prepared state for refinement re-runs.

    Transitions: drilling -> prepared, evaluated -> prepared
    Clears: user answers, evaluations, next_steps; resets progress

    Args:
        session: Session in 'drilling' or 'evaluated' state

    Returns:
        Updated session

    Raises:
        FlowError: If session not in 'drilling' or 'evaluated' state
    """
    check_drilling_or_evaluated(session)
    enforce_transition(session.status, "prepared")
    session.status = "prepared"
    for q in session.questions:
        q.user_answer = None
        q.evaluation = None
    session.next_steps = []
    session.progress = Progress()  # Reset progress
    session.touch()
    return session


# --- Questions validation (from docs/spec/questions.md) ---


def material_too_short(text: str) -> bool:
    """Check if material is too vague.

    Args:
        text: The material text.

    Returns:
        True if the material is too vague (fewer than MIN_MATERIAL_CHARS after trimming).
    """
    return len(text.strip()) < MIN_MATERIAL_CHARS


def question_count(duration_minutes: int | None) -> int:
    """Calculate the number of questions based on session duration.

    Args:
        duration_minutes: Session length in minutes, or None for default.

    Returns:
        Number of questions (3-15).
    """
    from qnagym.contracts.constants import (
        FALLBACK_COUNT,
        MINUTES_PER_QUESTION,
        QUESTION_COUNT_MAX,
        QUESTION_COUNT_MIN,
    )

    if duration_minutes is None:
        return FALLBACK_COUNT
    return max(
        QUESTION_COUNT_MIN, min(QUESTION_COUNT_MAX, round(duration_minutes / MINUTES_PER_QUESTION))
    )


# --- Prompts validation (from docs/spec/prompts.md) ---


def should_show_confidence(confidence: float) -> bool:
    """Return True if confidence should be displayed (below 0.95)."""
    return confidence < CONFIDENCE_SHOW_BELOW


def close_alternatives(top_score: float, alternatives: list[Alternative]) -> list[Alternative]:
    """Return alternatives within ALTERNATIVE_DELTA of the top score."""
    return [a for a in alternatives if top_score - a.score <= ALTERNATIVE_DELTA]


def build_material_blob(material: str, context: Context) -> str:
    """Build the material blob for prompts (see docs/spec/prompts.md)."""
    parts = [f"Material:\n{material.strip()}"]
    if context.duration_minutes is not None:
        parts.append(f"duration_minutes: {context.duration_minutes}")
    if context.difficulty:
        parts.append(f"difficulty: {context.difficulty}")
    if context.language:
        parts.append(f"language: {context.language}")
    return "\n".join(parts)


def build_generate_messages(material: str, context: Context, n: int) -> list[dict[str, str]]:
    """Build messages for question generation (see docs/spec/prompts.md)."""
    from qnagym.contracts.constants import GENERATE_SYSTEM

    return [
        {"role": "system", "content": GENERATE_SYSTEM},
        {
            "role": "user",
            "content": f"Generate {n} Q&A.\n{build_material_blob(material, context)}",
        },
    ]


def build_refine_messages(
    material: str,
    context: Context,
    questions: list[Question],
    comments: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Build messages for Q&A refinement (see docs/spec/prompts.md)."""
    from qnagym.contracts.constants import REFINE_SYSTEM

    items = []
    for q in questions:
        items.append({"id": q.id, "prompt": q.prompt, "agreed_answer": q.agreed_answer})

    comments_str = "\n".join([f"- {c['question_id']}: {c['comment']}" for c in comments])

    return [
        {"role": "system", "content": REFINE_SYSTEM},
        {
            "role": "user",
            "content": (
                "Refine Q&A based on comments.\n"
                f"{build_material_blob(material, context)}\n"
                f"Current Q&A: {items}\n"
                f"Comments:\n{comments_str}"
            ),
        },
    ]


def build_evaluate_messages(session: Session) -> list[dict[str, str]]:
    """Build messages for evaluation (see docs/spec/prompts.md)."""
    from qnagym.contracts.constants import EVALUATE_SYSTEM

    items = []
    for q in session.questions:
        items.append(
            {
                "id": q.id,
                "prompt": q.prompt,
                "agreed_answer": q.agreed_answer,
                "user_answer": q.user_answer or "",
            }
        )
    return [
        {"role": "system", "content": EVALUATE_SYSTEM},
        {
            "role": "user",
            "content": f"{build_material_blob(session.material, session.context)}\nitems: {items}",
        },
    ]


# --- Config validation (from docs/spec/config.md) ---


def validate_config(config: Config) -> None:
    """Validate config fields."""
    if not config.base_url or not config.base_url.startswith(("http://", "https://")):
        raise ValueError("base_url must be a valid HTTP/HTTPS URL")
    if not config.model:
        raise ValueError("model must be non-empty")
    if not 0.0 <= config.temperature <= 2.0:
        raise ValueError("temperature must be in [0.0, 2.0]")
    if config.max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if config.timeout <= 0:
        raise ValueError("timeout must be positive")
    if not config.data_dir:
        raise ValueError("data_dir must be non-empty")
