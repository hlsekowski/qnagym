"""Acceptance scenario tests for SDD Process (ADR 0007 follow-up item 5).

Covers:
- Issue-originated SDD work (initial handoff from Issue Process)
- PR-feedback SDD work (subsequent handoff from PR Process)
- Successful delivery handoff to PR Process
- Incomplete delivery handoff to PR Process
"""

from qnagym.contracts.sdd_process import (
    SDD_RESULT_INCOMPLETE,
    SDD_RESULT_SUCCESSFUL,
    SDD_TASK_STATE_COMPLETED,
    SDD_TASK_STATE_INCOMPLETE,
    SDDTask,
    SDDTaskIdentity,
    SDDTaskInput,
)
from qnagym.services.sdd_process import deliver_task


def _make_task(
    state=SDD_TASK_STATE_COMPLETED,
    source="issue",
    source_ref="42",
    spec_changed=True,
    contract_changed=True,
    tests_updated=True,
    implementation_done=True,
    traceability_updated=True,
    local_verification_passed=True,
    pr_diff_size=100,
    pr_diff_limit=400,
    commit_sha="abc123",
    result=None,
):
    identity = SDDTaskIdentity(task_id="t1", source=source, source_ref=source_ref)
    input_data = SDDTaskInput(
        source=source,
        source_ref=source_ref,
        accepted_requirements="accepted requirements",
        accepted_input_revision="desc-hash-123",
        branch_name="feat/test",
        issue_number=42 if source == "issue" else None,
        pr_number=10 if source == "pr" else None,
        feedback_reference="feedback-c1" if source == "pr" else None,
    )
    return SDDTask(
        identity=identity,
        input=input_data,
        state=state,
        spec_changed=spec_changed,
        contract_changed=contract_changed,
        tests_updated=tests_updated,
        implementation_done=implementation_done,
        traceability_updated=traceability_updated,
        local_verification_passed=local_verification_passed,
        pr_diff_size=pr_diff_size,
        pr_diff_limit=pr_diff_limit,
        result=result,
        commit_sha=commit_sha,
    )


class TestIssueOriginatedSuccessfulHandoff:
    """Issue-originated SDD work with successful delivery."""

    def test_issue_originated_successful_delivery(self):
        task = _make_task(source="issue", source_ref="42")
        result = deliver_task(task)
        assert result.result == SDD_RESULT_SUCCESSFUL
        assert result.issue_number == 42
        assert result.pr_number is None
        assert result.branch_name == "feat/test"
        assert result.commit_sha == "abc123"
        assert result.local_verification == "passed"
        assert result.pr_diff_size == 100
        assert result.pr_diff_size <= result.pr_diff_limit
        assert "spec" in result.work_completed
        assert "contract" in result.work_completed
        assert "tests" in result.work_completed
        assert "implementation" in result.work_completed
        assert "traceability" in result.work_completed


class TestPRFeedbackSuccessfulHandoff:
    """PR-feedback SDD work with successful delivery."""

    def test_pr_feedback_successful_delivery(self):
        task = _make_task(source="pr", source_ref="10")
        result = deliver_task(task)
        assert result.result == SDD_RESULT_SUCCESSFUL
        assert result.issue_number is None
        assert result.pr_number == 10
        assert result.branch_name == "feat/test"
        assert result.commit_sha == "abc123"


class TestIncompleteHandoffMissingSteps:
    """Incomplete delivery: missing spec, tests, implementation."""

    def test_incomplete_missing_spec_and_tests(self):
        task = _make_task(
            spec_changed=False,
            tests_updated=False,
            implementation_done=False,
            local_verification_passed=False,
            pr_diff_size=50,
        )
        result = deliver_task(task)
        assert result.result == SDD_RESULT_INCOMPLETE
        assert "specification not updated" in result.diagnostics
        assert "tests not updated" in result.diagnostics
        assert "implementation not done" in result.diagnostics
        assert "local verification not passed" in result.diagnostics


class TestIncompleteHandoffDiffExceedsLimit:
    """Incomplete delivery: PR diff exceeds C2 limit."""

    def test_incomplete_diff_exceeds_limit(self):
        task = _make_task(
            pr_diff_size=500,
            pr_diff_limit=400,
        )
        result = deliver_task(task)
        assert result.result == SDD_RESULT_INCOMPLETE
        assert "exceeds limit" in result.diagnostics
        assert result.pr_diff_size == 500
        assert result.pr_diff_limit == 400


class TestIncompleteHandoffBeforePR:
    """Incomplete delivery reported before any PR exists."""

    def test_incomplete_before_pr_exists(self):
        task = _make_task(
            source="issue",
            source_ref="42",
            state=SDD_TASK_STATE_INCOMPLETE,
            spec_changed=False,
            tests_updated=False,
            implementation_done=False,
            local_verification_passed=False,
        )
        result = deliver_task(task)
        assert result.result == SDD_RESULT_INCOMPLETE
        assert result.issue_number == 42
        assert result.pr_number is None
        assert result.diagnostics != ""
