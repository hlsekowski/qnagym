"""Unit tests for the issue process domain logic."""

from qnagym.contracts.constants import CONFIDENCE_SHOW_BELOW
from qnagym.contracts.issue_process import (
    ACTION_ACCEPT_AND_SEAL,
    ACTION_EXCLUDE_REOPENED,
    ACTION_NONE,
    ACTION_POST_REOPENED_NOTICE,
    ACTION_POST_SEALED_EDIT_NOTICE,
    ACTION_REPORT_AMBIGUOUS_LINK,
    ACTION_REQUEST_CLARIFICATION,
    ACTION_WITHDRAW,
    ISSUE_STATE_PENDING,
    ISSUE_STATE_SEALED,
    Issue,
    IssueEvaluation,
    IssueIdentity,
)
from qnagym.domain.issue_process import (
    decide_issue,
    evaluate_issue,
    handle_description_edit,
    handle_issue_closed,
    handle_reopened_issue,
)


def _identity(number=42, repository="hlsekowski/qnagym"):
    return IssueIdentity(number=number, repository=repository)


def _issue(
    identity=None,
    state=ISSUE_STATE_PENDING,
    is_reopened=False,
    is_exception=False,
    sealed=False,
):
    if identity is None:
        identity = _identity()
    return Issue(
        identity=identity,
        title="Test issue",
        description="description",
        description_hash="abc123",
        state=ISSUE_STATE_SEALED if sealed else state,
        is_reopened=is_reopened,
        is_exception=is_exception,
        sealed_description="sealed desc" if sealed else None,
        sealed_description_hash="sealed-hash" if sealed else None,
    )


def _evaluation(
    result="Pass",
    confidence=0.98,
    clarity_pass=True,
    consistency_pass=True,
    change_type="feat",
):
    return IssueEvaluation(
        result=result,
        confidence=confidence,
        reason="reason",
        clarity_pass=clarity_pass,
        consistency_pass=consistency_pass,
        change_type=change_type,
    )


class TestEvaluateIssue:
    def test_pass(self):
        evaluation = evaluate_issue(
            description="desc",
            change_type="feat",
            confidence=0.98,
            clarity_pass=True,
            consistency_pass=True,
        )
        assert evaluation.result == "Pass"
        assert evaluation.clarity_pass
        assert evaluation.consistency_pass

    def test_clarity_fail(self):
        evaluation = evaluate_issue(
            description="desc",
            change_type=None,
            confidence=0.98,
            clarity_pass=False,
            consistency_pass=True,
        )
        assert evaluation.result == "Fail"
        assert "clarity" in evaluation.reason

    def test_consistency_fail(self):
        evaluation = evaluate_issue(
            description="desc",
            change_type="feat",
            confidence=0.98,
            clarity_pass=True,
            consistency_pass=False,
        )
        assert evaluation.result == "Inconsistent"
        assert "consistency" in evaluation.reason

    def test_confidence_at_threshold_fails(self):
        evaluation = evaluate_issue(
            description="desc",
            change_type="feat",
            confidence=CONFIDENCE_SHOW_BELOW,
            clarity_pass=True,
            consistency_pass=True,
        )
        assert evaluation.result == "Fail"
        assert "threshold" in evaluation.reason

    def test_confidence_above_threshold_passes(self):
        evaluation = evaluate_issue(
            description="desc",
            change_type="feat",
            confidence=CONFIDENCE_SHOW_BELOW + 0.01,
            clarity_pass=True,
            consistency_pass=True,
        )
        assert evaluation.result == "Pass"


class TestDecideIssue:
    def test_accept_and_seal(self):
        issue = _issue()
        evaluation = _evaluation()
        decision = decide_issue(issue, evaluation, now=100.0)
        assert decision.action == ACTION_ACCEPT_AND_SEAL
        assert decision.seal
        assert decision.create_branch
        assert decision.branch_name == "feat/test-issue"

    def test_request_clarification(self):
        issue = _issue()
        evaluation = _evaluation(result="Fail", clarity_pass=False)
        decision = decide_issue(issue, evaluation, now=100.0)
        assert decision.action == ACTION_REQUEST_CLARIFICATION
        assert not decision.seal

    def test_reopened_excluded(self):
        issue = _issue(is_reopened=True)
        evaluation = _evaluation()
        decision = decide_issue(issue, evaluation, now=100.0)
        assert decision.action == ACTION_EXCLUDE_REOPENED
        assert not decision.seal

    def test_exception_excluded(self):
        issue = _issue(is_exception=True)
        evaluation = _evaluation()
        decision = decide_issue(issue, evaluation, now=100.0)
        assert decision.action == ACTION_NONE

    def test_ambiguous_link_reported(self):
        issue = _issue()
        evaluation = _evaluation(result="Ambiguous")
        decision = decide_issue(issue, evaluation, now=100.0)
        assert decision.action == ACTION_REPORT_AMBIGUOUS_LINK

    def test_branch_name_from_change_type(self):
        issue = _issue()
        issue.title = "Add new feature"
        evaluation = _evaluation(change_type="feat")
        decision = decide_issue(issue, evaluation, now=100.0)
        assert decision.branch_name == "feat/add-new-feature"


class TestHandleDescriptionEdit:
    def test_edit_schedules_evaluation(self):
        issue = _issue()
        decision = handle_description_edit(issue, "new desc", "new-hash", now=100.0)
        assert decision.action == ACTION_NONE
        assert decision.scheduled_evaluation_at == 100.0 + 20.0 * 3600

    def test_edit_to_sealed_issues_notice(self):
        issue = _issue(sealed=True)
        decision = handle_description_edit(issue, "new desc", "new-hash", now=100.0)
        assert decision.action == ACTION_POST_SEALED_EDIT_NOTICE
        assert "sealed" in decision.comment.lower()


class TestHandleReopenedIssue:
    def test_reopened_not_processed(self):
        issue = _issue()
        decision = handle_reopened_issue(issue)
        assert decision.action == ACTION_POST_REOPENED_NOTICE
        assert "reopened" in decision.comment.lower()


class TestHandleIssueClosed:
    def test_closed_before_pr_withdraws(self):
        issue = _issue()
        decision = handle_issue_closed(issue, pr_exists=False)
        assert decision.action == ACTION_WITHDRAW

    def test_closed_with_pr_open_does_not_withdraw(self):
        issue = _issue()
        decision = handle_issue_closed(issue, pr_exists=True)
        assert decision.action == ACTION_NONE
