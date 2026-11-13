"""Task runner service (orchestration).

Mirrors docs/adr/0004-worker-task-model.md §2-§7. Orchestrates running
a single task attempt: claim, execute, record outcome, save state.
Performs no GitHub or model I/O.
"""

from __future__ import annotations

from collections.abc import Callable

from qnagym.contracts.task_model import (
    ExecutionState,
    Task,
)
from qnagym.domain.task_queue import (
    claim_task,
    task_key_for_identity,
)
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.task_queue import next_eligible_task


class TaskRunnerError(Exception):
    """Error during task runner orchestration."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


def run_once(
    service: ExecutionStateService,
    state_name: str,
    worker_id: str,
    expiry_time: float,
    run_task: Callable[[Task], str],
) -> tuple[Task | None, str | None]:
    """Run one task attempt: claim, execute, record outcome, save.

    Args:
        service: The execution state service.
        state_name: The name of the execution state to load.
        worker_id: The worker id claiming the task.
        expiry_time: The claim expiry time.
        run_task: A callable that takes a Task and returns an outcome string.
            Returns the outcome string or raises an exception on failure.

    Returns:
        (task, outcome) where task is the claimed task (or None if none
        eligible) and outcome is the outcome string (or None if no task
        was claimed).

    Raises:
        TaskRunnerError: If the state cannot be loaded or saved.
    """
    state = service.load(state_name)

    task = next_eligible_task(state, expiry_time)
    if task is None:
        # Try takeover: a Running task whose claim has expired
        task = _takeover_expired(state, worker_id, expiry_time)
        if task is None:
            return None, None

    try:
        claim_task(state, task, worker_id, expiry_time)
    except ValueError:
        # Another worker already claimed this task (duplicate delivery or conflict)
        return None, None

    try:
        outcome = run_task(task)
    except Exception as exc:
        outcome = f"failed: {exc}"

    task.state = "Completed" if outcome and not outcome.startswith("failed:") else "Failed"
    state.put_task(task)
    service.save(state_name, state)

    return task, outcome


def _takeover_expired(
    state: ExecutionState,
    worker_id: str,
    now: float,
) -> Task | None:
    """Find a Running task whose claim has expired and return it for takeover.

    Returns None if no such task exists.
    """
    from qnagym.contracts.task_model import TASK_STATE_RUNNING

    for task in state.tasks.values():
        if task.state != TASK_STATE_RUNNING:
            continue
        task_key = task_key_for_identity(task.identity)
        claim = state.get_claim(task_key)
        if claim is not None and claim.is_expired(now=now):
            return task
    return None


def run_once_with_retry(
    service: ExecutionStateService,
    state_name: str,
    worker_id: str,
    expiry_time: float,
    run_task: Callable[[Task], str],
    max_retries: int = 3,
) -> tuple[Task | None, str | None]:
    """Run one task attempt with retry on claim conflict.

    Args:
        service: The execution state service.
        state_name: The name of the execution state to load.
        worker_id: The worker id claiming the task.
        expiry_time: The claim expiry time.
        run_task: A callable that takes a Task and returns an outcome string.
        max_retries: Maximum number of retries on claim conflict.

    Returns:
        (task, outcome) where task is the claimed task (or None if none
        eligible) and outcome is the outcome string (or None if no task
        was claimed).
    """
    for _ in range(max_retries + 1):
        task, outcome = run_once(service, state_name, worker_id, expiry_time, run_task)
        if task is not None:
            return task, outcome
        # Task was None, meaning another worker claimed it. Reload and retry.
        service.load(state_name)

    return None, None


if __name__ == "__main__":
    raise SystemExit("task_runner is a library module; run tests with pytest")
