"""Local synchronization domain logic (pure business logic, no I/O).

Mirrors docs/adr/0003 follow-up item 7. Implements local repo
synchronization and resumable post-merge operations; performs no I/O.
"""

from __future__ import annotations

from qnagym.contracts.local_sync import (
    LOCAL_SYNC_STATE_BLOCKED,
    LOCAL_SYNC_STATE_COMPLETED,
    LOCAL_SYNC_STATE_FAILED,
    LOCAL_SYNC_STATE_IN_PROGRESS,
    LOCAL_SYNC_STATE_PENDING,
    POST_MERGE_STEP_ISSUE_CLOSED,
    POST_MERGE_STEP_LOCAL_SYNCED,
    LocalSync,
    SyncResult,
)

# Actions the local sync can produce.
ACTION_START_SYNC = "StartSync"
ACTION_CLOSE_ISSUE = "CloseIssue"
ACTION_SYNC_LOCAL = "SyncLocal"
ACTION_RETRY_SYNC = "RetrySync"
ACTION_REPORT_FAILURE = "ReportFailure"
ACTION_NONE = "None"


class LocalSyncError(Exception):
    """Error during local sync domain operations."""

    pass


def start_local_sync(
    pr_number: int,
    target_branch: str,
    max_retries: int = 3,
) -> LocalSync:
    """Create a new local sync operation in Pending state.

    Args:
        pr_number: The PR number that was merged.
        target_branch: The target branch to sync with.
        max_retries: Maximum number of retry attempts.

    Returns:
        The new LocalSync in Pending state.
    """
    from qnagym.contracts.local_sync import LocalSyncIdentity

    return LocalSync(
        identity=LocalSyncIdentity(
            pr_number=pr_number,
            target_branch=target_branch,
        ),
        state=LOCAL_SYNC_STATE_PENDING,
        max_retries=max_retries,
    )


def next_sync_step(sync: LocalSync) -> str:
    """Return the next post-merge step for a local sync.

    Order: issue_closed first, then local_synced.
    """
    if not sync.issue_closed:
        return ACTION_CLOSE_ISSUE
    if not sync.local_synced:
        return ACTION_SYNC_LOCAL
    return ACTION_NONE


def mark_issue_closed(sync: LocalSync) -> None:
    """Mark the issue closure step as complete."""
    sync.issue_closed = True


def mark_local_synced(sync: LocalSync) -> None:
    """Mark the local sync step as complete."""
    sync.local_synced = True


def mark_sync_in_progress(sync: LocalSync) -> None:
    """Mark the sync as in progress."""
    sync.state = LOCAL_SYNC_STATE_IN_PROGRESS
    sync.last_error = None


def mark_sync_completed(sync: LocalSync) -> None:
    """Mark the sync as completed."""
    sync.state = LOCAL_SYNC_STATE_COMPLETED


def mark_sync_failed(sync: LocalSync, error: str) -> None:
    """Mark the sync as failed with an error message.

    Increments the retry count. If retries are exhausted, the sync
    becomes blocked.
    """
    sync.state = LOCAL_SYNC_STATE_FAILED
    sync.last_error = error
    sync.retry_count += 1
    if sync.retry_count >= sync.max_retries:
        sync.state = LOCAL_SYNC_STATE_BLOCKED


def mark_sync_blocked(sync: LocalSync, reason: str) -> None:
    """Mark the sync as blocked."""
    sync.state = LOCAL_SYNC_STATE_BLOCKED
    sync.last_error = reason


def can_retry_sync(sync: LocalSync) -> bool:
    """Check whether a retry is still allowed."""
    return sync.is_failed and sync.retry_count < sync.max_retries


def retry_sync(sync: LocalSync) -> None:
    """Reset the sync to pending for retry."""
    if not can_retry_sync(sync):
        raise LocalSyncError(
            f"cannot retry sync: state={sync.state}, retries={sync.retry_count}/{sync.max_retries}"
        )
    sync.state = LOCAL_SYNC_STATE_PENDING
    sync.last_error = None


def build_sync_result(sync: LocalSync) -> SyncResult:
    """Build a SyncResult from a LocalSync state."""
    return SyncResult(
        success=sync.is_complete,
        pr_number=sync.identity.pr_number,
        target_branch=sync.identity.target_branch,
        issue_closed=sync.issue_closed,
        local_synced=sync.local_synced,
        error=sync.last_error,
        steps_completed=tuple(
            step
            for step, done in (
                (POST_MERGE_STEP_ISSUE_CLOSED, sync.issue_closed),
                (POST_MERGE_STEP_LOCAL_SYNCED, sync.local_synced),
            )
            if done
        ),
    )


__all__ = [
    "ACTION_CLOSE_ISSUE",
    "ACTION_NONE",
    "ACTION_RETRY_SYNC",
    "ACTION_REPORT_FAILURE",
    "ACTION_START_SYNC",
    "ACTION_SYNC_LOCAL",
    "build_sync_result",
    "can_retry_sync",
    "mark_issue_closed",
    "mark_sync_blocked",
    "mark_sync_completed",
    "mark_sync_failed",
    "mark_sync_in_progress",
    "next_sync_step",
    "retry_sync",
    "start_local_sync",
]
