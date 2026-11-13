"""Unit tests for the PR lifecycle service."""

import pytest

from qnagym.domain.pr_lifecycle import (
    EVENT_CHECKS_PASS_CLEAR,
    EVENT_CHECKS_PASS_PENDING,
    EVENT_CHECKS_PENDING,
    EVENT_CLARIFICATION_RESOLVED,
    EVENT_ISSUE_CLOSED,
    EVENT_NEW_FEEDBACK,
    EVENT_POST_MERGE_FAILED,
    EVENT_POST_MERGE_OK,
    EVENT_POST_MERGE_STARTED,
    EVENT_PR_CLOSED,
    EVENT_PR_MERGED,
    EVENT_PR_REOPENED,
    PRLifecycle,
)
from qnagym.services.pr_lifecycle import (
    PRLifecycleError,
    apply_event,
    complete_post_merge_step,
)


class TestMonitoringTransitions:
    def test_starts_in_monitoring(self):
        assert PRLifecycle().state == "Monitoring"

    def test_pending_checks_stay_in_monitoring(self):
        lifecycle = PRLifecycle()
        assert apply_event(lifecycle, EVENT_CHECKS_PENDING) == "Monitoring"

    def test_checks_pass_clear(self):
        lifecycle = PRLifecycle()
        assert apply_event(lifecycle, EVENT_CHECKS_PASS_CLEAR) == "ChecksPassClear"

    def test_checks_pass_pending(self):
        lifecycle = PRLifecycle()
        assert apply_event(lifecycle, EVENT_CHECKS_PASS_PENDING) == "ChecksPassPending"

    def test_closed_without_merge_is_an_anomaly(self):
        lifecycle = PRLifecycle()
        assert apply_event(lifecycle, EVENT_PR_CLOSED) == "ClosedAnomaly"

    def test_merged(self):
        lifecycle = PRLifecycle()
        assert apply_event(lifecycle, EVENT_PR_MERGED) == "Merged"

    def test_issue_closed_while_open_warns_and_continues(self):
        lifecycle = PRLifecycle()
        assert apply_event(lifecycle, EVENT_ISSUE_CLOSED) == "Monitoring"


class TestResumption:
    def test_new_feedback_returns_to_monitoring(self):
        lifecycle = PRLifecycle()
        apply_event(lifecycle, EVENT_CHECKS_PASS_CLEAR)
        assert apply_event(lifecycle, EVENT_NEW_FEEDBACK) == "Monitoring"

    def test_clarification_resolved_returns_to_monitoring(self):
        lifecycle = PRLifecycle()
        apply_event(lifecycle, EVENT_CHECKS_PASS_PENDING)
        assert apply_event(lifecycle, EVENT_CLARIFICATION_RESOLVED) == "Monitoring"

    def test_reopened_pr_resumes_monitoring(self):
        lifecycle = PRLifecycle()
        apply_event(lifecycle, EVENT_PR_CLOSED)
        assert apply_event(lifecycle, EVENT_PR_REOPENED) == "Monitoring"


class TestPostMerge:
    def test_both_steps_required_for_done(self):
        lifecycle = PRLifecycle()
        apply_event(lifecycle, EVENT_PR_MERGED)
        apply_event(lifecycle, EVENT_POST_MERGE_STARTED)
        complete_post_merge_step(lifecycle, "issue_closed")
        assert not lifecycle.post_merge_complete
        complete_post_merge_step(lifecycle, "local_synced")
        assert lifecycle.post_merge_complete
        assert apply_event(lifecycle, EVENT_POST_MERGE_OK) == "Done"

    def test_failure_blocks_and_retry_covers_only_the_missing_step(self):
        lifecycle = PRLifecycle()
        apply_event(lifecycle, EVENT_PR_MERGED)
        apply_event(lifecycle, EVENT_POST_MERGE_STARTED)
        complete_post_merge_step(lifecycle, "issue_closed")
        assert apply_event(lifecycle, EVENT_POST_MERGE_FAILED) == "PostMergeBlocked"
        assert lifecycle.outstanding_post_merge_steps == ("local_synced",)
        assert apply_event(lifecycle, EVENT_POST_MERGE_OK) == "PostMerge"
        complete_post_merge_step(lifecycle, "local_synced")
        assert apply_event(lifecycle, EVENT_POST_MERGE_OK) == "Done"

    def test_unknown_step_is_rejected(self):
        lifecycle = PRLifecycle()
        with pytest.raises(PRLifecycleError, match="unknown post-merge step"):
            complete_post_merge_step(lifecycle, "bogus")


class TestInvalidEvents:
    def test_invalid_event_in_state_raises(self):
        lifecycle = PRLifecycle()
        with pytest.raises(PRLifecycleError, match="not valid in state"):
            apply_event(lifecycle, EVENT_POST_MERGE_OK)

    def test_done_is_terminal(self):
        lifecycle = PRLifecycle()
        apply_event(lifecycle, EVENT_PR_MERGED)
        apply_event(lifecycle, EVENT_POST_MERGE_STARTED)
        complete_post_merge_step(lifecycle, "issue_closed")
        complete_post_merge_step(lifecycle, "local_synced")
        apply_event(lifecycle, EVENT_POST_MERGE_OK)
        with pytest.raises(PRLifecycleError):
            apply_event(lifecycle, EVENT_NEW_FEEDBACK)
