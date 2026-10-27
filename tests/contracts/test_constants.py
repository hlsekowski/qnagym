"""Contract tests for constants."""

from qnagym.contracts.constants import (
    ALLOWED_TRANSITIONS,
    ALTERNATIVE_DELTA,
    AVOID_MODELS,
    CLARIFYING_QUESTIONS,
    CONFIDENCE_SHOW_BELOW,
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_DATA_DIR,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    ENV_MAP,
    EXIT_CODE_CONFIG_ERROR,
    EXIT_CODE_FLOW_ERROR,
    EXIT_CODE_INPUT_ERROR,
    EXIT_CODE_MODEL_ERROR,
    EXIT_CODE_SUCCESS,
    FALLBACK_COUNT,
    MIN_MATERIAL_CHARS,
    MINUTES_PER_QUESTION,
    QUESTION_COUNT_MAX,
    QUESTION_COUNT_MIN,
    STANDARD_USE_MODELS,
    VALID_STATUSES,
)


class TestConstants:
    def test_exit_codes(self):
        assert EXIT_CODE_SUCCESS == 0
        assert EXIT_CODE_MODEL_ERROR == 1
        assert EXIT_CODE_FLOW_ERROR == 2
        assert EXIT_CODE_CONFIG_ERROR == 3
        assert EXIT_CODE_INPUT_ERROR == 4

    def test_valid_statuses(self):
        assert {"prepared", "confirmed", "drilling", "evaluated"} == VALID_STATUSES

    def test_question_count_constants(self):
        assert FALLBACK_COUNT == 5
        assert QUESTION_COUNT_MIN == 3
        assert QUESTION_COUNT_MAX == 15
        assert MINUTES_PER_QUESTION == 6

    def test_material_constants(self):
        assert MIN_MATERIAL_CHARS == 20
        assert len(CLARIFYING_QUESTIONS) == 3

    def test_display_constants(self):
        assert CONFIDENCE_SHOW_BELOW == 0.95
        assert ALTERNATIVE_DELTA == 0.05

    def test_default_config(self):
        assert DEFAULT_BASE_URL == "http://127.0.0.1:11434/v1"
        assert DEFAULT_MODEL == "gemma3:12b"
        assert DEFAULT_API_KEY == "ollama"
        assert str(DEFAULT_DATA_DIR) == "data/sessions"
        assert DEFAULT_TEMPERATURE == 0.0
        assert DEFAULT_MAX_TOKENS == 4096
        assert DEFAULT_TIMEOUT == 60

    def test_env_map(self):
        assert ENV_MAP["base_url"] == "QNAGYM_BASE_URL"
        assert ENV_MAP["model"] == "QNAGYM_MODEL"
        assert ENV_MAP["api_key"] == "QNAGYM_API_KEY"
        assert ENV_MAP["data_dir"] == "QNAGYM_DATA_DIR"
        assert ENV_MAP["temperature"] == "QNAGYM_TEMPERATURE"
        assert ENV_MAP["max_tokens"] == "QNAGYM_MAX_TOKENS"
        assert ENV_MAP["timeout"] == "QNAGYM_TIMEOUT"

    def test_standard_use_models(self):
        assert "gemma3:12b" in STANDARD_USE_MODELS
        assert "llama3.2" in STANDARD_USE_MODELS
        assert "nemotron-3.5-super-vl-120b-a12b" in STANDARD_USE_MODELS

    def test_avoid_models(self):
        assert "gemma4:12b" in AVOID_MODELS
        assert "gemma4:12b-mlx" in AVOID_MODELS

    def test_allowed_transitions(self):
        assert ALLOWED_TRANSITIONS["prepared"] == {"prepared", "confirmed"}
        assert ALLOWED_TRANSITIONS["confirmed"] == {"drilling"}
        assert ALLOWED_TRANSITIONS["drilling"] == {"evaluated", "confirmed", "prepared"}
        assert ALLOWED_TRANSITIONS["evaluated"] == {"confirmed", "prepared"}
