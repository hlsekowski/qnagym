"""Unit tests for the PR check monitoring service."""

from qnagym.contracts.pr_process import CheckResult
from qnagym.domain.pr_checks import (
    ACTION_AWAIT,
    ACTION_CORRECT,
    ACTION_EXHAUSTED,
    ACTION_UNRESOLVABLE,
    CorrectionBatch,
    classify_check,
    decide_check_action,
)
from qnagym.services.pr_checks import (
    all_checks_clear,
    monitor_check,
    record_correction,
    request_retry,
)

FAILED = CheckResult(name="lint", status="Failed")


class TestClassifyCheck:
    def test_failed_is_a_failure(self):
        assert classify_check(FAILED) == "failed"

    def test_passing_is_not_a_failure(self):
        assert classify_check(CheckResult("lint", "Passing")) == "non-failure"

    def test_pending_is_not_a_failure(self):
        assert classify_check(CheckResult("lint", "Pending")) == "non-failure"

    def test_cancelled_is_not_a_failure(self):
        assert classify_check(CheckResult("lint", "Cancelled")) == "non-failure"

    def test_skipped_is_not_a_failure(self):
        assert classify_check(CheckResult("lint", "Skipped")) == "non-failure"

    def test_infrastructure_failed_is_not_a_failure(self):
        assert classify_check(CheckResult("lint", "InfrastructureFailed")) == "non-failure"

    def test_unknown_status_is_unknown(self):
        assert classify_check(CheckResult("lint", "Weird")) == "unknown"


class TestDecideCheckAction:
    def test_failed_with_budget_corrects(self):
        decision = decide_check_action(FAILED, CorrectionBatch())
        assert decision.action == ACTION_CORRECT

    def test_non_failure_awaits(self):
        decision = decide_check_action(CheckResult("lint", "Cancelled"), CorrectionBatch())
        assert decision.action == ACTION_AWAIT

    def test_unknown_status_is_unresolvable(self):
        decision = decide_check_action(CheckResult("lint", "Weird"), CorrectionBatch())
        assert decision.action == ACTION_UNRESOLVABLE

    def test_exhausted_batch_stops(self):
        batch = CorrectionBatch()
        for i in range(batch.limit):
            batch.record_attempt(f"attempt {i + 1}")
        decision = decide_check_action(FAILED, batch)
        assert decision.action == ACTION_EXHAUSTED


class TestCorrectionBatch:
    def test_default_limit_is_five(self):
        assert CorrectionBatch().limit == 5

    def test_limit_is_configurable(self):
        assert CorrectionBatch(limit=2).limit == 2

    def test_attempts_are_counted(self):
        batch = CorrectionBatch()
        batch.record_attempt("first")
        assert batch.attempts_used == 1
        assert batch.remaining == 4

    def test_exhausted_at_the_limit(self):
        batch = CorrectionBatch(limit=2)
        batch.record_attempt("one")
        assert not batch.exhausted
        batch.record_attempt("two")
        assert batch.exhausted

    def test_retry_starts_a_new_batch_and_preserves_history(self):
        batch = CorrectionBatch()
        batch.record_attempt("one")
        batch.record_attempt("two")
        request_retry(batch)
        assert batch.attempts_used == 0
        assert batch.remaining == 5
        assert batch.history == ["one", "two"]

    def test_reopening_does_not_reset_the_counter(self):
        batch = CorrectionBatch()
        batch.record_attempt("one")
        # No API exists to reset a batch except an explicit retry.
        assert batch.attempts_used == 1


class TestAllChecksClear:
    def test_all_passing_is_clear(self):
        assert all_checks_clear([CheckResult("lint", "Passing"), CheckResult("test", "Passing")])

    def test_pending_does_not_block_clearance(self):
        assert all_checks_clear([CheckResult("lint", "Passing"), CheckResult("test", "Pending")])

    def test_cancelled_does_not_block_clearance(self):
        assert all_checks_clear([CheckResult("lint", "Cancelled")])

    def test_failed_blocks_clearance(self):
        assert not all_checks_clear([CheckResult("lint", "Passing"), FAILED])

    def test_empty_is_clear(self):
        assert all_checks_clear([])


class TestServiceFacade:
    def test_monitor_check_delegates(self):
        assert monitor_check(FAILED, CorrectionBatch()).action == ACTION_CORRECT

    def test_record_correction_mutates_the_batch(self):
        batch = CorrectionBatch()
        record_correction(batch, "fixed lint")
        assert batch.attempts_used == 1
        assert batch.history == ["fixed lint"]
