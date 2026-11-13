"""Unit tests for the local sync domain logic."""

from qnagym.contracts.local_sync import (
    LOCAL_SYNC_STATE_BLOCKED,
    LOCAL_SYNC_STATE_COMPLETED,
    LOCAL_SYNC_STATE_FAILED,
    LOCAL_SYNC_STATE_IN_PROGRESS,
    LOCAL_SYNC_STATE_PENDING,
    LocalSync,
    LocalSyncIdentity,
)
from qnagym.domain.local_sync import (
    ACTION_CLOSE_ISSUE,
    ACTION_NONE,
    ACTION_SYNC_LOCAL,
    LocalSyncError,
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


def _identity(pr_number=42, target_branch="main"):
    return LocalSyncIdentity(pr_number=pr_number, target_branch=target_branch)


def _sync(
    identity=None,
    state=LOCAL_SYNC_STATE_PENDING,
    issue_closed=False,
    local_synced=False,
    last_error=None,
    retry_count=0,
    max_retries=3,
):
    if identity is None:
        identity = _identity()
    return LocalSync(
        identity=identity,
        state=state,
        issue_closed=issue_closed,
        local_synced=local_synced,
        last_error=last_error,
        retry_count=retry_count,
        max_retries=max_retries,
    )


class TestStartLocalSync:
    def test_create_pending_sync(self):
        sync = start_local_sync(42, "main")
        assert sync.state == LOCAL_SYNC_STATE_PENDING
        assert sync.identity.pr_number == 42
        assert sync.identity.target_branch == "main"
        assert not sync.issue_closed
        assert not sync.local_synced
        assert sync.retry_count == 0
        assert sync.max_retries == 3

    def test_custom_max_retries(self):
        sync = start_local_sync(42, "main", max_retries=5)
        assert sync.max_retries == 5


class TestNextSyncStep:
    def test_issue_closed_first(self):
        sync = _sync()
        assert next_sync_step(sync) == ACTION_CLOSE_ISSUE

    def test_local_synced_after_issue_closed(self):
        sync = _sync(issue_closed=True)
        assert next_sync_step(sync) == ACTION_SYNC_LOCAL

    def test_none_when_complete(self):
        sync = _sync(issue_closed=True, local_synced=True)
        assert next_sync_step(sync) == ACTION_NONE


class TestMarkIssueClosed:
    def test_mark_issue_closed(self):
        sync = _sync()
        mark_issue_closed(sync)
        assert sync.issue_closed


class TestMarkLocalSynced:
    def test_mark_local_synced(self):
        sync = _sync()
        mark_local_synced(sync)
        assert sync.local_synced


class TestMarkSyncStates:
    def test_mark_in_progress(self):
        sync = _sync()
        mark_sync_in_progress(sync)
        assert sync.state == LOCAL_SYNC_STATE_IN_PROGRESS
        assert sync.last_error is None

    def test_mark_completed(self):
        sync = _sync()
        mark_sync_completed(sync)
        assert sync.state == LOCAL_SYNC_STATE_COMPLETED

    def test_mark_failed(self):
        sync = _sync()
        mark_sync_failed(sync, "network error")
        assert sync.state == LOCAL_SYNC_STATE_FAILED
        assert sync.last_error == "network error"
        assert sync.retry_count == 1

    def test_mark_blocked(self):
        sync = _sync()
        mark_sync_blocked(sync, "permanent failure")
        assert sync.state == LOCAL_SYNC_STATE_BLOCKED
        assert sync.last_error == "permanent failure"


class TestCanRetrySync:
    def test_cannot_retry_pending(self):
        sync = _sync()
        assert not can_retry_sync(sync)

    def test_can_retry_failed_with_retries_left(self):
        sync = _sync(state=LOCAL_SYNC_STATE_FAILED, retry_count=1, max_retries=3)
        assert can_retry_sync(sync)

    def test_cannot_retry_exhausted(self):
        sync = _sync(state=LOCAL_SYNC_STATE_FAILED, retry_count=3, max_retries=3)
        assert not can_retry_sync(sync)

    def test_cannot_retry_completed(self):
        sync = _sync(state=LOCAL_SYNC_STATE_COMPLETED)
        assert not can_retry_sync(sync)


class TestRetrySync:
    def test_retry_resets_to_pending(self):
        sync = _sync(state=LOCAL_SYNC_STATE_FAILED, retry_count=1, last_error="error")
        retry_sync(sync)
        assert sync.state == LOCAL_SYNC_STATE_PENDING
        assert sync.last_error is None

    def test_retry_when_not_retryable_raises(self):
        sync = _sync(state=LOCAL_SYNC_STATE_COMPLETED)
        try:
            retry_sync(sync)
        except LocalSyncError:
            pass
        else:
            raise AssertionError("expected LocalSyncError")


class TestBuildSyncResult:
    def test_build_result_from_pending(self):
        sync = _sync()
        result = build_sync_result(sync)
        assert not result.success
        assert result.pr_number == 42
        assert result.target_branch == "main"
        assert not result.issue_closed
        assert not result.local_synced
        assert result.steps_completed == ()

    def test_build_result_from_completed(self):
        sync = _sync(
            state=LOCAL_SYNC_STATE_COMPLETED,
            issue_closed=True,
            local_synced=True,
        )
        result = build_sync_result(sync)
        assert result.success
        assert result.issue_closed
        assert result.local_synced
        assert result.steps_completed == ("issue_closed", "local_synced")

    def test_build_result_from_failed(self):
        sync = _sync(
            state=LOCAL_SYNC_STATE_FAILED,
            last_error="network error",
            issue_closed=True,
        )
        result = build_sync_result(sync)
        assert not result.success
        assert result.error == "network error"
        assert result.steps_completed == ("issue_closed",)
