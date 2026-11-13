"""PR notification routing (pure business logic, no I/O).

Mirrors docs/adr/0006-pr-process.md §4. Decides where a message goes
and renders it; performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from qnagym.contracts.constants import WORKFLOW_COMMENT_MARKER
from qnagym.contracts.pr_process import PRMessage

# Message kinds and the surface each routes to (ADR 0006 §4).
ROUTING: dict[str, str] = {
    "IssueClarification": "IssueComment",
    "FeedbackClarification": "PRComment",
    "CheckResults": "PRComment",
    "LifecycleFailure": "PRComment",
    "ScopeChange": "ScopeChangeNotice",
}


@dataclass
class RoutedMessage:
    """A rendered message and the surface it belongs on."""

    target: str
    body: str

    @property
    def is_workflow_authored(self) -> bool:
        """True when the body carries the workflow marker."""
        return self.body.startswith(WORKFLOW_COMMENT_MARKER)


def route_message(kind: str) -> str:
    """The surface a message kind routes to.

    Raises:
        ValueError: If the kind is unknown.
    """
    if kind not in ROUTING:
        raise ValueError(f"unknown message kind: {kind!r}")
    return ROUTING[kind]


def render_message(message: PRMessage) -> str:
    """Render a message with the workflow marker and all required sections.

    Every message covers what happened and its evidence, the decision and
    why, what is complete versus pending, the automation state, and the
    user's next step (ADR 0006 §4).
    """
    sections = [
        f"**What happened:** {message.what_happened}",
        f"**Evidence:** {message.evidence}",
        f"**Decision:** {message.decision}",
        f"**Completed:** {message.completed}",
        f"**Pending:** {message.pending}",
        f"**Automation state:** {message.automation_state}",
        f"**Next step for you:** {message.user_next_step}",
    ]
    return "\n".join([WORKFLOW_COMMENT_MARKER, *sections])


def build_notification(message: PRMessage) -> RoutedMessage:
    """Route and render a message in one step.

    ``PRMessage.target`` names the message *kind*; the surface it routes
    to is derived from ``ROUTING``.
    """
    return RoutedMessage(target=route_message(message.target), body=render_message(message))


def is_workflow_comment(body: str) -> bool:
    """True when a comment body was authored by the workflow.

    Marker-prefixed comments are excluded from feedback and retry
    detection (ADR 0006 §5), so the workflow never reacts to itself.
    """
    return body.startswith(WORKFLOW_COMMENT_MARKER)


def validate_kind(kind: str) -> None:
    """Raise ValueError if the kind is not a known message kind.

    A message *kind* (what the message is about) is distinct from the
    *surface* it routes to; ``route_message`` maps one to the other.
    """
    if kind not in ROUTING:
        raise ValueError(f"unknown message kind: {kind!r}")
