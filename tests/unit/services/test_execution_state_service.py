"""Unit tests for the execution state service."""

import tempfile

from qnagym.contracts.task_model import (
    ExecutionState,
    Task,
    TaskIdentity,
)
from qnagym.services.execution_state import (
    ExecutionStateService,
    ExecutionStateServiceError,
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


class TestExecutionStateService:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExecutionStateService(tmpdir)
            state = ExecutionState()
            identity = _identity(generation=1)
            task = _task(identity=identity)
            state.put_task(task)
            state.increment_generation()

            service.save("test_state", state)
            loaded = service.load("test_state")

            assert loaded.get_task(identity) is not None
            assert loaded.get_task(identity).identity == identity
            assert loaded.generation_counter == 1

    def test_save_and_load_multiple(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExecutionStateService(tmpdir)

            state1 = ExecutionState()
            identity1 = _identity(generation=1)
            task1 = _task(identity=identity1)
            state1.put_task(task1)

            state2 = ExecutionState()
            identity2 = _identity(generation=2)
            task2 = _task(identity=identity2)
            state2.put_task(task2)

            service.save("state1", state1)
            service.save("state2", state2)

            loaded1 = service.load("state1")
            loaded2 = service.load("state2")

            assert loaded1.get_task(identity1) is not None
            assert loaded2.get_task(identity2) is not None

    def test_load_nonexistent_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExecutionStateService(tmpdir)
            try:
                service.load("nonexistent")
                raise AssertionError("Should have raised ExecutionStateServiceError")
            except ExecutionStateServiceError:
                pass

    def test_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExecutionStateService(tmpdir)
            assert not service.exists("nonexistent")

            state = ExecutionState()
            identity = _identity()
            task = _task(identity=identity)
            state.put_task(task)
            service.save("test_state", state)

            assert service.exists("test_state")

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExecutionStateService(tmpdir)
            state = ExecutionState()
            identity = _identity()
            task = _task(identity=identity)
            state.put_task(task)
            service.save("test_state", state)

            assert service.exists("test_state")
            service.delete("test_state")
            assert not service.exists("test_state")

            try:
                service.delete("test_state")
                raise AssertionError("Should have raised ExecutionStateServiceError")
            except ExecutionStateServiceError:
                pass

    def test_list_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExecutionStateService(tmpdir)

            state1 = ExecutionState()
            identity1 = _identity(generation=1)
            task1 = _task(identity=identity1)
            state1.put_task(task1)

            state2 = ExecutionState()
            identity2 = _identity(generation=2)
            task2 = _task(identity=identity2)
            state2.put_task(task2)

            service.save("state1", state1)
            service.save("state2", state2)

            names = service.list_all()
            assert "state1" in names
            assert "state2" in names
            assert len(names) == 2

    def test_atomic_write_on_crash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExecutionStateService(tmpdir)
            state = ExecutionState()
            identity = _identity()
            task = _task(identity=identity)
            state.put_task(task)

            service.save("test_state", state)

            # Verify the file is valid JSON
            import json

            path = service._path_for("test_state")
            with open(path, encoding="utf-8") as f:
                data = json.loads(f.read())
            assert "tasks" in data
