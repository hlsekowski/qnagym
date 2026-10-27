"""Questions contract module.

Mirrors docs/spec/questions.md.
"""

from __future__ import annotations

from qnagym.contracts.constants import (
    CLARIFYING_QUESTIONS,
    FALLBACK_COUNT,
    MIN_MATERIAL_CHARS,
    MINUTES_PER_QUESTION,
    QUESTION_COUNT_MAX,
    QUESTION_COUNT_MIN,
)
from qnagym.contracts.validation import (
    material_too_short,
    question_count,
)
from qnagym.domain.questions import (
    build_question_bank,
    calculate_question_count,
    parse_generate_response,
    validate_material,
)

__all__ = [
    "FALLBACK_COUNT",
    "QUESTION_COUNT_MIN",
    "QUESTION_COUNT_MAX",
    "MINUTES_PER_QUESTION",
    "MIN_MATERIAL_CHARS",
    "CLARIFYING_QUESTIONS",
    "material_too_short",
    "question_count",
    "calculate_question_count",
    "validate_material",
    "parse_generate_response",
    "build_question_bank",
]
