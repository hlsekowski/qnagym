"""Domain question logic (pure business logic, no I/O).

Mirrors docs/spec/questions.md.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.types import GenerateQuestion, GenerateResponse
from qnagym.contracts.validation import (
    VagueMaterialError,
    material_too_short,
    question_count,
)


def calculate_question_count(duration_minutes: int | None) -> int:
    """Calculate the number of questions based on session duration.

    Args:
        duration_minutes: Session length in minutes, or None for default.

    Returns:
        Number of questions (3-15).
    """
    return question_count(duration_minutes)


def validate_material(material: str) -> None:
    """Validate that material is not too vague.

    Args:
        material: The material text.

    Raises:
        VagueMaterialError: If material is too vague with clarifying questions.
    """
    if material_too_short(material):
        from qnagym.contracts.constants import CLARIFYING_QUESTIONS

        raise VagueMaterialError(CLARIFYING_QUESTIONS)


def parse_generate_response(data: dict[str, Any]) -> GenerateResponse:
    """Parse raw model response into GenerateResponse (pure function)."""
    return GenerateResponse.from_dict(data)


def build_question_bank(
    generate_response: GenerateResponse,
    expected_count: int,
) -> list[GenerateQuestion]:
    """Build question bank from generate response.

    Args:
        generate_response: Parsed generate response
        expected_count: Expected number of questions

    Returns:
        List of GenerateQuestion objects

    Raises:
        VagueMaterialError: If response indicates vague material or no questions
    """
    if not generate_response.ok:
        clarifying = (
            [q.prompt for q in generate_response.questions] if generate_response.questions else []
        )
        raise VagueMaterialError(clarifying or [])

    if not generate_response.questions:
        raise VagueMaterialError([])

    questions = []
    for i, item in enumerate(generate_response.questions, start=1):
        questions.append(
            GenerateQuestion(
                id=item.id or f"q{i}",
                prompt=item.prompt,
                model_answer=item.model_answer,
            )
        )

    if len(questions) != expected_count:
        # Note: warning is logged by caller (adapter/service)
        pass

    return questions
