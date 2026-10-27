"""Contract tests for CLI."""

from qnagym.contracts.cli import (
    BEHAVIOR_RULES,
    COMMANDS,
    EXIT_CODES,
    GLOBAL_FLAGS,
)


class TestCLIContract:
    def test_commands_defined(self):
        assert "generate" in COMMANDS
        assert "refine" in COMMANDS
        assert "confirm" in COMMANDS
        assert "drill" in COMMANDS
        assert "evaluate" in COMMANDS
        assert "repeat" in COMMANDS
        assert "reset" in COMMANDS
        assert "list" in COMMANDS
        assert "show" in COMMANDS

    def test_global_flags_defined(self):
        assert "base_url" in GLOBAL_FLAGS
        assert "model" in GLOBAL_FLAGS
        assert "api_key" in GLOBAL_FLAGS
        assert "data_dir" in GLOBAL_FLAGS
        assert "config" in GLOBAL_FLAGS
        assert "json" in GLOBAL_FLAGS

    def test_exit_codes_defined(self):
        assert EXIT_CODES["success"] == 0
        assert EXIT_CODES["model_error"] == 1
        assert EXIT_CODES["flow_error"] == 2
        assert EXIT_CODES["config_error"] == 3
        assert EXIT_CODES["input_error"] == 4

    def test_behavior_rules_defined(self):
        assert len(BEHAVIOR_RULES) >= 8
