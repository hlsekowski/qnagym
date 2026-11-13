"""Unit tests for the task queue service."""

from qnagym.contracts.task_model import (
    PRIORITY_LONG,
    PRIORITY_SHORT,
    TASK_STATE_QUEUED,
    ExecutionState,
    TaskIdentity,
)
from qnagym.services.task_queue import (
    claim_next_task,
    create_task,
    next_eligible_task,
)


def _state():
    return ExecutionState()


def _identity(
    kind="issue_evaluation",
    work_item="42",
    target="t",
    revision="r",
    generation=0,
):
    return TaskIdentity(
        kind=kind,
        work_item=work_item,
        target=target,
        revision=revision,
        generation=generation,
    )


class TestCreateTask:
    def test_create_queued_task(self):
        state = _state()
        task, reason = create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=1.0,
            not_before_time=5.0,
            event_time=2.0,
        )
        assert reason is None
        assert task.state == TASK_STATE_QUEUED
        assert state.get_task(_identity()) is task

    def test_duplicate_not_created(self):
        state = _state()
        create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=1.0,
            not_before_time=5.0,
            event_time=2.0,
        )
        task, reason = create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=3.0,
            not_before_time=5.0,
            event_time=4.0,
        )
        assert reason is not None
        assert "queued" in reason or "completed" in reason
        # Only one task stored
        assert len(state.tasks) == 1

    def test_different_revision_creates_new_task(self):
        state = _state()
        create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r1",
            created_time=1.0,
            not_before_time=5.0,
            event_time=2.0,
        )
        task, reason = create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r2",
            created_time=3.0,
            not_before_time=5.0,
            event_time=4.0,
        )
        assert reason is None
        assert len(state.tasks) == 2

    def test_generation_creates_distinct_identity(self):
        state = _state()
        create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=1.0,
            not_before_time=5.0,
            event_time=2.0,
            generation=0,
        )
        task, reason = create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=3.0,
            not_before_time=5.0,
            event_time=4.0,
            generation=1,
        )
        assert reason is None
        assert len(state.tasks) == 2


class TestNextEligibleTask:
    def test_none_when_empty(self):
        state = _state()
        assert next_eligible_task(state, now=10.0) is None

    def test_none_when_not_before_not_reached(self):
        state = _state()
        create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=1.0,
            not_before_time=100.0,
            event_time=2.0,
        )
        assert next_eligible_task(state, now=10.0) is None

    def test_returns_eligible_task(self):
        state = _state()
        create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=1.0,
            not_before_time=5.0,
            event_time=2.0,
        )
        task = next_eligible_task(state, now=10.0)
        assert task is not None
        assert task.identity.revision == "r"

    def test_short_before_long(self):
        state = _state()
        create_task(
            state,
            kind="sdd_cycle",
            work_item="42",
            target="t",
            revision="r1",
            created_time=1.0,
            not_before_time=5.0,
            event_time=2.0,
            priority=PRIORITY_LONG,
        )
        create_task(
            state,
            kind="issue_evaluation",
            work_item="43",
            target="t2",
            revision="r2",
            created_time=1.0,
            not_before_time=5.0,
            event_time=100.0,
            priority=PRIORITY_SHORT,
        )
        task = next_eligible_task(state, now=10.0)
        assert task.identity.kind == "issue_evaluation"  # short goes first despite later event time


class TestClaimNextTask:
    def test_claims_next_eligible(self):
        state = _state()
        create_task(
            state,
            kind="issue_evaluation",
            work_item="42",
            target="t",
            revision="r",
            created_time=1.0,
            not_before_time=5.0,
            event_time=2.0,
        )
        result = claim_next_task(state, worker_id="w1", expiry_time=100.0)
        assert result is not None
        task, claim = result
        assert claim.worker_id == "w1"
        assert task.state == "Running"

    def test_none_when_no_eligible(self):
        state = _state()
        assert claim_next_task(state, worker_id="w1", expiry_time=100.0) is None
