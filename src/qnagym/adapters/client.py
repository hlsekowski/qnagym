"""Model client adapter (I/O boundary).

Mirrors docs/spec/prompts.md, docs/spec/config.md.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from qnagym.contracts.types import Config, ModelClientProtocol

logger = logging.getLogger(__name__)


class ModelError(Exception):
    """Model client error."""

    def __init__(self, message: str, error_type: str = "model_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)


class ModelClient(ModelClientProtocol):
    """OpenAI-compatible model client with JSON structured output."""

    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
        )

    def chat_json(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Send chat completion request with JSON response format.

        Args:
            messages: List of message dicts with role and content

        Returns:
            Parsed JSON response

        Raises:
            ModelError: On HTTP error, timeout, malformed JSON, or invalid schema
        """
        logger.debug("Sending request to %s model %s", self.config.base_url, self.config.model)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,  # type: ignore[call-overload]
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.error("Model request failed: %s", exc)
            raise ModelError(f"Model request failed: {exc}", error_type="model_error") from exc

        content = response.choices[0].message.content
        if not content:
            raise ModelError("Empty response from model", error_type="invalid_response")

        logger.debug("Received response: %s", content[:200])

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON response: %s", exc)
            raise ModelError(
                f"Invalid JSON response: {exc}", error_type="invalid_response"
            ) from exc

        # Check for error response from model
        if "error" in data:
            err = data["error"]
            raise ModelError(
                err.get("message", "Model returned error"),
                error_type=err.get("type", "model_error"),
            )

        return data  # type: ignore[no-any-return]
