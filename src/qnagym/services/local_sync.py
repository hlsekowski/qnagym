"""Local synchronization service (orchestration).

Mirrors docs/adr/0003 follow-up item 7. Orchestrates local repo
synchronization and resumable post-merge operations; performs no I/O.
"""

from __future__ import annotations

from qnagym.contracts.local_sync import LocalSync, SyncResult
from qnagym.domain.local_sync import (
    build_sync_result,
    can_retry_sync,
    mark_issue_closed,
    mark_local_synced,
    mark_sync_blocked,
    mark_sync_completed,
    mark_sync_failed,
    mark_sync_in_progress,
    next_sync_step,
    retry_sync,
    start_local_sync,
)


def create_local_sync(
    pr_number: int,
    target_branch: str,
    max_retries: int = 3,
) -> LocalSync:
    """Create a new local sync operation.

    Args:
        pr_number: The PR number that was merged.
        target_branch: The target branch to sync with.
        max_retries: Maximum number of retry attempts.

    Returns:
        The new LocalSync in Pending state.
    """
    return start_local_sync(pr_number, target_branch, max_retries)


def get_next_step(sync: LocalSync) -> str:
    """Return the next post-merge step for a local sync."""
    return next_sync_step(sync)


def perform_issue_closure(sync: LocalSync) -> None:
    """Mark the issue closure step as complete."""
    mark_issue_closed(sync)


def perform_local_sync(sync: LocalSync) -> None:
    """Mark the local sync step as complete."""
    mark_local_synced(sync)


def start_sync(sync: LocalSync) -> None:
    """Mark the sync as in progress."""
    mark_sync_in_progress(sync)


def complete_sync(sync: LocalSync) -> None:
    """Mark the sync as completed."""
    mark_sync_completed(sync)


def fail_sync(sync: LocalSync, error: str) -> None:
    """Mark the sync as failed with an error message."""
    mark_sync_failed(sync, error)


def block_sync(sync: LocalSync, reason: str) -> None:
    """Mark the sync as blocked."""
    mark_sync_blocked(sync, reason)


def retry_local_sync(sync: LocalSync) -> None:
    """Reset the sync to pending for retry."""
    retry_sync(sync)


def build_result(sync: LocalSync) -> SyncResult:
    """Build a SyncResult from a LocalSync state."""
    return build_sync_result(sync)


def is_retryable(sync: LocalSync) -> bool:
    """Check whether a retry is still allowed."""
    return can_retry_sync(sync)


__all__ = [
    "block_sync",
    "build_result",
    "complete_sync",
    "create_local_sync",
    "fail_sync",
    "get_next_step",
    "is_retryable",
    "perform_issue_closure",
    "perform_local_sync",
    "retry_local_sync",
    "start_sync",
]
