"""Unit tests for the model routing service."""

from qnagym.services.model_routing import (
    ModelRouter,
    ModelRoutingError,
)


class TestModelRouter:
    def test_register_and_resolve_route(self):
        router = ModelRouter()
        router.register_route(
            "chat", "gemma3:12b", provider="ollama", base_url="http://127.0.0.1:11434/v1"
        )

        route = router.resolve("chat")
        assert route.alias == "chat"
        assert route.model == "gemma3:12b"
        assert route.provider == "ollama"
        assert route.base_url == "http://127.0.0.1:11434/v1"

    def test_resolve_unknown_alias_raises(self):
        router = ModelRouter()
        try:
            router.resolve("nonexistent")
        except ModelRoutingError:
            pass
        else:
            raise AssertionError("Expected ModelRoutingError for unknown alias")

    def test_is_allowed(self):
        router = ModelRouter()
        router.register_route("chat", "gemma3:12b", provider="ollama")

        assert router.is_allowed("gemma3:12b")
        assert not router.is_allowed("unknown-model")

    def test_route_checks_allowlist(self):
        router = ModelRouter()
        router.register_route("chat", "gemma3:12b", provider="ollama")

        # Allowed model works
        route = router.route("chat")
        assert route.model == "gemma3:12b"

        # Unknown alias raises
        try:
            router.route("unknown-alias")
        except ModelRoutingError:
            pass
        else:
            raise AssertionError("Expected ModelRoutingError for unknown alias")

    def test_default_route(self):
        router = ModelRouter()
        router.register_route("chat", "gemma3:12b", provider="ollama")

        route = router.default_route()
        assert route.model == "gemma3:12b"

    def test_default_route_not_allowed_raises(self):
        router = ModelRouter()
        router.default_model = "unknown-model"
        try:
            router.default_route()
        except ModelRoutingError:
            pass
        else:
            raise AssertionError("Expected ModelRoutingError for non-allowed default model")

    def test_to_dict_and_from_dict(self):
        router = ModelRouter()
        router.register_route(
            "chat", "gemma3:12b", provider="ollama", base_url="http://127.0.0.1:11434/v1"
        )
        router.register_route(
            "code", "qwen2.5-coder:7b", provider="ollama", base_url="http://127.0.0.1:11434/v1"
        )
        router.default_model = "gemma3:12b"

        data = router.to_dict()
        assert data["routes"]["chat"]["model"] == "gemma3:12b"
        assert data["routes"]["code"]["model"] == "qwen2.5-coder:7b"
        assert data["default_model"] == "gemma3:12b"
        assert "gemma3:12b" in data["allowlist"]
        assert "qwen2.5-coder:7b" in data["allowlist"]

        restored = ModelRouter.from_dict(data)
        assert restored.routes["chat"].model == "gemma3:12b"
        assert restored.routes["code"].model == "qwen2.5-coder:7b"
        assert restored.default_model == "gemma3:12b"
        assert restored.is_allowed("gemma3:12b")
        assert restored.is_allowed("qwen2.5-coder:7b")

    def test_empty_router(self):
        router = ModelRouter()
        assert router.routes == {}
        assert router.allowlist == set()
        assert router.default_model == "gemma3:12b"

        try:
            router.default_route()
        except ModelRoutingError:
            pass
        else:
            raise AssertionError("Expected ModelRoutingError for empty router default route")
