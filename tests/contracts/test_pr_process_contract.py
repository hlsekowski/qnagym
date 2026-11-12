"""Contract tests for the PR Process."""

from qnagym.contracts.constants import CONFIDENCE_SHOW_BELOW
from qnagym.contracts.pr_process import (
    CHECK_STATUSES,
    CORRECTION_ATTEMPT_STEPS,
    EVALUATION_RESULTS,
    FEEDBACK_EVENT_TYPES,
    MAX_CORRECTION_ATTEMPTS_PER_BATCH,
    MESSAGE_ROUTING_TARGETS,
    NON_FAILURE_CHECK_STATUSES,
    PR_LIFECYCLE_EVENTS,
    PR_LIFECYCLE_STATES,
    WORKFLOW_COMMENT_MARKER,
    CheckResult,
    CorrectionAttempt,
    EvaluationResult,
    FeedbackEvent,
    PRMessage,
)


class TestVocabularies:
    def test_feedback_event_types(self):
        assert set(FEEDBACK_EVENT_TYPES) == {
            "ConversationComment",
            "Review",
            "InlineComment",
            "Reply",
        }

    def test_evaluation_results(self):
        assert set(EVALUATION_RESULTS) == {
            "ClearActionable",
            "Ambiguous",
            "ScopeChange",
            "Conflict",
            "NoAction",
        }

    def test_check_statuses(self):
        assert set(CHECK_STATUSES) == {
            "Passing",
            "Pending",
            "Running",
            "Failed",
            "Cancelled",
            "Skipped",
            "InfrastructureFailed",
            "ExternallyBlocked",
        }

    def test_non_failure_statuses_are_a_subset_of_check_statuses(self):
        assert NON_FAILURE_CHECK_STATUSES < CHECK_STATUSES
        assert "Failed" not in NON_FAILURE_CHECK_STATUSES

    def test_correction_attempt_steps(self):
        assert set(CORRECTION_ATTEMPT_STEPS) == {
            "Diagnosis",
            "Fix",
            "LocalVerification",
            "Push",
            "Observe",
        }

    def test_batch_limit(self):
        assert MAX_CORRECTION_ATTEMPTS_PER_BATCH == 5

    def test_lifecycle_states(self):
        assert set(PR_LIFECYCLE_STATES) == {
            "Monitoring",
            "ChecksPassClear",
            "ChecksPassPending",
            "ClosedAnomaly",
            "Merged",
            "PostMerge",
            "PostMergeBlocked",
            "Done",
        }

    def test_lifecycle_events(self):
        assert set(PR_LIFECYCLE_EVENTS) == {
            "CheckResult",
            "Feedback",
            "PRClosed",
            "PRReopened",
            "IssueClosed",
            "PRMerged",
            "PostMergeStepResult",
        }

    def test_message_routing_targets(self):
        assert set(MESSAGE_ROUTING_TARGETS) == {
            "IssueComment",
            "PRComment",
            "ScopeChangeNotice",
        }

    def test_comment_marker_is_an_html_comment(self):
        assert WORKFLOW_COMMENT_MARKER.startswith("<!--")
        assert WORKFLOW_COMMENT_MARKER.endswith("-->")


class TestFeedbackEvent:
    def test_roundtrip(self):
        event = FeedbackEvent(
            event_type="Review",
            author="owner",
            body="please fix the typo",
            comment_id="c1",
        )
        assert FeedbackEvent.from_dict(event.to_dict()) == event

    def test_event_type_is_in_the_vocabulary(self):
        assert FeedbackEvent("Reply", "owner", "text", "c2").event_type in FEEDBACK_EVENT_TYPES


class TestEvaluationResult:
    def test_roundtrip(self):
        result = EvaluationResult(result="ClearActionable", confidence=0.98, reason="clear")
        assert EvaluationResult.from_dict(result.to_dict()) == result

    def test_confidence_uses_the_shared_threshold(self):
        assert CONFIDENCE_SHOW_BELOW == 0.95


class TestCheckResult:
    def test_roundtrip(self):
        check = CheckResult(name="lint", status="Failed")
        assert CheckResult.from_dict(check.to_dict()) == check

    def test_status_is_in_the_vocabulary(self):
        assert CheckResult("lint", "Passing").status in CHECK_STATUSES


class TestCorrectionAttempt:
    def test_roundtrip(self):
        attempt = CorrectionAttempt(step="Diagnosis", batch=1)
        assert CorrectionAttempt.from_dict(attempt.to_dict()) == attempt

    def test_step_is_in_the_vocabulary(self):
        assert CorrectionAttempt("Fix", 1).step in CORRECTION_ATTEMPT_STEPS


class TestPRMessage:
    def test_roundtrip(self):
        message = PRMessage(
            target="PRComment",
            what_happened="check failed",
            evidence="lint job",
            decision="correcting",
            completed="diagnosis",
            pending="fix",
            automation_state="attempt 1 of 5",
            user_next_step="none",
        )
        assert PRMessage.from_dict(message.to_dict()) == message

    def test_target_is_in_the_vocabulary(self):
        message = PRMessage(
            target="IssueComment",
            what_happened="",
            evidence="",
            decision="",
            completed="",
            pending="",
            automation_state="",
            user_next_step="",
        )
        assert message.target in MESSAGE_ROUTING_TARGETS

    def test_covers_every_required_field(self):
        fields = set(PRMessage.__dataclass_fields__)
        assert fields == {
            "target",
            "what_happened",
            "evidence",
            "decision",
            "completed",
            "pending",
            "automation_state",
            "user_next_step",
        }
