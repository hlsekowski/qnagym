"""Retry authorization domain logic (pure business logic, no I/O).

Mirrors docs/adr/0003 follow-up item 6. Implements retry request parsing,
authorization checks, feedback source eligibility, and workflow comment
marker detection; performs no GitHub I/O.
"""

from __future__ import annotations

from qnagym.contracts.constants import WORKFLOW_COMMENT_MARKER
from qnagym.contracts.retry_authorization import (
    RETRY_REQUEST_PREFIX,
    AuthorizationConfig,
    FeedbackSource,
    RetryRequest,
)


def parse_retry_request(comment_body: str) -> RetryRequest:
    """Parse a comment body to detect a retry request.

    Syntax: "/retry [optional reason]"

    Args:
        comment_body: The full comment body text.

    Returns:
        A RetryRequest with is_retry_request set and optional reason.
    """
    stripped = comment_body.strip()
    if not stripped.startswith(RETRY_REQUEST_PREFIX):
        return RetryRequest(
            is_retry_request=False,
            reason=None,
            raw_comment=comment_body,
        )

    # Extract the reason after the prefix
    rest = stripped[len(RETRY_REQUEST_PREFIX) :].strip()
    reason = rest if rest else None

    return RetryRequest(
        is_retry_request=True,
        reason=reason,
        raw_comment=comment_body,
    )


def is_workflow_comment(body: str) -> bool:
    """Check whether a comment body was authored by the workflow.

    Marker-prefixed comments are excluded from feedback and retry
    detection (ADR 0006 §5).
    """
    return body.startswith(WORKFLOW_COMMENT_MARKER)


def classify_feedback_source(
    source_type: str,
    account_id: str | None,
    account_login: str | None,
    comment_id: str,
    is_workflow_authored: bool,
) -> FeedbackSource:
    """Classify a feedback source with authorization info (ADR 0006 §5).

    Args:
        source_type: The type of feedback source.
        account_id: The account ID, if any.
        account_login: The account login, if any.
        comment_id: The comment ID.
        is_workflow_authored: Whether the comment was workflow-authored.

    Returns:
        A FeedbackSource with classification.
    """
    return FeedbackSource(
        source_type=source_type,
        account_id=account_id,
        account_login=account_login,
        comment_id=comment_id,
        is_workflow_authored=is_workflow_authored,
    )


def is_feedback_eligible(source: FeedbackSource, config: AuthorizationConfig) -> bool:
    """Check whether a feedback source is eligible for intake.

    Workflow-authored comments are never eligible (ADR 0006 §5).
    """
    return source.is_eligible(config)


def can_account_trigger_retry(config: AuthorizationConfig, account_id: str) -> bool:
    """Check whether an account can trigger a retry request.

    Args:
        config: The authorization configuration.
        account_id: The account ID to check.

    Returns:
        True if the account is authorized and can trigger a retry.
    """
    return config.can_trigger_retry(account_id)


def is_account_owner(config: AuthorizationConfig, account_id: str) -> bool:
    """Check whether an account is the owner."""
    return config.is_owner(account_id)


def is_account_authorized(config: AuthorizationConfig, account_id: str) -> bool:
    """Check whether an account is authorized."""
    return config.is_authorized(account_id)


__all__ = [
    "classify_feedback_source",
    "is_account_authorized",
    "is_account_owner",
    "can_account_trigger_retry",
    "is_feedback_eligible",
    "is_workflow_comment",
    "parse_retry_request",
]
