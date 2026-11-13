"""Task queue service (orchestration).

Mirrors docs/adr/0004-worker-task-model.md §2-§5. Orchestrates task
creation, claiming, and scheduling; performs no GitHub or model I/O.
"""

from __future__ import annotations

from qnagym.contracts.task_model import (
    PRIORITY_SHORT,
    TASK_STATE_QUEUED,
    Claim,
    ExecutionState,
    Task,
    TaskIdentity,
)
from qnagym.domain.task_queue import (
    claim_task,
    coalesce,
    is_duplicate,
    is_eligible,
    order_eligible,
)


class TaskQueueError(Exception):
    """Error during task queue orchestration."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


def create_task(
    state: ExecutionState,
    kind: str,
    work_item: str | None,
    target: str,
    revision: str,
    created_time: float,
    not_before_time: float,
    event_time: float | None,
    priority: str = PRIORITY_SHORT,
    max_duration: float = 300.0,
    retry_limit: int = 3,
    generation: int = 0,
) -> tuple[Task, str | None]:
    """Create a task if it is not a duplicate or coalesced.

    Returns (task, skip_reason). skip_reason is set when the task was
    not created because it duplicates or coalesces with an existing one.
    """
    identity = TaskIdentity(
        kind=kind,
        work_item=work_item,
        target=target,
        revision=revision,
        generation=generation,
    )

    duplicate, reason = is_duplicate(state, identity, created_time)
    if duplicate:
        return Task(
            identity=identity,
            created_time=created_time,
            not_before_time=not_before_time,
            event_time=event_time,
            state=TASK_STATE_QUEUED,
            priority=priority,
            max_duration=max_duration,
            retry_limit=retry_limit,
        ), reason

    coalesced, reason = coalesce(state, identity, created_time)
    if coalesced:
        return Task(
            identity=identity,
            created_time=created_time,
            not_before_time=not_before_time,
            event_time=event_time,
            state=TASK_STATE_QUEUED,
            priority=priority,
            max_duration=max_duration,
            retry_limit=retry_limit,
        ), reason

    task = Task(
        identity=identity,
        created_time=created_time,
        not_before_time=not_before_time,
        event_time=event_time,
        state=TASK_STATE_QUEUED,
        priority=priority,
        max_duration=max_duration,
        retry_limit=retry_limit,
    )
    state.put_task(task)
    return task, None


def next_eligible_task(state: ExecutionState, now: float) -> Task | None:
    """Return the next eligible task for a free worker, or None.

    Orders eligible tasks: short before long, then event time, then
    creation time. A running task is never preempted (ADR 0004 §3).
    """
    eligible = [t for t in state.tasks.values() if is_eligible(t, now)]
    if not eligible:
        return None
    return order_eligible(eligible)[0]


def claim_next_task(
    state: ExecutionState, worker_id: str, expiry_time: float
) -> tuple[Task, Claim] | None:
    """Claim the next eligible task for a worker.

    Returns (task, claim) or None if no eligible task exists.
    """
    task = next_eligible_task(state, expiry_time)
    if task is None:
        return None

    claim = claim_task(state, task, worker_id, expiry_time)
    return task, claim
