"""Prompts contract module.

Mirrors docs/spec/prompts.md.
"""

from __future__ import annotations

from qnagym.contracts.constants import (
    ALTERNATIVE_DELTA,
    AVOID_MODELS,
    CONFIDENCE_SHOW_BELOW,
    EVALUATE_SYSTEM,
    GENERATE_SYSTEM,
    REFINE_SYSTEM,
    STANDARD_USE_MODELS,
)
from qnagym.contracts.validation import (
    build_evaluate_messages,
    build_generate_messages,
    build_material_blob,
    build_refine_messages,
    close_alternatives,
    should_show_confidence,
)

__all__ = [
    "GENERATE_SYSTEM",
    "REFINE_SYSTEM",
    "EVALUATE_SYSTEM",
    "CONFIDENCE_SHOW_BELOW",
    "ALTERNATIVE_DELTA",
    "STANDARD_USE_MODELS",
    "AVOID_MODELS",
    "build_generate_messages",
    "build_refine_messages",
    "build_evaluate_messages",
    "build_material_blob",
    "should_show_confidence",
    "close_alternatives",
]
