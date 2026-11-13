"""Unit tests for the PR notification service."""

import pytest

from qnagym.contracts.constants import WORKFLOW_COMMENT_MARKER
from qnagym.contracts.pr_process import PRMessage
from qnagym.services.pr_notifications import (
    PRNotificationError,
    is_own_comment,
    notify,
    surface_for,
)


def message(kind: str = "CheckResults") -> PRMessage:
    return PRMessage(
        target=kind,
        what_happened="lint failed",
        evidence="lint job",
        decision="correcting",
        completed="diagnosis",
        pending="fix",
        automation_state="attempt 1 of 5",
        user_next_step="none",
    )


class TestRouting:
    def test_issue_clarification_goes_to_the_issue(self):
        assert surface_for("IssueClarification") == "IssueComment"

    def test_feedback_clarification_goes_to_the_pr(self):
        assert surface_for("FeedbackClarification") == "PRComment"

    def test_check_results_go_to_the_pr(self):
        assert surface_for("CheckResults") == "PRComment"

    def test_lifecycle_failures_go_to_the_pr(self):
        assert surface_for("LifecycleFailure") == "PRComment"

    def test_scope_change_goes_to_the_linked_issue(self):
        assert surface_for("ScopeChange") == "ScopeChangeNotice"

    def test_unknown_kind_raises(self):
        with pytest.raises(PRNotificationError, match="unknown message kind"):
            surface_for("Bogus")


class TestRendering:
    def test_message_carries_the_marker(self):
        routed = notify(message())
        assert routed.body.startswith(WORKFLOW_COMMENT_MARKER)
        assert routed.is_workflow_authored

    def test_message_covers_every_required_section(self):
        body = notify(message()).body
        for section in (
            "What happened",
            "Evidence",
            "Decision",
            "Completed",
            "Pending",
            "Automation state",
            "Next step for you",
        ):
            assert section in body

    def test_message_includes_the_values(self):
        body = notify(message()).body
        assert "lint failed" in body
        assert "attempt 1 of 5" in body

    def test_target_is_the_surface_not_the_kind(self):
        routed = notify(message("ScopeChange"))
        assert routed.target == "ScopeChangeNotice"

    def test_unknown_kind_raises_on_notify(self):
        with pytest.raises(PRNotificationError, match="unknown message kind"):
            notify(message("Bogus"))


class TestSelfDetection:
    def test_workflow_comment_is_recognised(self):
        assert is_own_comment(notify(message()).body)

    def test_human_comment_is_not(self):
        assert not is_own_comment("please fix the typo")

    def test_marker_alone_is_recognised(self):
        assert is_own_comment(WORKFLOW_COMMENT_MARKER)
