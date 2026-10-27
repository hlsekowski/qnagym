"""Config contract module.

Mirrors docs/spec/config.md.
"""

from __future__ import annotations

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

__all__ = [
    "Config",
    "validate_config",
    "CONFIG_KEYS",
    "DEFAULTS",
    "ENV_MAP",
    "TOML_LOCAL",
    "TOML_XDG",
    "TOML_HOME",
]
