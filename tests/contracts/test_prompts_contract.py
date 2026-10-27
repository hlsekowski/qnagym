"""Contract tests for prompts."""

from qnagym.contracts.prompts import (
    ALTERNATIVE_DELTA,
    AVOID_MODELS,
    CONFIDENCE_SHOW_BELOW,
    EVALUATE_SYSTEM,
    GENERATE_SYSTEM,
    REFINE_SYSTEM,
    STANDARD_USE_MODELS,
    build_evaluate_messages,
    build_generate_messages,
    build_material_blob,
    build_refine_messages,
    close_alternatives,
    should_show_confidence,
)


class TestPromptsContract:
    def test_system_prompts_defined(self):
        assert "Knowledge coach" in GENERATE_SYSTEM
        assert "Refine Q&A" in REFINE_SYSTEM
        assert "Score each user answer" in EVALUATE_SYSTEM

    def test_display_constants_defined(self):
        assert CONFIDENCE_SHOW_BELOW == 0.95
        assert ALTERNATIVE_DELTA == 0.05

    def test_model_lists_defined(self):
        assert "gemma3:12b" in STANDARD_USE_MODELS
        assert "llama3.2" in STANDARD_USE_MODELS
        assert "nemotron-3.5-super-vl-120b-a12b" in STANDARD_USE_MODELS
        assert "gemma4:12b" in AVOID_MODELS
        assert "gemma4:12b-mlx" in AVOID_MODELS

    def test_prompt_builders_defined(self):
        assert callable(build_generate_messages)
        assert callable(build_refine_messages)
        assert callable(build_evaluate_messages)
        assert callable(build_material_blob)
        assert callable(should_show_confidence)
        assert callable(close_alternatives)
