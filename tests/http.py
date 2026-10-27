"""HTTP mocking utilities for tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from qnagym.contracts.types import ModelClientProtocol


def model_client(response: dict[str, Any]) -> ModelClientProtocol:
    """Create a mock model client that returns the given response."""
    mock = MagicMock(spec=ModelClientProtocol)
    mock.chat_json.return_value = response
    return mock


def model_client_sequence(responses: list[dict[str, Any]]) -> ModelClientProtocol:
    """Create a mock model client that returns a sequence of responses."""
    mock = MagicMock(spec=ModelClientProtocol)
    mock.chat_json.side_effect = responses
    return mock
