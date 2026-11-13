"""Unit tests for the SDD process service."""

from qnagym.contracts.sdd_process import (
    SDD_RESULT_INCOMPLETE,
    SDD_RESULT_SUCCESSFUL,
    SDD_TASK_STATE_ANALYZING,
    SDD_TASK_STATE_COMPLETED,
    SDD_TASK_STATE_SPECIFYING,
)
from qnagym.services.sdd_process import (
    advance_task,
    create_sdd_task,
    deliver_task,
)


class TestCreateSDDTask:
    def test_create_analyzing_task(self):
        task = create_sdd_task(
            task_id="t1",
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
            branch_name="feat/test",
        )
        assert task.identity.task_id == "t1"
        assert task.identity.source == "issue"
        assert task.identity.source_ref == "42"
        assert task.state == SDD_TASK_STATE_ANALYZING
        assert task.input.branch_name == "feat/test"

    def test_pr_originated_task(self):
        task = create_sdd_task(
            task_id="t2",
            source="pr",
            source_ref="10",
            accepted_requirements="requirements",
            pr_number=10,
        )
        assert task.identity.source == "pr"
        assert task.input.pr_number == 10


class TestAdvanceTask:
    def test_advance_from_analyzing(self):
        task = create_sdd_task(
            task_id="t1",
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
        )
        action = advance_task(task)
        assert action == "Specify"

    def test_advance_from_specifying(self):
        task = create_sdd_task(
            task_id="t1",
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
        )
        task.state = SDD_TASK_STATE_SPECIFYING
        action = advance_task(task)
        assert action == "UpdateContract"


class TestDeliverTask:
    def test_deliver_successful(self):
        task = create_sdd_task(
            task_id="t1",
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
            branch_name="feat/test",
            issue_number=42,
        )
        task.state = SDD_TASK_STATE_COMPLETED
        task.spec_changed = True
        task.tests_updated = True
        task.implementation_done = True
        task.traceability_updated = True
        task.local_verification_passed = True
        task.pr_diff_size = 100
        task.commit_sha = "abc123"

        result = deliver_task(task)
        assert result.result == SDD_RESULT_SUCCESSFUL
        assert result.commit_sha == "abc123"

    def test_deliver_incomplete(self):
        task = create_sdd_task(
            task_id="t1",
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
        )
        result = deliver_task(task)
        assert result.result == SDD_RESULT_INCOMPLETE
