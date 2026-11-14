"""Model routing service.

Mirrors docs/adr/0012-litellm-model-routing.md and
docs/adr/0008-workflow-runtime-and-model-routing.md.

Routes workflow-agent model calls through LiteLLM Proxy with Auto Routing.
LiteLLM runs as a separately operated local gateway, not as a Python SDK
dependency in qnagym. Existing clients continue using the OpenAI-compatible
API, which preserves constitution C4 and rule NC3's dependency boundary.

Workflow-agent calls use LiteLLM router aliases and allowlists. Until a
separate decision authorizes otherwise, the allowlist contains only locally
hosted models; a failure or unknown model must not fall through to a paid
or cloud provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ModelRoutingError(Exception):
    """Error during model routing."""


class ModelNotAllowedError(ModelRoutingError):
    """Model is not in the allowlist."""


@dataclass
class ModelRoute:
    """A model route mapping a router alias to a concrete model."""

    alias: str
    model: str
    provider: str = "ollama"
    base_url: str = "http://127.0.0.1:11434/v1"


@dataclass
class ModelRouter:
    """Routes model calls through LiteLLM-compatible router.

    LiteLLM runs as a separate local gateway, not as a Python SDK
    dependency. This service provides the routing logic and allowlist
    that the LiteLLM gateway would use.
    """

    routes: dict[str, ModelRoute] = field(default_factory=dict)
    allowlist: set[str] = field(default_factory=set)
    default_model: str = "gemma3:12b"

    def register_route(
        self,
        alias: str,
        model: str,
        provider: str = "ollama",
        base_url: str = "http://127.0.0.1:11434/v1",
    ) -> None:
        """Register a model route alias.

        Args:
            alias: Router alias name.
            model: The model name.
            provider: The model provider (default: ollama).
            base_url: The provider base URL (default: local Ollama).
        """
        self.routes[alias] = ModelRoute(
            alias=alias,
            model=model,
            provider=provider,
            base_url=base_url,
        )
        self.allowlist.add(model)

    def resolve(self, alias: str) -> ModelRoute:
        """Resolve a router alias to a concrete model route.

        Args:
            alias: The router alias to resolve.

        Returns:
            The resolved ModelRoute.

        Raises:
            ModelRoutingError: If the alias is not registered.
        """
        if alias not in self.routes:
            raise ModelRoutingError(f"Unknown model alias: {alias}")
        return self.routes[alias]

    def is_allowed(self, model: str) -> bool:
        """Check whether a model is in the allowlist.

        Args:
            model: The model name to check.

        Returns:
            True if the model is allowed, False otherwise.
        """
        return model in self.allowlist

    def route(self, alias: str) -> ModelRoute:
        """Route a model call through the alias.

        Args:
            alias: The router alias to route.

        Returns:
            The resolved ModelRoute.

        Raises:
            ModelRoutingError: If the alias is not registered or the model
                is not in the allowlist.
        """
        route = self.resolve(alias)
        if not self.is_allowed(route.model):
            raise ModelRoutingError(f"Model {route.model} is not in the allowlist")
        return route

    def default_route(self) -> ModelRoute:
        """Get the default model route.

        Returns:
            The default ModelRoute.

        Raises:
            ModelRoutingError: If the default model has no route.
        """
        for route in self.routes.values():
            if route.model == self.default_model:
                return route
        raise ModelRoutingError(f"Default model {self.default_model} has no route")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the router configuration to a dictionary."""
        return {
            "routes": {
                alias: {
                    "model": route.model,
                    "provider": route.provider,
                    "base_url": route.base_url,
                }
                for alias, route in self.routes.items()
            },
            "allowlist": sorted(self.allowlist),
            "default_model": self.default_model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelRouter:
        """Deserialize a ModelRouter from a dictionary."""
        router = cls()
        for alias, route_data in data.get("routes", {}).items():
            router.register_route(
                alias=alias,
                model=route_data["model"],
                provider=route_data.get("provider", "ollama"),
                base_url=route_data.get("base_url", "http://127.0.0.1:11434/v1"),
            )
        router.default_model = data.get("default_model", "gemma3:12b")
        return router


__all__ = [
    "ModelRouter",
    "ModelRoute",
    "ModelRoutingError",
    "ModelNotAllowedError",
]
