"""Unit tests for the task queue domain logic."""

from qnagym.contracts.task_model import (
    PRIORITY_LONG,
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
from qnagym.domain.task_queue import (
    claim_task,
    coalesce,
    is_claim_valid,
    is_duplicate,
    is_eligible,
    order_eligible,
    release_claim,
    renew_claim,
    take_over_after_expiry,
    task_key_for_identity,
)


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


def _task(
    identity=None,
    state=TASK_STATE_QUEUED,
    priority=PRIORITY_SHORT,
    not_before=0.0,
    event_time=None,
    created_time=1.0,
):
    if identity is None:
        identity = _identity()
    return Task(
        identity=identity,
        created_time=created_time,
        not_before_time=not_before,
        event_time=event_time,
        state=state,
        priority=priority,
    )


class TestTaskKeyForIdentity:
    def test_stable_key(self):
        identity = _identity(generation=3)
        key = task_key_for_identity(identity)
        assert key == "issue_evaluation|42|t|r|3"

    def test_none_work_item(self):
        identity = _identity(work_item=None)
        key = task_key_for_identity(identity)
        assert key == "issue_evaluation||t|r|0"


class TestIsDuplicate:
    def test_no_existing_task(self):
        state = ExecutionState()
        dup, reason = is_duplicate(state, _identity(), 10.0)
        assert not dup
        assert reason is None

    def test_queued_is_duplicate(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_QUEUED))
        dup, reason = is_duplicate(state, _identity(), 10.0)
        assert dup
        assert "queued" in reason

    def test_running_is_duplicate(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_RUNNING))
        dup, reason = is_duplicate(state, _identity(), 10.0)
        assert dup
        assert "running" in reason

    def test_completed_is_duplicate(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_COMPLETED))
        dup, reason = is_duplicate(state, _identity(), 10.0)
        assert dup
        assert "completed" in reason

    def test_failed_is_duplicate(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_FAILED))
        dup, reason = is_duplicate(state, _identity(), 10.0)
        assert dup
        assert "failed" in reason

    def test_obsolete_is_duplicate(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_OBSOLETE))
        dup, reason = is_duplicate(state, _identity(), 10.0)
        assert dup
        assert "obsolete" in reason

    def test_different_identity_not_duplicate(self):
        state = ExecutionState()
        state.put_task(_task(identity=_identity(revision="r1")))
        dup, reason = is_duplicate(state, _identity(revision="r2"), 10.0)
        assert not dup
        assert reason is None


class TestCoalesce:
    def test_queued_coalesces(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_QUEUED))
        coal, reason = coalesce(state, _identity(), 10.0)
        assert coal
        assert "queued" in reason

    def test_running_coalesces(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_RUNNING))
        coal, reason = coalesce(state, _identity(), 10.0)
        assert coal
        assert "running" in reason

    def test_completed_does_not_coalesce(self):
        state = ExecutionState()
        state.put_task(_task(state=TASK_STATE_COMPLETED))
        coal, reason = coalesce(state, _identity(), 10.0)
        assert not coal
        assert reason is None

    def test_no_existing_does_not_coalesce(self):
        state = ExecutionState()
        coal, reason = coalesce(state, _identity(), 10.0)
        assert not coal
        assert reason is None


class TestIsEligible:
    def test_queued_and_not_before_reached(self):
        task = _task(not_before=5.0)
        assert is_eligible(task, 10.0)

    def test_not_before_not_reached(self):
        task = _task(not_before=20.0)
        assert not is_eligible(task, 10.0)

    def test_running_not_eligible(self):
        task = _task(state=TASK_STATE_RUNNING, not_before=0.0)
        assert not is_eligible(task, 10.0)

    def test_completed_not_eligible(self):
        task = _task(state=TASK_STATE_COMPLETED, not_before=0.0)
        assert not is_eligible(task, 10.0)


class TestOrderEligible:
    def test_short_before_long(self):
        short = _task(priority=PRIORITY_SHORT, event_time=100.0)
        long = _task(priority=PRIORITY_LONG, event_time=1.0)
        ordered = order_eligible([long, short])
        assert ordered[0] is short
        assert ordered[1] is long

    def test_event_time_then_created_time(self):
        t1 = _task(event_time=10.0, created_time=5.0)
        t2 = _task(event_time=10.0, created_time=3.0)
        ordered = order_eligible([t1, t2])
        assert ordered[0] is t2  # earlier created time first

    def test_event_time_absent_uses_created_time(self):
        t1 = _task(event_time=None, created_time=10.0)
        t2 = _task(event_time=None, created_time=5.0)
        ordered = order_eligible([t1, t2])
        assert ordered[0] is t2


class TestClaimTask:
    def test_claim_succeeds(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=100.0)
        assert claim.worker_id == "w1"
        assert claim.fencing_generation == 1
        assert task.state == TASK_STATE_RUNNING
        assert state.get_claim(task_key_for_identity(task.identity)) is claim

    def test_double_claim_rejected(self):
        state = ExecutionState()
        task = _task()
        claim_task(state, task, "w1", expiry_time=500.0)
        # w2 cannot claim while w1's claim is still valid (not expired at w2's desired expiry time)
        try:
            claim_task(state, task, "w2", expiry_time=300.0)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for double claim")

    def test_expired_claim_can_be_taken_over(self):
        state = ExecutionState()
        task = _task()
        claim_task(state, task, "w1", expiry_time=50.0)
        # w2 can claim after expiry
        claim = claim_task(state, task, "w2", expiry_time=200.0)
        assert claim.worker_id == "w2"
        assert claim.fencing_generation == 2


class TestRenewClaim:
    def test_renew_succeeds(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=100.0)
        renewed = renew_claim(state, claim, new_expiry_time=500.0)
        assert renewed.expiry_time == 500.0
        assert renewed.fencing_generation == 1

    def test_renew_wrong_worker_rejected(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=100.0)
        try:
            renew_claim(state, claim, new_expiry_time=500.0)
            # claim.worker_id is w1, so this should succeed; test with different worker
            claim.worker_id = "w2"
            renew_claim(state, claim, new_expiry_time=500.0)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for wrong worker")

    def test_renew_nonexistent_claim_rejected(self):
        state = ExecutionState()
        identity = _identity()
        claim = Claim(
            task_identity=identity,
            worker_id="w1",
            expiry_time=100.0,
            fencing_generation=1,
        )
        try:
            renew_claim(state, claim, new_expiry_time=500.0)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for nonexistent claim")


class TestReleaseClaim:
    def test_release_removes_claim(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=100.0)
        release_claim(state, claim)
        assert state.get_claim(task_key_for_identity(task.identity)) is None


class TestIsClaimValid:
    def test_valid_claim(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=100.0)
        assert is_claim_valid(state, claim, now=50.0)

    def test_expired_claim_invalid(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=50.0)
        assert not is_claim_valid(state, claim, now=200.0)

    def test_wrong_worker_invalid(self):
        state = ExecutionState()
        task = _task()
        claim_task(state, task, "w1", expiry_time=100.0)
        other = Claim(
            task_identity=task.identity,
            worker_id="w2",
            expiry_time=200.0,
            fencing_generation=1,
        )
        assert not is_claim_valid(state, other, now=50.0)

    def test_stale_fencing_invalid(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=100.0)
        # A takeover bumps the fencing generation, making the old claim stale
        claim_task(state, task, "w2", expiry_time=200.0)
        assert not is_claim_valid(state, claim, now=50.0)


class TestTakeOverAfterExpiry:
    def test_takeover_after_expiry(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=50.0)
        assert take_over_after_expiry(state, claim, now=200.0)

    def test_no_takeover_before_expiry(self):
        state = ExecutionState()
        task = _task()
        claim = claim_task(state, task, "w1", expiry_time=200.0)
        assert not take_over_after_expiry(state, claim, now=50.0)

    def test_no_takeover_no_claim(self):
        state = ExecutionState()
        identity = _identity()
        claim = Claim(
            task_identity=identity,
            worker_id="w1",
            expiry_time=100.0,
            fencing_generation=1,
        )
        assert not take_over_after_expiry(state, claim, now=200.0)
