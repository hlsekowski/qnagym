"""Unit tests for the task runner service."""

import tempfile
import time

from qnagym.contracts.task_model import (
    TASK_STATE_COMPLETED,
    TASK_STATE_FAILED,
    TASK_STATE_QUEUED,
    TASK_STATE_RUNNING,
    ExecutionState,
    Task,
    TaskIdentity,
)
from qnagym.domain.task_queue import claim_task
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.task_runner import (
    TaskRunnerError,
    run_once,
    run_once_with_retry,
)


def _identity(kind="issue_evaluation", work_item="42", target="t", revision="r", generation=0):
    return TaskIdentity(
        kind=kind,
        work_item=work_item,
        target=target,
        revision=revision,
        generation=generation,
    )


def _task(identity=None, state=TASK_STATE_QUEUED, not_before=0.0):
    if identity is None:
        identity = _identity()
    return Task(
        identity=identity,
        created_time=1.0,
        not_before_time=not_before,
        event_time=None,
        state=state,
    )


def _service():
    return ExecutionStateService(tempfile.mkdtemp())


def _state_with_queued_task():
    state = ExecutionState()
    identity = _identity()
    task = _task(identity=identity, not_before=0.0)
    state.put_task(task)
    return state, identity, task


class TestRunOnce:
    def test_claims_and_executes_task(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        result_task, outcome = run_once(service, "test_state", "w1", 100.0, stub)

        assert result_task is not None
        assert result_task.identity == identity
        assert outcome == "done"
        loaded = service.load("test_state")
        saved_task = loaded.get_task(identity)
        assert saved_task is not None
        assert saved_task.state == TASK_STATE_COMPLETED

    def test_returns_none_when_no_eligible_task(self):
        service = _service()
        state = ExecutionState()
        service.save("empty_state", state)

        def stub(t: Task) -> str:
            return "done"

        result_task, outcome = run_once(service, "empty_state", "w1", 100.0, stub)

        assert result_task is None
        assert outcome is None

    def test_returns_none_when_claim_conflict(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        claim_task(state, task, "w2", 9999.0)
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        result_task, outcome = run_once(service, "test_state", "w1", 100.0, stub)

        assert result_task is None
        assert outcome is None

    def test_saves_state_after_execution(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        run_once(service, "test_state", "w1", 100.0, stub)

        loaded = service.load("test_state")
        saved_task = loaded.get_task(identity)
        assert saved_task is not None
        assert saved_task.state == TASK_STATE_COMPLETED

    def test_records_failed_outcome(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        def stub(t: Task) -> str:
            raise RuntimeError("boom")

        result_task, outcome = run_once(service, "test_state", "w1", 100.0, stub)

        assert result_task is not None
        assert outcome == "failed: boom"
        loaded = service.load("test_state")
        saved_task = loaded.get_task(identity)
        assert saved_task.state == TASK_STATE_FAILED

    def test_restart_recovery(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        run_once(service, "test_state", "w1", 100.0, stub)

        service2 = ExecutionStateService(service.data_dir)
        loaded = service2.load("test_state")
        saved_task = loaded.get_task(identity)
        assert saved_task.state == TASK_STATE_COMPLETED

        result_task, outcome = run_once(service2, "test_state", "w1", 100.0, stub)
        assert result_task is None
        assert outcome is None

    def test_duplicate_delivery_handled(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        run_once(service, "test_state", "w1", 100.0, stub)

        result_task, outcome = run_once(service, "test_state", "w1", 100.0, stub)
        assert result_task is None
        assert outcome is None

    def test_claim_expiry_allows_takeover(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        task.state = TASK_STATE_RUNNING
        state.put_task(task)
        claim_task(state, task, "w1", 1.0)
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        time.sleep(1.1)
        result_task, outcome = run_once(service, "test_state", "w2", 100.0, stub)
        assert result_task is not None
        assert outcome == "done"

    def test_takeover_by_different_worker_id(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        run_once(service, "test_state", "w1", 100.0, stub)

        result_task, outcome = run_once(service, "test_state", "w2", 100.0, stub)
        assert result_task is None
        assert outcome is None


class TestRunOnceWithRetry:
    def test_retries_on_claim_conflict(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        claim_task(state, task, "w2", 9999.0)
        service.save("test_state", state)

        call_count = 0

        def stub(t: Task) -> str:
            nonlocal call_count
            call_count += 1
            return "done"

        result_task, outcome = run_once_with_retry(
            service, "test_state", "w1", 100.0, stub, max_retries=2
        )
        assert result_task is None
        assert outcome is None

    def test_succeeds_on_first_attempt(self):
        service = _service()
        state, identity, task = _state_with_queued_task()
        service.save("test_state", state)

        def stub(t: Task) -> str:
            return "done"

        result_task, outcome = run_once_with_retry(
            service, "test_state", "w1", 100.0, stub, max_retries=3
        )
        assert result_task is not None
        assert outcome == "done"

    def test_returns_none_when_no_eligible_task(self):
        service = _service()
        state = ExecutionState()
        service.save("empty_state", state)

        def stub(t: Task) -> str:
            return "done"

        result_task, outcome = run_once_with_retry(
            service, "empty_state", "w1", 100.0, stub, max_retries=3
        )
        assert result_task is None
        assert outcome is None


class TestTaskRunnerError:
    def test_error_has_message(self):
        err = TaskRunnerError("something went wrong")
        assert err.message == "something went wrong"
        assert str(err) == "something went wrong"
