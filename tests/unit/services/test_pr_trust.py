"""Unit tests for the PR trust boundary service."""

import pytest

from qnagym.contracts.constants import WORKFLOW_COMMENT_MARKER
from qnagym.contracts.pr_process import FeedbackEvent
from qnagym.domain.pr_trust import TrustPolicy, is_processable, is_workflow_authored
from qnagym.services.pr_trust import (
    FEEDBACK,
    INTAKE,
    RETRY,
    PRTrustError,
    accept_feedback,
    accept_intake,
    accept_retry,
    authorize,
)

POLICY = TrustPolicy(
    owner="hlsekowski",
    collaborators={"alice"},
    automated_reviewers={"coderabbit"},
)


def event(author: str = "alice", body: str = "fix the typo") -> FeedbackEvent:
    return FeedbackEvent(event_type="Review", author=author, body=body, comment_id="c1")


class TestAuthorization:
    def test_owner_is_authorized(self):
        assert POLICY.is_authorized("hlsekowski", INTAKE)

    def test_collaborator_is_authorized(self):
        assert POLICY.is_authorized("alice", FEEDBACK)

    def test_stranger_is_not_authorized(self):
        assert not POLICY.is_authorized("mallory", FEEDBACK)

    def test_configured_reviewer_may_give_feedback(self):
        assert POLICY.is_authorized("coderabbit", FEEDBACK)

    def test_reviewer_may_not_supply_intake(self):
        assert not POLICY.is_authorized("coderabbit", INTAKE)

    def test_reviewer_may_not_request_retry(self):
        assert not POLICY.is_authorized("coderabbit", RETRY)

    def test_unconfigured_reviewer_is_ignored(self):
        assert not POLICY.is_authorized("unknownbot", FEEDBACK)

    def test_authorize_raises_for_stranger(self):
        with pytest.raises(PRTrustError, match="unauthorized author"):
            authorize(POLICY, "mallory", FEEDBACK)


class TestFeedbackGate:
    def test_authorized_feedback_is_accepted(self):
        assert accept_feedback(POLICY, event()) is not None

    def test_stranger_feedback_is_rejected(self):
        with pytest.raises(PRTrustError, match="unauthorized author"):
            accept_feedback(POLICY, event(author="mallory"))

    def test_workflow_authored_body_is_not_input(self):
        with pytest.raises(PRTrustError, match="not input"):
            accept_feedback(POLICY, event(body=f"{WORKFLOW_COMMENT_MARKER}\nsummary"))


class TestRetryGate:
    def test_authorized_retry_is_accepted(self):
        accept_retry(POLICY, "alice", "please retry")

    def test_stranger_retry_is_rejected(self):
        with pytest.raises(PRTrustError, match="unauthorized author"):
            accept_retry(POLICY, "mallory", "please retry")

    def test_workflow_authored_retry_is_rejected(self):
        with pytest.raises(PRTrustError, match="not input"):
            accept_retry(POLICY, "alice", WORKFLOW_COMMENT_MARKER)


class TestIntakeGate:
    def test_owner_intake_is_accepted(self):
        accept_intake(POLICY, "hlsekowski")

    def test_stranger_intake_is_rejected(self):
        with pytest.raises(PRTrustError, match="unauthorized author"):
            accept_intake(POLICY, "mallory")


class TestMarkerDetection:
    def test_marked_body_is_workflow_authored(self):
        assert is_workflow_authored(f"{WORKFLOW_COMMENT_MARKER}\nsummary")

    def test_human_body_is_not(self):
        assert not is_workflow_authored("please fix the typo")

    def test_marked_body_is_not_processable(self):
        assert not is_processable(WORKFLOW_COMMENT_MARKER)

    def test_human_body_is_processable(self):
        assert is_processable("please fix the typo")
