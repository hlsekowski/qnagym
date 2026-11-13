"""Task queue domain logic (pure business logic, no I/O).

Mirrors docs/adr/0004-worker-task-model.md §2-§5. Implements task
coalescing, duplicate prevention, scheduling, and eligibility; performs
no I/O.
"""

from __future__ import annotations

from qnagym.contracts.task_model import (
    PRIORITY_SHORT,
    TASK_STATE_COMPLETED,
    TASK_STATE_FAILED,
    TASK_STATE_OBSOLETE,
    TASK_STATE_QUEUED,
    TASK_STATE_RUNNING,
    Claim,
    ExecutionState,
    Task,
    TaskIdentity,
)

# Actions the queue can produce.
ACTION_CLAIM = "Claim"
ACTION_NONE = "None"


def task_key_for_identity(identity: TaskIdentity) -> str:
    """Stable key for a task identity."""
    return (
        f"{identity.kind}|{identity.work_item or ''}|"
        f"{identity.target}|{identity.revision}|{identity.generation}"
    )


def is_duplicate(
    state: ExecutionState, identity: TaskIdentity, now: float
) -> tuple[bool, str | None]:
    """Check whether a task identity already exists in a non-terminal state.

    Returns (is_duplicate, reason). Creating a task whose identity is
    already queued, running, successfully completed, or terminal Failed
    has no effect (ADR 0004 §3).
    """
    existing = state.get_task(identity)
    if existing is None:
        return False, None

    if existing.state in {TASK_STATE_QUEUED, TASK_STATE_RUNNING}:
        return True, f"task already {existing.state.lower()}"
    if existing.state == TASK_STATE_COMPLETED:
        return True, "task already completed"
    if existing.state == TASK_STATE_FAILED:
        return True, "task terminally failed"
    if existing.state == TASK_STATE_OBSOLETE:
        return True, "task obsolete"

    return False, None


def coalesce(state: ExecutionState, identity: TaskIdentity, now: float) -> tuple[bool, str | None]:
    """Apply coalescing policy for inputs arriving before a task starts.

    Inputs for the same work item that arrive before a task starts produce
    one task per kind, evaluating the latest state. They do not produce
    one task per input. Coalescing must preserve all unprocessed event
    identifiers (ADR 0004 §3).
    """
    existing = state.get_task(identity)
    if existing is None:
        return False, None

    if existing.state == TASK_STATE_QUEUED:
        return True, "coalesced into existing queued task"
    if existing.state == TASK_STATE_RUNNING:
        return True, "coalesced into running task"

    return False, None


def is_eligible(task: Task, now: float) -> bool:
    """A task is eligible when its not-before time is reached and it is queued."""
    return task.state == TASK_STATE_QUEUED and task.not_before_time <= now


def order_eligible(tasks: list[Task]) -> list[Task]:
    """Order eligible tasks: short before long, then event time, then creation time.

    Among eligible tasks, short tasks go ahead of long tasks. Otherwise
    tasks are ordered by event time, then by creation time (ADR 0004 §3).
    """

    def sort_key(task: Task) -> tuple[int, float, float, str]:
        priority_rank = 0 if task.priority == PRIORITY_SHORT else 1
        event_time = task.event_time if task.event_time is not None else task.created_time
        return (priority_rank, event_time, task.created_time, task.identity.kind)

    return sorted(tasks, key=sort_key)


def claim_task(state: ExecutionState, task: Task, worker_id: str, expiry_time: float) -> Claim:
    """Atomically claim a task for a worker.

    Claim acquisition must be atomic: two workers must not acquire valid
    claims for the same task or for concurrent tasks of the same work item
    (ADR 0004 §7).
    """
    task_key = task_key_for_identity(task.identity)
    existing_claim = state.get_claim(task_key)
    if existing_claim is not None and not existing_claim.is_expired(now=expiry_time):
        raise ValueError(f"task {task_key} already claimed by {existing_claim.worker_id}")

    fencing_generation = (existing_claim.fencing_generation + 1) if existing_claim else 1
    claim = Claim(
        task_identity=task.identity,
        worker_id=worker_id,
        expiry_time=expiry_time,
        fencing_generation=fencing_generation,
    )
    state.put_claim(claim)
    task.state = TASK_STATE_RUNNING
    state.put_task(task)
    return claim


def renew_claim(state: ExecutionState, claim: Claim, new_expiry_time: float) -> Claim:
    """Renew a claim before expiry (ADR 0004 §7)."""
    task_key = task_key_for_identity(claim.task_identity)
    existing = state.get_claim(task_key)
    if existing is None or existing.worker_id != claim.worker_id:
        raise ValueError(f"claim {task_key} not owned by {claim.worker_id}")

    renewed = Claim(
        task_identity=claim.task_identity,
        worker_id=claim.worker_id,
        expiry_time=new_expiry_time,
        fencing_generation=claim.fencing_generation,
    )
    state.put_claim(renewed)
    return renewed


def release_claim(state: ExecutionState, claim: Claim) -> None:
    """Release a claim when a task completes."""
    task_key = task_key_for_identity(claim.task_identity)
    state.remove_claim(task_key)


def is_claim_valid(state: ExecutionState, claim: Claim, now: float) -> bool:
    """Check that a claim is still valid and not expired (ADR 0004 §7)."""
    existing = state.get_claim(task_key_for_identity(claim.task_identity))
    if existing is None:
        return False
    if existing.worker_id != claim.worker_id:
        return False
    if existing.fencing_generation != claim.fencing_generation:
        return False
    return not existing.is_expired(now=now)


def take_over_after_expiry(state: ExecutionState, claim: Claim, now: float) -> bool:
    """Permit takeover after expiry and required ownership checks (ADR 0004 §7).

    A claim must not be released merely because another worker or process
    starts. Takeover is permitted after expiry.
    """
    existing = state.get_claim(task_key_for_identity(claim.task_identity))
    if existing is None:
        return False
    return bool(existing.is_expired(now=now))
