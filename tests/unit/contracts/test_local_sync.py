"""Unit tests for local sync contracts."""

from qnagym.contracts.local_sync import (
    LOCAL_SYNC_STATE_BLOCKED,
    LOCAL_SYNC_STATE_COMPLETED,
    LOCAL_SYNC_STATE_FAILED,
    LOCAL_SYNC_STATE_IN_PROGRESS,
    LOCAL_SYNC_STATE_PENDING,
    LOCAL_SYNC_STATES,
    TERMINAL_LOCAL_SYNC_STATES,
    LocalSync,
    LocalSyncIdentity,
    SyncResult,
)


class TestLocalSyncIdentity:
    def test_identity_roundtrip(self):
        identity = LocalSyncIdentity(pr_number=42, target_branch="main")
        assert LocalSyncIdentity.from_dict(identity.to_dict()) == identity


class TestLocalSync:
    def test_sync_roundtrip(self):
        identity = LocalSyncIdentity(pr_number=42, target_branch="main")
        sync = LocalSync(
            identity=identity,
            state=LOCAL_SYNC_STATE_IN_PROGRESS,
            issue_closed=True,
            local_synced=False,
            last_error=None,
            retry_count=1,
            max_retries=3,
        )
        assert LocalSync.from_dict(sync.to_dict()) == sync

    def test_is_terminal(self):
        identity = LocalSyncIdentity(pr_number=1, target_branch="main")
        sync = LocalSync(identity=identity)
        assert not sync.is_terminal
        sync.state = LOCAL_SYNC_STATE_COMPLETED
        assert sync.is_terminal
        sync.state = LOCAL_SYNC_STATE_FAILED
        assert sync.is_terminal
        sync.state = LOCAL_SYNC_STATE_BLOCKED
        assert sync.is_terminal

    def test_is_complete(self):
        identity = LocalSyncIdentity(pr_number=1, target_branch="main")
        sync = LocalSync(identity=identity)
        assert not sync.is_complete
        sync.state = LOCAL_SYNC_STATE_COMPLETED
        assert sync.is_complete

    def test_is_failed(self):
        identity = LocalSyncIdentity(pr_number=1, target_branch="main")
        sync = LocalSync(identity=identity)
        assert not sync.is_failed
        sync.state = LOCAL_SYNC_STATE_FAILED
        assert sync.is_failed

    def test_is_blocked(self):
        identity = LocalSyncIdentity(pr_number=1, target_branch="main")
        sync = LocalSync(identity=identity)
        assert not sync.is_blocked
        sync.state = LOCAL_SYNC_STATE_BLOCKED
        assert sync.is_blocked

    def test_outstanding_steps(self):
        identity = LocalSyncIdentity(pr_number=1, target_branch="main")
        sync = LocalSync(identity=identity)
        assert sync.outstanding_steps == ("issue_closed", "local_synced")
        sync.issue_closed = True
        assert sync.outstanding_steps == ("local_synced",)
        sync.local_synced = True
        assert sync.outstanding_steps == ()

    def test_can_retry(self):
        identity = LocalSyncIdentity(pr_number=1, target_branch="main")
        sync = LocalSync(identity=identity, max_retries=3)
        assert not sync.can_retry
        sync.state = LOCAL_SYNC_STATE_FAILED
        sync.retry_count = 1
        assert sync.can_retry
        sync.retry_count = 3
        assert not sync.can_retry


class TestSyncResult:
    def test_result_roundtrip(self):
        result = SyncResult(
            success=True,
            pr_number=42,
            target_branch="main",
            issue_closed=True,
            local_synced=True,
            steps_completed=("issue_closed", "local_synced"),
        )
        assert SyncResult.from_dict(result.to_dict()) == result

    def test_success_and_failure(self):
        success = SyncResult(success=True, pr_number=1, target_branch="main")
        failure = SyncResult(success=False, pr_number=1, target_branch="main")
        assert success.success
        assert not failure.success


class TestConstants:
    def test_states(self):
        assert LOCAL_SYNC_STATE_PENDING in LOCAL_SYNC_STATES
        assert LOCAL_SYNC_STATE_COMPLETED in LOCAL_SYNC_STATES
        assert LOCAL_SYNC_STATE_FAILED in LOCAL_SYNC_STATES
        assert LOCAL_SYNC_STATE_BLOCKED in LOCAL_SYNC_STATES

    def test_terminal_states(self):
        assert LOCAL_SYNC_STATE_COMPLETED in TERMINAL_LOCAL_SYNC_STATES
        assert LOCAL_SYNC_STATE_FAILED in TERMINAL_LOCAL_SYNC_STATES
        assert LOCAL_SYNC_STATE_BLOCKED in TERMINAL_LOCAL_SYNC_STATES
        assert LOCAL_SYNC_STATE_PENDING not in TERMINAL_LOCAL_SYNC_STATES
