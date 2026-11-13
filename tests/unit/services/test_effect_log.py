"""Unit tests for the safe effect log service."""

import tempfile

from qnagym.contracts.task_model import ExecutionState
from qnagym.services.effect_log import (
    EffectAdapterError,
    EffectLog,
    EffectLogError,
)
from qnagym.services.execution_state import ExecutionStateService


class FakeAdapter:
    """Fake effect adapter recording calls."""

    def __init__(self):
        self.posted: list[str] = []
        self.fail = False

    def post_comment(self, body: str) -> str:
        if self.fail:
            raise EffectAdapterError("post failed")
        self.posted.append(body)
        return f"external-{len(self.posted)}"


def _service():
    return ExecutionStateService(tempfile.mkdtemp())


def _effect_log(service=None, adapter=None, state_name="effect_state"):
    if service is None:
        service = _service()
    if adapter is None:
        adapter = FakeAdapter()
    return EffectLog(service=service, state_name=state_name, adapter=adapter)


class TestRecordIntent:
    def test_record_intent_saves(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.record_intent("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")

        loaded = service.load("effect_state")
        assert "eff-1" in loaded.effects
        assert loaded.effects["eff-1"]["outcome"] is None
        assert loaded.effects["eff-1"]["body"] == "<!-- qnagym-workflow --> hi"

    def test_duplicate_intent_raises(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.record_intent("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")

        try:
            log.record_intent("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")
            raise AssertionError("Should have raised EffectLogError")
        except EffectLogError:
            pass


class TestRecordOutcome:
    def test_record_outcome_saves(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.record_intent("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")
        log.record_outcome("eff-1", "external-1")

        loaded = service.load("effect_state")
        assert loaded.effects["eff-1"]["outcome"] == "external-1"

    def test_record_outcome_no_intent_raises(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        try:
            log.record_outcome("eff-1", "external-1")
            raise AssertionError("Should have raised EffectLogError")
        except EffectLogError:
            pass


class TestHasOutcome:
    def test_has_outcome_false_before_outcome(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.record_intent("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")

        assert not log.has_outcome("eff-1")

    def test_has_outcome_true_after_outcome(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.record_intent("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")
        log.record_outcome("eff-1", "external-1")

        assert log.has_outcome("eff-1")

    def test_has_outcome_false_unknown_id(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        assert not log.has_outcome("unknown")


class TestDispatchIfNeeded:
    def test_dispatch_posts_comment_once(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        external_id = log.dispatch_if_needed(
            "eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi"
        )

        assert external_id == "external-1"
        assert len(adapter.posted) == 1
        assert adapter.posted[0] == "<!-- qnagym-workflow --> hi"

    def test_replay_does_not_post_twice(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.dispatch_if_needed("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")
        result = log.dispatch_if_needed(
            "eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi"
        )

        assert result is None
        assert len(adapter.posted) == 1

    def test_crash_between_intent_and_outcome_replay_posts_once(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        # Record intent manually (simulating crash before outcome)
        log.record_intent("eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi")

        # Replay: dispatch_if_needed sees intent without outcome, dispatches
        external_id = log.dispatch_if_needed(
            "eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> hi"
        )

        assert external_id == "external-1"
        assert len(adapter.posted) == 1

    def test_comment_starts_with_workflow_marker(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.dispatch_if_needed(
            "eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> body"
        )

        assert adapter.posted[0].startswith("<!-- qnagym-workflow -->")

    def test_adapter_never_calls_merge_or_close(self):
        service = _service()
        adapter = FakeAdapter()
        log = _effect_log(service, adapter)
        state = ExecutionState()
        service.save("effect_state", state)

        log.dispatch_if_needed(
            "eff-1", "task-key-1", "post_comment", "<!-- qnagym-workflow --> body"
        )

        # FakeAdapter only has post_comment; no merge/close methods exist
        assert not hasattr(adapter, "merge")
        assert not hasattr(adapter, "close")
        assert len(adapter.posted) == 1


class TestEffectLogError:
    def test_error_has_message(self):
        err = EffectLogError("something went wrong")
        assert err.message == "something went wrong"
        assert str(err) == "something went wrong"


class TestEffectAdapterError:
    def test_error_has_message(self):
        err = EffectAdapterError("adapter failed")
        assert err.message == "adapter failed"
        assert str(err) == "adapter failed"
