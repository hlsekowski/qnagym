"""Config adapter (I/O boundary).

Mirrors docs/spec/config.md.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from qnagym.contracts.constants import (
    CONFIG_KEYS,
    DEFAULTS,
    ENV_MAP,
    TOML_HOME,
    TOML_LOCAL,
    TOML_XDG,
)
from qnagym.contracts.types import Config
from qnagym.contracts.validation import validate_config


def load_toml_config(path: Path) -> dict[str, Any]:
    """Load config from TOML file."""
    if not path.is_file():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def find_toml_config(explicit: Path | None = None) -> dict[str, Any]:
    """Find and load TOML config file (auto-discovery)."""
    if explicit:
        return load_toml_config(explicit)

    # Auto-discovery order
    for path in [TOML_LOCAL, TOML_XDG, TOML_HOME]:
        if path.is_file():
            return load_toml_config(path)

    return {}


def load_config(
    cli_args: dict[str, Any] | None = None,
    explicit_config: Path | None = None,
) -> Config:
    """Load config with precedence: CLI > Env > TOML > Defaults.

    Args:
        cli_args: Dict of CLI arguments (keys matching CONFIG_KEYS)
        explicit_config: Explicit TOML config file path

    Returns:
        Validated Config object
    """
    # Start with defaults
    values = DEFAULTS.copy()

    # Apply TOML config
    toml_config = find_toml_config(explicit_config)
    for key in CONFIG_KEYS:
        if key in toml_config:
            values[key] = toml_config[key]

    # Apply environment variables
    for key, env_var in ENV_MAP.items():
        env_val = os.environ.get(env_var)
        if env_val is not None:
            # Type conversion
            if key in {"temperature"}:
                values[key] = float(env_val)
            elif key in {"max_tokens", "timeout"}:
                values[key] = int(env_val)
            elif key == "data_dir":
                values[key] = Path(env_val)
            else:
                values[key] = env_val

    # Apply CLI args (highest precedence)
    if cli_args:
        for key in CONFIG_KEYS:
            if key in cli_args and cli_args[key] is not None:
                values[key] = cli_args[key]

    # Convert data_dir to Path if string
    if isinstance(values["data_dir"], str):
        values["data_dir"] = Path(values["data_dir"])

    config = Config(
        base_url=values["base_url"],  # type: ignore[arg-type]
        model=values["model"],  # type: ignore[arg-type]
        api_key=values["api_key"],  # type: ignore[arg-type]
        data_dir=values["data_dir"],  # type: ignore[arg-type]
        temperature=values["temperature"],  # type: ignore[arg-type]
        max_tokens=values["max_tokens"],  # type: ignore[arg-type]
        timeout=values["timeout"],  # type: ignore[arg-type]
    )
    validate_config(config)
    return config
