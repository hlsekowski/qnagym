"""Retry authorization service (orchestration).

Mirrors docs/adr/0003 follow-up item 6. Orchestrates retry request
parsing, authorization checks, and feedback source eligibility;
performs no GitHub I/O.
"""

from __future__ import annotations

from qnagym.contracts.retry_authorization import (
    AuthorizationConfig,
    AuthorizedAccount,
    FeedbackSource,
    RetryRequest,
)
from qnagym.domain.retry_authorization import (
    can_account_trigger_retry,
    classify_feedback_source,
    is_account_authorized,
    is_account_owner,
    is_feedback_eligible,
    is_workflow_comment,
    parse_retry_request,
)


class RetryAuthorizationError(Exception):
    """Error during retry authorization."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


def create_authorization_config(
    authorized_accounts: list[dict[str, str]] | None = None,
    eligible_feedback_sources: list[str] | None = None,
    require_owner_for_retry: bool = False,
) -> AuthorizationConfig:
    """Create an authorization configuration.

    Args:
        authorized_accounts: List of account dicts with account_id,
            account_type, and login.
        eligible_feedback_sources: List of eligible feedback source types.
        require_owner_for_retry: Whether only the owner can trigger retries.

    Returns:
        The AuthorizationConfig.
    """
    accounts = []
    if authorized_accounts:
        for a in authorized_accounts:
            accounts.append(
                AuthorizedAccount(
                    account_id=str(a["account_id"]),
                    account_type=str(a["account_type"]),
                    login=str(a["login"]),
                )
            )

    return AuthorizationConfig(
        authorized_accounts=accounts,
        eligible_feedback_sources=(
            frozenset(eligible_feedback_sources)
            if eligible_feedback_sources is not None
            else frozenset()
        ),
        require_owner_for_retry=require_owner_for_retry,
    )


def parse_comment_for_retry(comment_body: str) -> RetryRequest:
    """Parse a comment body to detect a retry request.

    Args:
        comment_body: The full comment body text.

    Returns:
        A RetryRequest.
    """
    return parse_retry_request(comment_body)


def check_comment_is_workflow_authored(body: str) -> bool:
    """Check whether a comment was authored by the workflow.

    Args:
        body: The comment body text.

    Returns:
        True if the comment carries the workflow marker.
    """
    return is_workflow_comment(body)


def classify_feedback(
    source_type: str,
    account_id: str | None,
    account_login: str | None,
    comment_id: str,
    is_workflow_authored: bool,
) -> FeedbackSource:
    """Classify a feedback source.

    Args:
        source_type: The type of feedback source.
        account_id: The account ID, if any.
        account_login: The account login, if any.
        comment_id: The comment ID.
        is_workflow_authored: Whether the comment was workflow-authored.

    Returns:
        A FeedbackSource.
    """
    return classify_feedback_source(
        source_type, account_id, account_login, comment_id, is_workflow_authored
    )


def check_feedback_eligible(
    source: FeedbackSource, config: AuthorizationConfig
) -> bool:
    """Check whether a feedback source is eligible for intake.

    Args:
        source: The feedback source to check.
        config: The authorization configuration.

    Returns:
        True if the source is eligible.
    """
    return is_feedback_eligible(source, config)


def check_account_can_trigger_retry(
    config: AuthorizationConfig, account_id: str
) -> bool:
    """Check whether an account can trigger a retry request.

    Args:
        config: The authorization configuration.
        account_id: The account ID to check.

    Returns:
        True if the account can trigger a retry.
    """
    return can_account_trigger_retry(config, account_id)


def check_account_is_authorized(
    config: AuthorizationConfig, account_id: str
) -> bool:
    """Check whether an account is authorized."""
    return is_account_authorized(config, account_id)


def check_account_is_owner(
    config: AuthorizationConfig, account_id: str
) -> bool:
    """Check whether an account is the owner."""
    return is_account_owner(config, account_id)


__all__ = [
    "RetryAuthorizationError",
    "check_account_can_trigger_retry",
    "check_account_is_authorized",
    "check_account_is_owner",
    "check_comment_is_workflow_authored",
    "check_feedback_eligible",
    "classify_feedback",
    "create_authorization_config",
    "parse_comment_for_retry",
]
