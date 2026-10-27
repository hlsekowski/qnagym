"""Contract tests for config."""

from qnagym.contracts.config import (
    CONFIG_KEYS,
    DEFAULTS,
    ENV_MAP,
    TOML_HOME,
    TOML_LOCAL,
    TOML_XDG,
)


class TestConfigContract:
    def test_config_keys_defined(self):
        expected = [
            "base_url",
            "model",
            "api_key",
            "data_dir",
            "temperature",
            "max_tokens",
            "timeout",
        ]
        assert expected == CONFIG_KEYS

    def test_defaults_defined(self):
        assert "base_url" in DEFAULTS
        assert "model" in DEFAULTS
        assert "api_key" in DEFAULTS
        assert "data_dir" in DEFAULTS
        assert "temperature" in DEFAULTS
        assert "max_tokens" in DEFAULTS
        assert "timeout" in DEFAULTS

    def test_env_map_defined(self):
        assert ENV_MAP["base_url"] == "QNAGYM_BASE_URL"
        assert ENV_MAP["model"] == "QNAGYM_MODEL"
        assert ENV_MAP["api_key"] == "QNAGYM_API_KEY"
        assert ENV_MAP["data_dir"] == "QNAGYM_DATA_DIR"
        assert ENV_MAP["temperature"] == "QNAGYM_TEMPERATURE"
        assert ENV_MAP["max_tokens"] == "QNAGYM_MAX_TOKENS"
        assert ENV_MAP["timeout"] == "QNAGYM_TIMEOUT"

    def test_toml_paths_defined(self):
        assert str(TOML_LOCAL) == "qnagym.toml"
        assert "qnagym" in str(TOML_XDG)
        assert "qnagym" in str(TOML_HOME)
