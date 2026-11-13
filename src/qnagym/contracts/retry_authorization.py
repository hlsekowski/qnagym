"""Retry authorization contracts (pure data shapes, no logic).

Mirrors docs/adr/0003 follow-up item 6. Defines retry request syntax,
eligible feedback sources, authorization configuration, and the
workflow comment marker format.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# --- Workflow comment marker (ADR 0006 §5, ADR 0003 follow-up item 6) ---

WORKFLOW_COMMENT_MARKER = "<!-- qnagym-workflow -->"

# --- Retry request syntax ---

# A retry request comment starts with this prefix, followed by a space
# and an optional reason.
RETRY_REQUEST_PREFIX = "/retry"

# --- Authorization ---

# Account types eligible to trigger retries.
ACCOUNT_TYPE_OWNER = "owner"
ACCOUNT_TYPE_COLLABORATOR = "collaborator"
ACCOUNT_TYPE_AUTOMATED_REVIEWER = "automated_revisor"

ACCOUNT_TYPES = frozenset(
    {ACCOUNT_TYPE_OWNER, ACCOUNT_TYPE_COLLABORATOR, ACCOUNT_TYPE_AUTOMATED_REVIEWER}
)

# Feedback sources eligible to trigger a retry (ADR 0006 §5).
FEEDBACK_SOURCE_OWNER_COMMENT = "owner_comment"
FEEDBACK_SOURCE_COLLABORATOR_COMMENT = "collaborator_comment"
FEEDBACK_SOURCE_AUTOMATED_REVIEWER = "automated_reviewer"
FEEDBACK_SOURCE_RETRY_COMMENT = "retry_comment"

FEEDBACK_SOURCES = frozenset(
    {
        FEEDBACK_SOURCE_OWNER_COMMENT,
        FEEDBACK_SOURCE_COLLABORATOR_COMMENT,
        FEEDBACK_SOURCE_AUTOMATED_REVIEWER,
        FEEDBACK_SOURCE_RETRY_COMMENT,
    }
)


@dataclass(frozen=True)
class AuthorizedAccount:
    """An account authorized to trigger retries and provide feedback."""

    account_id: str
    account_type: str  # one of ACCOUNT_TYPES
    login: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthorizedAccount:
        return cls(
            account_id=str(data["account_id"]),
            account_type=str(data["account_type"]),
            login=str(data["login"]),
        )

    @property
    def is_owner(self) -> bool:
        return self.account_type == ACCOUNT_TYPE_OWNER

    @property
    def is_collaborator(self) -> bool:
        return self.account_type == ACCOUNT_TYPE_COLLABORATOR

    @property
    def is_automated_reviewer(self) -> bool:
        return self.account_type == ACCOUNT_TYPE_AUTOMATED_REVIEWER


@dataclass
class AuthorizationConfig:
    """Authorization configuration for retry requests and feedback intake.

    Defines which accounts are authorized to trigger retries and which
    feedback sources are eligible (ADR 0006 §5).
    """

    authorized_accounts: list[AuthorizedAccount] = field(default_factory=list)
    eligible_feedback_sources: frozenset[str] = field(
        default_factory=lambda: FEEDBACK_SOURCES
    )
    require_owner_for_retry: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorized_accounts": [a.to_dict() for a in self.authorized_accounts],
            "eligible_feedback_sources": sorted(self.eligible_feedback_sources),
            "require_owner_for_retry": self.require_owner_for_retry,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthorizationConfig:
        return cls(
            authorized_accounts=[
                AuthorizedAccount.from_dict(a) for a in data.get("authorized_accounts", [])
            ],
            eligible_feedback_sources=frozenset(
                data.get("eligible_feedback_sources", list(FEEDBACK_SOURCES))
            ),
            require_owner_for_retry=bool(data.get("require_owner_for_retry", False)),
        )

    def is_authorized(self, account_id: str) -> bool:
        """Check whether an account is authorized."""
        return any(a.account_id == account_id for a in self.authorized_accounts)

    def is_owner(self, account_id: str) -> bool:
        """Check whether an account is the owner."""
        return any(
            a.account_id == account_id and a.is_owner for a in self.authorized_accounts
        )

    def can_trigger_retry(self, account_id: str) -> bool:
        """Check whether an account can trigger a retry.

        If require_owner_for_retry is True, only the owner can trigger.
        Otherwise, any authorized account can trigger.
        """
        if not self.is_authorized(account_id):
            return False
        if self.require_owner_for_retry:
            return self.is_owner(account_id)
        return True

    def is_feedback_source_eligible(self, source: str) -> bool:
        """Check whether a feedback source is eligible for intake."""
        return source in self.eligible_feedback_sources


@dataclass
class RetryRequest:
    """A parsed retry request from a comment (ADR 0003 follow-up item 6).

    Syntax: "/retry [optional reason]"
    """

    is_retry_request: bool
    reason: str | None = None
    raw_comment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetryRequest:
        return cls(
            is_retry_request=bool(data["is_retry_request"]),
            reason=data.get("reason"),
            raw_comment=data.get("raw_comment"),
        )


@dataclass
class FeedbackSource:
    """A feedback source with authorization info (ADR 0006 §5)."""

    source_type: str  # one of FEEDBACK_SOURCES
    account_id: str | None
    account_login: str | None
    comment_id: str
    is_workflow_authored: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeedbackSource:
        return cls(
            source_type=str(data["source_type"]),
            account_id=data.get("account_id"),
            account_login=data.get("account_login"),
            comment_id=str(data["comment_id"]),
            is_workflow_authored=bool(data["is_workflow_authored"]),
        )

    def is_eligible(self, config: AuthorizationConfig) -> bool:
        """Check whether this feedback source is eligible for intake."""
        if self.is_workflow_authored:
            return False
        return config.is_feedback_source_eligible(self.source_type)
