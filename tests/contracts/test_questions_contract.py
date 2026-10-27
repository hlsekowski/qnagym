"""Contract tests for questions."""

from qnagym.contracts.questions import (
    CLARIFYING_QUESTIONS,
    FALLBACK_COUNT,
    MIN_MATERIAL_CHARS,
    MINUTES_PER_QUESTION,
    QUESTION_COUNT_MAX,
    QUESTION_COUNT_MIN,
    build_question_bank,
    calculate_question_count,
    material_too_short,
    parse_generate_response,
    question_count,
    validate_material,
)


class TestQuestionsContract:
    def test_constants_defined(self):
        assert FALLBACK_COUNT == 5
        assert QUESTION_COUNT_MIN == 3
        assert QUESTION_COUNT_MAX == 15
        assert MINUTES_PER_QUESTION == 6
        assert MIN_MATERIAL_CHARS == 20
        assert len(CLARIFYING_QUESTIONS) == 3

    def test_functions_defined(self):
        assert callable(material_too_short)
        assert callable(question_count)
        assert callable(calculate_question_count)
        assert callable(validate_material)
        assert callable(parse_generate_response)
        assert callable(build_question_bank)
