"""Unit tests for task execution model contracts."""

from qnagym.contracts.task_model import (
    PRIORITY_CLASSES,
    PRIORITY_LONG,
    PRIORITY_SHORT,
    TASK_KINDS,
    TASK_STATE_COMPLETED,
    TASK_STATE_FAILED,
    TASK_STATE_OBSOLETE,
    TASK_STATE_QUEUED,
    TASK_STATE_RUNNING,
    TASK_STATES,
    TERMINAL_STATES,
    Claim,
    ExecutionAttempt,
    ExecutionState,
    Task,
    TaskIdentity,
)


class TestTaskIdentity:
    def test_identity_roundtrip(self):
        identity = TaskIdentity(
            kind="issue_evaluation",
            work_item="42",
            target="branch-42",
            revision="rev-1",
            generation=2,
        )
        assert TaskIdentity.from_dict(identity.to_dict()) == identity

    def test_identity_default_generation(self):
        identity = TaskIdentity(kind="k", work_item=None, target="t", revision="r")
        assert identity.generation == 0


class TestTask:
    def test_task_roundtrip(self):
        identity = TaskIdentity(kind="k", work_item="1", target="t", revision="r")
        task = Task(
            identity=identity,
            created_time=100.0,
            not_before_time=110.0,
            event_time=105.0,
            state=TASK_STATE_QUEUED,
            priority=PRIORITY_SHORT,
            max_duration=300.0,
            retry_limit=3,
            attempt_count=0,
        )
        assert Task.from_dict(task.to_dict()) == task

    def test_is_terminal(self):
        identity = TaskIdentity(kind="k", work_item=None, target="t", revision="r")
        task = Task(identity=identity, created_time=1.0, not_before_time=1.0, event_time=None)
        assert not task.is_terminal
        task.state = TASK_STATE_COMPLETED
        assert task.is_terminal
        task.state = TASK_STATE_FAILED
        assert task.is_terminal
        task.state = TASK_STATE_OBSOLETE
        assert task.is_terminal
        task.state = TASK_STATE_RUNNING
        assert not task.is_terminal

    def test_is_eligible(self):
        identity = TaskIdentity(kind="k", work_item=None, target="t", revision="r")
        task = Task(
            identity=identity,
            created_time=1.0,
            not_before_time=10.0,
            event_time=None,
            state=TASK_STATE_QUEUED,
        )
        assert task.is_eligible  # state-based; not_before_time checked by domain layer
        task.state = TASK_STATE_RUNNING
        assert not task.is_eligible


class TestExecutionAttempt:
    def test_attempt_roundtrip(self):
        attempt = ExecutionAttempt(
            attempt_number=1,
            outcome="completed",
            retry_deadline=200.0,
            claim_id="c1",
        )
        assert ExecutionAttempt.from_dict(attempt.to_dict()) == attempt


class TestClaim:
    def test_claim_roundtrip(self):
        identity = TaskIdentity(kind="k", work_item="1", target="t", revision="r")
        claim = Claim(
            task_identity=identity,
            worker_id="w1",
            expiry_time=500.0,
            fencing_generation=3,
        )
        assert Claim.from_dict(claim.to_dict()) == claim

    def test_is_expired(self):
        identity = TaskIdentity(kind="k", work_item=None, target="t", revision="r")
        claim = Claim(
            task_identity=identity,
            worker_id="w1",
            expiry_time=100.0,
            fencing_generation=1,
        )
        assert claim.is_expired(now=200.0)
        assert not claim.is_expired(now=50.0)


class TestExecutionState:
    def test_state_roundtrip(self):
        state = ExecutionState()
        identity = TaskIdentity(kind="k", work_item="1", target="t", revision="r")
        task = Task(identity=identity, created_time=1.0, not_before_time=1.0, event_time=None)
        state.put_task(task)
        state.increment_generation()
        assert state.generation_counter == 1
        assert state.get_task(identity) is task

    def test_task_key(self):
        state = ExecutionState()
        identity = TaskIdentity(kind="k", work_item="1", target="t", revision="r", generation=2)
        key = state.task_key(identity)
        assert key == "k|1|t|r|2"

    def test_increment_generation(self):
        state = ExecutionState()
        assert state.increment_generation() == 1
        assert state.increment_generation() == 2

    def test_claim_put_get_remove(self):
        state = ExecutionState()
        identity = TaskIdentity(kind="k", work_item=None, target="t", revision="r")
        claim = Claim(
            task_identity=identity,
            worker_id="w1",
            expiry_time=100.0,
            fencing_generation=1,
        )
        state.put_claim(claim)
        key = state.task_key(identity)
        assert state.get_claim(key) is claim
        state.remove_claim(key)
        assert state.get_claim(key) is None

    def test_attempts_add_get(self):
        state = ExecutionState()
        identity = TaskIdentity(kind="k", work_item=None, target="t", revision="r")
        attempt = ExecutionAttempt(attempt_number=1)
        state.add_attempt(identity, attempt)
        assert state.get_attempts(identity) == [attempt]

    def test_state_dict_roundtrip(self):
        state = ExecutionState()
        identity = TaskIdentity(kind="k", work_item="1", target="t", revision="r")
        task = Task(identity=identity, created_time=1.0, not_before_time=1.0, event_time=None)
        state.put_task(task)
        state.increment_generation()
        restored = ExecutionState.from_dict(state.to_dict())
        assert restored.generation_counter == 1
        assert restored.get_task(identity) is not None
        assert restored.get_task(identity).identity == identity


class TestConstants:
    def test_task_kinds(self):
        assert "issue_evaluation" in TASK_KINDS
        assert "observation" in TASK_KINDS
        assert len(TASK_KINDS) == 6

    def test_task_states(self):
        assert TASK_STATE_QUEUED in TASK_STATES
        assert TASK_STATE_RUNNING in TASK_STATES
        assert TASK_STATE_COMPLETED in TASK_STATES
        assert TASK_STATE_FAILED in TASK_STATES
        assert TASK_STATE_OBSOLETE in TASK_STATES

    def test_priority_classes(self):
        assert PRIORITY_SHORT in PRIORITY_CLASSES
        assert PRIORITY_LONG in PRIORITY_CLASSES

    def test_terminal_states(self):
        assert TASK_STATE_COMPLETED in TERMINAL_STATES
        assert TASK_STATE_FAILED in TERMINAL_STATES
        assert TASK_STATE_OBSOLETE in TERMINAL_STATES
        assert TASK_STATE_QUEUED not in TERMINAL_STATES
        assert TASK_STATE_RUNNING not in TERMINAL_STATES
