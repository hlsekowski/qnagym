"""PR trust boundary service (orchestration).

Mirrors docs/adr/0006-pr-process.md §5. Gates PR Process input by
author and surface; performs no I/O.
"""

from __future__ import annotations

from qnagym.contracts.pr_process import FeedbackEvent
from qnagym.domain.pr_trust import (
    FEEDBACK,
    INTAKE,
    RETRY,
    TrustPolicy,
    is_processable,
    is_workflow_authored,
)


class PRTrustError(Exception):
    """Input from an unauthorized source."""

    def __init__(self, message: str, exit_code: int = 4):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def authorize(policy: TrustPolicy, author: str, surface: str) -> None:
    """Raise if the author may not supply input on the surface.

    Raises:
        PRTrustError: If the author is not authorized.
    """
    if not policy.is_authorized(author, surface):
        raise PRTrustError(f"unauthorized author {author!r} for {surface}")


def accept_feedback(policy: TrustPolicy, event: FeedbackEvent) -> FeedbackEvent:
    """Return the event if it may be processed, else raise.

    Two gates: the author must be authorized for feedback, and the
    body must not be the workflow's own output.

    Raises:
        PRTrustError: If the author is unauthorized or the body is
            workflow-authored.
    """
    authorize(policy, event.author, FEEDBACK)
    if not is_processable(event.body):
        raise PRTrustError("workflow-authored comment is not input")
    return event


def accept_retry(policy: TrustPolicy, author: str, body: str) -> None:
    """Raise unless the author may request a retry with this body.

    Raises:
        PRTrustError: If the author is unauthorized or the body is
            workflow-authored.
    """
    authorize(policy, author, RETRY)
    if not is_processable(body):
        raise PRTrustError("workflow-authored comment is not input")


def accept_intake(policy: TrustPolicy, author: str) -> None:
    """Raise unless the author may supply intake input.

    Raises:
        PRTrustError: If the author is not authorized.
    """
    authorize(policy, author, INTAKE)


__all__ = [
    "FEEDBACK",
    "INTAKE",
    "RETRY",
    "PRTrustError",
    "TrustPolicy",
    "accept_feedback",
    "accept_intake",
    "accept_retry",
    "authorize",
    "is_workflow_authored",
]
