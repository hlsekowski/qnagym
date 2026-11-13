"""Unit tests for issue process contracts."""

from qnagym.contracts.issue_process import (
    EVALUATION_FAIL,
    EVALUATION_INCONSISTENT,
    EVALUATION_PASS,
    ISSUE_STATE_PENDING,
    ISSUE_STATE_SEALED,
    TERMINAL_ISSUE_STATES,
    DecisionRecord,
    Issue,
    IssueDecision,
    IssueEvaluation,
    IssueIdentity,
)


class TestIssueIdentity:
    def test_identity_roundtrip(self):
        identity = IssueIdentity(number=42, repository="hlsekowski/qnagym")
        assert IssueIdentity.from_dict(identity.to_dict()) == identity


class TestIssue:
    def test_issue_roundtrip(self):
        identity = IssueIdentity(number=42, repository="hlsekowski/qnagym")
        issue = Issue(
            identity=identity,
            title="Test issue",
            description="description",
            description_hash="abc123",
            state=ISSUE_STATE_PENDING,
        )
        assert Issue.from_dict(issue.to_dict()) == issue

    def test_is_terminal(self):
        identity = IssueIdentity(number=1, repository="r")
        issue = Issue(identity=identity, title="t", description="d", description_hash="h")
        assert not issue.is_terminal
        issue.state = "Withdrawn"
        assert issue.is_terminal
        issue.state = "Excluded"
        assert issue.is_terminal

    def test_is_sealed(self):
        identity = IssueIdentity(number=1, repository="r")
        issue = Issue(identity=identity, title="t", description="d", description_hash="h")
        assert not issue.is_sealed
        issue.state = ISSUE_STATE_SEALED
        assert issue.is_sealed


class TestIssueEvaluation:
    def test_evaluation_roundtrip(self):
        evaluation = IssueEvaluation(
            result="Pass",
            confidence=0.98,
            reason="clear",
            clarity_pass=True,
            consistency_pass=True,
            change_type="feat",
            has_goal=True,
            has_acceptance_criteria=True,
            has_change_type=True,
            scope_fits_one_pr=True,
            no_contradictions=True,
            consistent_with_constitution=True,
            consistent_with_rules=True,
            consistent_with_spec=True,
            consistent_with_adrs=True,
            input_revision="abc123",
            input_type="description",
        )
        assert IssueEvaluation.from_dict(evaluation.to_dict()) == evaluation


class TestDecisionRecord:
    def test_decision_record_roundtrip(self):
        record = DecisionRecord(
            decision_id="dr-1",
            input_revision="abc123",
            input_type="description",
            decision="accept",
            confidence=0.98,
            reason="clear and consistent",
            clarity_pass=True,
            consistency_pass=True,
            gate_passed=True,
            created_at=100.0,
        )
        assert DecisionRecord.from_dict(record.to_dict()) == record

    def test_decision_record_defaults(self):
        record = DecisionRecord(
            decision_id="dr-1",
            input_revision="abc123",
            input_type="description",
            decision="clarify",
            confidence=0.5,
            reason="unclear",
            clarity_pass=False,
            consistency_pass=True,
            gate_passed=False,
            created_at=100.0,
        )
        assert record.decision_id == "dr-1"
        assert record.input_type == "description"
        assert not record.gate_passed


class TestIssueDecision:
    def test_decision_roundtrip(self):
        decision = IssueDecision(
            action="AcceptAndSeal",
            reason="accepted",
            seal=True,
            create_branch=True,
            branch_name="feat/test",
            comment="sealed",
        )
        d = IssueDecision.from_dict(decision.to_dict())
        assert d.action == "AcceptAndSeal"
        assert d.invokes_sdd

    def test_invokes_sdd(self):
        decision = IssueDecision(action="x", reason="y", seal=True, create_branch=True)
        assert decision.invokes_sdd

        decision = IssueDecision(action="x", reason="y", seal=True, create_branch=False)
        assert not decision.invokes_sdd

        decision = IssueDecision(action="x", reason="y", seal=False, create_branch=True)
        assert not decision.invokes_sdd


class TestConstants:
    def test_terminal_states(self):
        assert "Withdrawn" in TERMINAL_ISSUE_STATES
        assert "Excluded" in TERMINAL_ISSUE_STATES
        assert ISSUE_STATE_PENDING not in TERMINAL_ISSUE_STATES

    def test_evaluation_results(self):
        assert EVALUATION_PASS == "Pass"
        assert EVALUATION_FAIL == "Fail"
        assert EVALUATION_INCONSISTENT == "Inconsistent"
