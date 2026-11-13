"""Unit tests for the PR feedback evaluation service."""

import pytest

from qnagym.contracts.pr_process import EvaluationResult, FeedbackEvent
from qnagym.domain.pr_feedback import (
    ACTION_CLARIFY,
    ACTION_EXPLAIN_CONFLICT,
    ACTION_IGNORE,
    ACTION_INVOKE_SDD,
    ACTION_NO_ACTION,
    ACTION_SCOPE_CHANGE,
    evaluate_feedback,
    is_monitored,
)
from qnagym.services.pr_feedback import PRFeedbackError, evaluate_pr_feedback
from tests.http import model_client

EVENT = FeedbackEvent(event_type="Review", author="owner", body="fix the typo", comment_id="c1")


class TestIsMonitored:
    def test_new_event_is_monitored(self):
        assert is_monitored(EVENT)

    def test_edit_is_not_monitored(self):
        edited = FeedbackEvent("Review:edited", "owner", "changed", "c1")
        assert not is_monitored(edited)


class TestEvaluateFeedback:
    def test_clear_and_actionable_invokes_sdd(self):
        decision = evaluate_feedback(EVENT, EvaluationResult("ClearActionable", 0.98, "clear"))
        assert decision.action == ACTION_INVOKE_SDD
        assert decision.invokes_sdd
        assert not decision.scope_change

    def test_conflict_explains_without_implementing(self):
        decision = evaluate_feedback(EVENT, EvaluationResult("Conflict", 0.99, "breaks C3"))
        assert decision.action == ACTION_EXPLAIN_CONFLICT
        assert not decision.invokes_sdd

    def test_ambiguous_requests_clarification(self):
        decision = evaluate_feedback(EVENT, EvaluationResult("Ambiguous", 0.99, "unclear"))
        assert decision.action == ACTION_CLARIFY
        assert not decision.invokes_sdd

    def test_low_confidence_requests_clarification(self):
        decision = evaluate_feedback(EVENT, EvaluationResult("ClearActionable", 0.5, "unsure"))
        assert decision.action == ACTION_CLARIFY

    def test_confidence_at_threshold_does_not_pass(self):
        decision = evaluate_feedback(EVENT, EvaluationResult("ClearActionable", 0.95, "borderline"))
        assert decision.action == ACTION_CLARIFY

    def test_no_action_means_no_sdd(self):
        decision = evaluate_feedback(EVENT, EvaluationResult("NoAction", 0.99, "nothing to do"))
        assert decision.action == ACTION_NO_ACTION
        assert not decision.invokes_sdd

    def test_scope_change_invokes_sdd_and_flags_scope(self):
        decision = evaluate_feedback(
            EVENT, EvaluationResult("ScopeChange", 0.99, "new requirement")
        )
        assert decision.action == ACTION_SCOPE_CHANGE
        assert decision.invokes_sdd
        assert decision.scope_change

    def test_edit_is_ignored_regardless_of_evaluation(self):
        edited = FeedbackEvent("Review:edited", "owner", "changed", "c1")
        decision = evaluate_feedback(edited, EvaluationResult("ClearActionable", 0.99, "clear"))
        assert decision.action == ACTION_IGNORE
        assert not decision.invokes_sdd


class TestEvaluatePRFeedbackService:
    def test_success(self):
        client = model_client({"result": "ClearActionable", "confidence": 0.98, "reason": "clear"})
        decision = evaluate_pr_feedback(client, EVENT, "spec v1")
        assert decision.action == ACTION_INVOKE_SDD
        client.chat_json.assert_called_once()

    def test_model_error_raises(self):
        client = model_client({})
        client.chat_json.side_effect = RuntimeError("connection refused")
        with pytest.raises(PRFeedbackError, match="Model error"):
            evaluate_pr_feedback(client, EVENT, "spec v1")

    def test_invalid_result_raises(self):
        client = model_client({"result": "Bogus", "confidence": 0.5, "reason": "x"})
        with pytest.raises(PRFeedbackError, match="Invalid model response"):
            evaluate_pr_feedback(client, EVENT, "spec v1")

    def test_messages_include_requirements(self):
        client = model_client({"result": "NoAction", "confidence": 0.99, "reason": "none"})
        evaluate_pr_feedback(client, EVENT, "the sealed baseline")
        messages = client.chat_json.call_args[0][0]
        assert "the sealed baseline" in messages[1]["content"]
        assert "fix the typo" in messages[1]["content"]
