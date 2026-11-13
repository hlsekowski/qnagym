"""Unit tests for the issue process service."""

from qnagym.contracts.issue_process import (
    IssueEvaluation,
)
from qnagym.services.issue_process import (
    accept_and_seal,
    create_issue,
    evaluate_and_decide,
)


class TestCreateIssue:
    def test_create_pending_issue(self):
        issue = create_issue(
            number=42,
            repository="hlsekowski/qnagym",
            title="Test issue",
            description="description",
        )
        assert issue.identity.number == 42
        assert issue.identity.repository == "hlsekowski/qnagym"
        assert issue.title == "Test issue"
        assert issue.state == "Pending"
        assert issue.description_hash != ""

    def test_exception_issue(self):
        issue = create_issue(
            number=1,
            repository="r",
            title="t",
            description="d",
            is_exception=True,
        )
        assert issue.is_exception

    def test_reopened_issue(self):
        issue = create_issue(
            number=1,
            repository="r",
            title="t",
            description="d",
            is_reopened=True,
        )
        assert issue.is_reopened


class TestEvaluateAndDecide:
    def test_pass_accepts_and_seals(self):
        issue = create_issue(1, "r", "t", "d")
        decision = evaluate_and_decide(
            issue,
            description="d",
            change_type="feat",
            confidence=0.98,
            clarity_pass=True,
            consistency_pass=True,
            now=100.0,
        )
        assert decision.action == "AcceptAndSeal"
        assert decision.seal
        assert decision.create_branch

    def test_fail_requests_clarification(self):
        issue = create_issue(1, "r", "t", "d")
        decision = evaluate_and_decide(
            issue,
            description="d",
            change_type=None,
            confidence=0.98,
            clarity_pass=False,
            consistency_pass=True,
            now=100.0,
        )
        assert decision.action == "RequestClarification"
        assert not decision.seal

    def test_reopened_excluded(self):
        issue = create_issue(1, "r", "t", "d", is_reopened=True)
        decision = evaluate_and_decide(
            issue,
            description="d",
            change_type="feat",
            confidence=0.98,
            clarity_pass=True,
            consistency_pass=True,
            now=100.0,
        )
        assert decision.action == "ExcludeReopened"


class TestAcceptAndSeal:
    def test_accept_and_seal(self):
        issue = create_issue(1, "r", "t", "d")
        evaluation = IssueEvaluation(
            result="Pass",
            confidence=0.98,
            reason="clear",
            clarity_pass=True,
            consistency_pass=True,
        )
        decision = accept_and_seal(issue, evaluation, branch_name="feat/test")
        assert decision.action == "AcceptAndSeal"
        assert decision.seal
        assert decision.create_branch
        assert decision.branch_name == "feat/test"
