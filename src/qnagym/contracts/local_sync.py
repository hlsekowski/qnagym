"""Local synchronization contracts (pure data shapes, no logic).

Mirrors docs/adr/0003 follow-up item 7. Defines local repo
synchronization and resumable post-merge operations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# --- Local sync states ---

LOCAL_SYNC_STATE_PENDING = "Pending"
LOCAL_SYNC_STATE_IN_PROGRESS = "InProgress"
LOCAL_SYNC_STATE_COMPLETED = "Completed"
LOCAL_SYNC_STATE_FAILED = "Failed"
LOCAL_SYNC_STATE_BLOCKED = "Blocked"

LOCAL_SYNC_STATES = frozenset(
    {
        LOCAL_SYNC_STATE_PENDING,
        LOCAL_SYNC_STATE_IN_PROGRESS,
        LOCAL_SYNC_STATE_COMPLETED,
        LOCAL_SYNC_STATE_FAILED,
        LOCAL_SYNC_STATE_BLOCKED,
    }
)

# Terminal states
TERMINAL_LOCAL_SYNC_STATES = frozenset(
    {LOCAL_SYNC_STATE_COMPLETED, LOCAL_SYNC_STATE_FAILED, LOCAL_SYNC_STATE_BLOCKED}
)

# --- Post-merge steps ---

POST_MERGE_STEP_ISSUE_CLOSED = "issue_closed"
POST_MERGE_STEP_LOCAL_SYNCED = "local_synced"

POST_MERGE_STEPS = frozenset({POST_MERGE_STEP_ISSUE_CLOSED, POST_MERGE_STEP_LOCAL_SYNCED})


@dataclass(frozen=True)
class LocalSyncIdentity:
    """The immutable identity of a local sync operation."""

    pr_number: int
    target_branch: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocalSyncIdentity:
        return cls(
            pr_number=int(data["pr_number"]),
            target_branch=str(data["target_branch"]),
        )


@dataclass
class LocalSync:
    """Local repository synchronization state (ADR 0003 follow-up item 7).

    Tracks sync progress after PR merge, including which post-merge
    steps have completed and which remain for resumption on failure.
    """

    identity: LocalSyncIdentity
    state: str = LOCAL_SYNC_STATE_PENDING
    issue_closed: bool = False
    local_synced: bool = False
    last_error: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "state": self.state,
            "issue_closed": self.issue_closed,
            "local_synced": self.local_synced,
            "last_error": self.last_error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocalSync:
        return cls(
            identity=LocalSyncIdentity.from_dict(data["identity"]),
            state=str(data.get("state", LOCAL_SYNC_STATE_PENDING)),
            issue_closed=bool(data.get("issue_closed", False)),
            local_synced=bool(data.get("local_synced", False)),
            last_error=data.get("last_error"),
            retry_count=int(data.get("retry_count", 0)),
            max_retries=int(data.get("max_retries", 3)),
        )

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_LOCAL_SYNC_STATES

    @property
    def is_complete(self) -> bool:
        return self.state == LOCAL_SYNC_STATE_COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.state == LOCAL_SYNC_STATE_FAILED

    @property
    def is_blocked(self) -> bool:
        return self.state == LOCAL_SYNC_STATE_BLOCKED

    @property
    def outstanding_steps(self) -> tuple[str, ...]:
        """Post-merge steps that still need to complete."""
        return tuple(
            step
            for step, done in (
                (POST_MERGE_STEP_ISSUE_CLOSED, self.issue_closed),
                (POST_MERGE_STEP_LOCAL_SYNCED, self.local_synced),
            )
            if not done
        )

    @property
    def can_retry(self) -> bool:
        """Whether a retry is still allowed."""
        return self.retry_count < self.max_retries and self.is_failed


@dataclass
class SyncResult:
    """The result of a local sync operation."""

    success: bool
    pr_number: int
    target_branch: str
    issue_closed: bool = False
    local_synced: bool = False
    error: str | None = None
    steps_completed: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SyncResult:
        return cls(
            success=bool(data["success"]),
            pr_number=int(data["pr_number"]),
            target_branch=str(data["target_branch"]),
            issue_closed=bool(data.get("issue_closed", False)),
            local_synced=bool(data.get("local_synced", False)),
            error=data.get("error"),
            steps_completed=tuple(data.get("steps_completed", [])),
        )
