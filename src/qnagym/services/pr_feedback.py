"""PR feedback evaluation service (orchestration).

Mirrors docs/adr/0006-pr-process.md §1. Evaluates one feedback event and
returns the action the PR Process should take.
"""

from __future__ import annotations

from qnagym.contracts.pr_process import FeedbackEvent
from qnagym.contracts.types import ModelClientProtocol
from qnagym.contracts.validation import (
    build_pr_feedback_messages,
    parse_pr_feedback_response,
)
from qnagym.domain.pr_feedback import FeedbackDecision, evaluate_feedback


class PRFeedbackError(Exception):
    """Error during PR feedback evaluation."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def evaluate_pr_feedback(
    client: ModelClientProtocol,
    event: FeedbackEvent,
    accepted_requirements: str,
) -> FeedbackDecision:
    """Evaluate one PR feedback event against the accepted requirements.

    Args:
        client: Model client for evaluation
        event: The feedback event to evaluate
        accepted_requirements: The sealed requirements baseline

    Returns:
        The action the PR Process should take.

    Raises:
        PRFeedbackError: On model error or invalid model response.
    """
    messages = build_pr_feedback_messages(event, accepted_requirements)

    try:
        response = client.chat_json(messages)
    except Exception as exc:
        raise PRFeedbackError(f"Model error: {exc}", exit_code=1) from exc

    try:
        evaluation = parse_pr_feedback_response(response)
    except Exception as exc:
        raise PRFeedbackError(f"Invalid model response: {exc}", exit_code=1) from exc

    return evaluate_feedback(event, evaluation)
