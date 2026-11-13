"""PR feedback evaluation logic (pure business logic, no I/O).

Mirrors docs/adr/0006-pr-process.md §1. Decides what a feedback event
means; performs no GitHub or model I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from qnagym.contracts.constants import CONFIDENCE_SHOW_BELOW
from qnagym.contracts.pr_process import EvaluationResult, FeedbackEvent

# Actions the evaluation can produce, in the order ADR 0006 §1 decides them.
ACTION_IGNORE = "Ignore"
ACTION_NO_ACTION = "NoAction"
ACTION_EXPLAIN_CONFLICT = "ExplainConflict"
ACTION_CLARIFY = "Clarify"
ACTION_SCOPE_CHANGE = "ScopeChange"
ACTION_INVOKE_SDD = "InvokeSDD"


@dataclass
class FeedbackDecision:
    """What the PR Process should do about one feedback event."""

    action: str
    reason: str
    scope_change: bool = False

    @property
    def invokes_sdd(self) -> bool:
        return self.action in {ACTION_SCOPE_CHANGE, ACTION_INVOKE_SDD}


def is_monitored(event: FeedbackEvent) -> bool:
    """Edits to existing comments are not monitored (ADR 0006 §1).

    A user corrects or supersedes earlier feedback by posting a new
    comment or review, so only new events enter evaluation.
    """
    return not event.event_type.endswith(":edited")


def evaluate_feedback(
    event: FeedbackEvent,
    evaluation: EvaluationResult,
) -> FeedbackDecision:
    """Decide the action for one evaluated feedback event.

    Args:
        event: The feedback event being evaluated.
        evaluation: The model's assessment: result, confidence, reason.

    Returns:
        The action the PR Process should take.
    """
    if not is_monitored(event):
        return FeedbackDecision(ACTION_IGNORE, "edit to an existing comment")

    if evaluation.result == "Conflict":
        return FeedbackDecision(
            ACTION_EXPLAIN_CONFLICT,
            f"conflicts with a non-negotiable rule: {evaluation.reason}",
        )

    if evaluation.result == "Ambiguous" or evaluation.confidence <= CONFIDENCE_SHOW_BELOW:
        return FeedbackDecision(
            ACTION_CLARIFY,
            f"unclear or below the decision gate (confidence {evaluation.confidence})",
        )

    if evaluation.result == "NoAction":
        return FeedbackDecision(ACTION_NO_ACTION, "no development change needed")

    if evaluation.result == "ScopeChange":
        return FeedbackDecision(
            ACTION_SCOPE_CHANGE,
            f"explicit scope change: {evaluation.reason}",
            scope_change=True,
        )

    return FeedbackDecision(
        ACTION_INVOKE_SDD,
        f"clear and actionable: {evaluation.reason}",
    )
