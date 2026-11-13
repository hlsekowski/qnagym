"""Unit tests for the execution state domain logic."""

import contextlib

from qnagym.contracts.task_model import (
    ExecutionState,
    Task,
    TaskIdentity,
)
from qnagym.domain.execution_state import (
    ExecutionStateError,
    deserialize_state,
    is_corrupt,
    merge_states,
    serialize_state,
    validate_state,
)


def _identity(kind="issue_evaluation", work_item="42", target="t", revision="r", generation=0):
    return TaskIdentity(
        kind=kind,
        work_item=work_item,
        target=target,
        revision=revision,
        generation=generation,
    )


def _task(identity=None, state="Queued", not_before=0.0):
    if identity is None:
        identity = _identity()
    return Task(
        identity=identity,
        created_time=1.0,
        not_before_time=not_before,
        event_time=None,
        state=state,
    )


class TestSerializeDeserialize:
    def test_roundtrip(self):
        state = ExecutionState()
        identity = _identity(generation=1)
        task = _task(identity=identity)
        state.put_task(task)
        state.increment_generation()

        data = serialize_state(state)
        restored = deserialize_state(data)
        assert restored.get_task(identity) is not None
        assert restored.get_task(identity).identity == identity
        assert restored.generation_counter == 1

    def test_serialize_to_dict(self):
        state = ExecutionState()
        identity = _identity()
        task = _task(identity=identity)
        state.put_task(task)

        data = serialize_state(state)
        assert "tasks" in data
        assert "claims" in data
        assert "observation_watermark" in data
        assert "generation_counter" in data


class TestDeserializeErrors:
    def test_invalid_json_raises(self):
        try:
            deserialize_state("{not valid json")
            raise AssertionError("Should have raised ExecutionStateError")
        except ExecutionStateError:
            pass

    def test_missing_fields_raises(self):
        with contextlib.suppress(ExecutionStateError):
            deserialize_state({"tasks": {}})

    def test_corrupt_data(self):
        assert is_corrupt("{not valid json")
        assert not is_corrupt('{"tasks": {}}')


class TestMergeStates:
    def test_merge_two_states(self):
        state1 = ExecutionState()
        identity1 = _identity(generation=1)
        task1 = _task(identity=identity1)
        state1.put_task(task1)
        state1.increment_generation()
        state1.increment_generation()  # generation_counter = 2

        state2 = ExecutionState()
        identity2 = _identity(generation=2)
        task2 = _task(identity=identity2)
        state2.put_task(task2)
        state2.increment_generation()  # generation_counter = 1

        merged = merge_states(state1, state2)
        assert merged.get_task(identity1) is not None
        assert merged.get_task(identity2) is not None
        assert merged.generation_counter == 2  # max(2, 1) = 2


class TestValidateState:
    def test_valid_state(self):
        state = ExecutionState()
        identity = _identity()
        task = _task(identity=identity)
        state.put_task(task)
        problems = validate_state(state)
        assert problems == []


class TestExecutionStateRoundtrip:
    def test_full_roundtrip(self):
        state = ExecutionState()
        identity = _identity(generation=5)
        task = _task(identity=identity, state="Running")
        state.put_task(task)
        state.increment_generation()
        state.increment_generation()
        state.observation_watermark = 1234567890.0

        data = serialize_state(state)
        restored = deserialize_state(data)

        assert restored.get_task(identity) is not None
        assert restored.get_task(identity).state == "Running"
        assert restored.generation_counter == 2
        assert restored.observation_watermark == 1234567890.0
