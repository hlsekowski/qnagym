"""PR notification service (orchestration).

Mirrors docs/adr/0006-pr-process.md §4. Routes and renders messages;
performs no I/O.
"""

from __future__ import annotations

from qnagym.contracts.pr_process import PRMessage
from qnagym.domain.pr_notifications import (
    RoutedMessage,
    build_notification,
    is_workflow_comment,
    route_message,
    validate_kind,
)


class PRNotificationError(Exception):
    """Error building or routing a notification."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def notify(message: PRMessage) -> RoutedMessage:
    """Route and render one message.

    Raises:
        PRNotificationError: If the message kind or target is unknown.
    """
    try:
        validate_kind(message.target)
        return build_notification(message)
    except ValueError as exc:
        raise PRNotificationError(str(exc)) from exc


def surface_for(kind: str) -> str:
    """The surface a message kind routes to.

    Raises:
        PRNotificationError: If the kind is unknown.
    """
    try:
        return route_message(kind)
    except ValueError as exc:
        raise PRNotificationError(str(exc)) from exc


def is_own_comment(body: str) -> bool:
    """True when a comment was authored by this workflow."""
    return is_workflow_comment(body)
