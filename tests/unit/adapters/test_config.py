"""Unit tests for config adapter."""

from qnagym.adapters.config import find_toml_config, load_config, load_toml_config
from qnagym.contracts.types import Config


class TestConfigAdapter:
    def test_load_config_defaults(self, tmp_path):
        config = load_config({"data_dir": tmp_path})
        assert isinstance(config, Config)
        assert config.base_url == "http://127.0.0.1:11434/v1"
        assert config.model == "gemma3:12b"
        assert config.api_key == "ollama"
        assert config.temperature == 0.0
        assert config.max_tokens == 4096
        assert config.timeout == 60

    def test_load_config_cli_override(self, tmp_path):
        config = load_config({"data_dir": tmp_path, "model": "llama3.2", "temperature": 0.5})
        assert config.model == "llama3.2"
        assert config.temperature == 0.5

    def test_load_toml_config(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        toml_file.write_text('model = "custom-model"\ntemperature = 0.7\n')
        config = load_toml_config(toml_file)
        assert config["model"] == "custom-model"
        assert config["temperature"] == 0.7

    def test_find_toml_config_local(self, tmp_path):
        toml_file = tmp_path / "qnagym.toml"
        toml_file.write_text('model = "local-model"\n')
        config = find_toml_config(tmp_path / "qnagym.toml")
        assert config["model"] == "local-model"

    def test_find_toml_config_not_found(self, tmp_path):
        config = find_toml_config(tmp_path / "nonexistent.toml")
        assert config == {}
