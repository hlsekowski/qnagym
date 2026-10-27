"""Domain scoring logic (pure business logic, no I/O).

Mirrors docs/spec/prompts.md, docs/spec/session.md.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.constants import (
    ALTERNATIVE_DELTA,
    CONFIDENCE_SHOW_BELOW,
    EVALUATE_SYSTEM,
    GENERATE_SYSTEM,
    REFINE_SYSTEM,
)
from qnagym.contracts.types import (
    Alternative,
    Context,
    EvaluateResponse,
    GenerateResponse,
    Progress,
    Session,
)
from qnagym.contracts.validation import (
    build_evaluate_messages,
    build_generate_messages,
    build_refine_messages,
    close_alternatives,
    should_show_confidence,
)


def build_generate_messages_for_domain(
    material: str, context: Context, n: int
) -> list[dict[str, str]]:
    """Build messages for question generation (pure function)."""
    return build_generate_messages(material, context, n)


def build_refine_messages_for_domain(
    material: str,
    context: Context,
    questions: list[Any],
    comments: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Build messages for Q&A refinement (pure function)."""
    return build_refine_messages(material, context, questions, comments)


def build_evaluate_messages_for_domain(session: Session) -> list[dict[str, str]]:
    """Build messages for evaluation (pure function)."""
    return build_evaluate_messages(session)


def parse_generate_response(data: dict[str, Any]) -> GenerateResponse:
    """Parse raw model response into GenerateResponse (pure function)."""
    return GenerateResponse.from_dict(data)


def parse_refine_response(data: dict[str, Any]) -> Any:
    """Parse raw model response into RefineResponse (pure function)."""
    from qnagym.contracts.types import RefineResponse

    return RefineResponse.from_dict(data)


def parse_evaluate_response(data: dict[str, Any]) -> EvaluateResponse:
    """Parse raw model response into EvaluateResponse (pure function)."""
    return EvaluateResponse.from_dict(data)


def should_display_confidence(confidence: float) -> bool:
    """Check if confidence should be displayed (pure function)."""
    return should_show_confidence(confidence)


def get_close_alternatives(top_score: float, alternatives: list[Alternative]) -> list[Alternative]:
    """Get alternatives within delta of top score (pure function)."""
    return close_alternatives(top_score, alternatives)


def apply_evaluations_to_session(
    session: Session,
    evaluate_response: EvaluateResponse,
) -> Session:
    """Apply parsed evaluations to session (pure function, returns updated session)."""
    from qnagym.domain.flow import apply_evaluation

    return apply_evaluation(session, evaluate_response.to_dict())


def get_generate_system_prompt() -> str:
    """Get the system prompt for question generation."""
    return GENERATE_SYSTEM


def get_refine_system_prompt() -> str:
    """Get the system prompt for Q&A refinement."""
    return REFINE_SYSTEM


def get_evaluate_system_prompt() -> str:
    """Get the system prompt for evaluation."""
    return EVALUATE_SYSTEM


def get_confidence_threshold() -> float:
    """Get the confidence display threshold."""
    return CONFIDENCE_SHOW_BELOW


def get_alternative_delta() -> float:
    """Get the alternative score delta threshold."""
    return ALTERNATIVE_DELTA


def calculate_progress_trend(progress: Progress) -> str:
    """Calculate progress trend indicator."""
    if progress.attempts <= 1:
        return "➡️"  # Starting
    elif progress.improving:
        return "📈"  # Improving
    elif progress.last_score == progress.best_score:
        return "➡️"  # Stable at best
    else:
        return "📉"  # Declining


def format_score(score: float) -> str:
    """Format score as percentage."""
    return f"{score * 100:.0f}%"
