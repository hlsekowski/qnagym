"""Unit tests for event processing contracts."""

from qnagym.contracts.event_process import (
    EVENT_STATE_DEDUPLICATED,
    EVENT_STATE_INTERRUPTED,
    EVENT_STATE_PENDING,
    EVENT_STATE_PROCESSED,
    EVENT_STATE_RECOVERED,
    EVENT_TYPE_BRANCH_DELETED,
    EVENT_TYPE_CHECK_RESULT,
    EVENT_TYPE_DESCRIPTION_EDIT,
    EVENT_TYPE_FEEDBACK,
    EVENT_TYPE_PR_CLOSED,
    EVENT_TYPE_STOP_SIGNAL,
    EVENT_TYPES,
    INTERRUPTION_BRANCH_DELETED,
    INTERRUPTION_ISSUE_CLOSED,
    INTERRUPTION_PR_CLOSED,
    INTERRUPTION_STOP_SIGNAL,
    EventIdentity,
    EventProcessingState,
    InterruptionRecord,
    NotificationConfig,
    ProcessedEvent,
)


class TestEventIdentity:
    def test_identity_roundtrip(self):
        identity = EventIdentity(
            event_type="description_edit",
            source_id="evt-123",
            source="github",
        )
        assert EventIdentity.from_dict(identity.to_dict()) == identity


class TestProcessedEvent:
    def test_event_roundtrip(self):
        identity = EventIdentity(
            event_type="feedback",
            source_id="c1",
            source="github",
        )
        event = ProcessedEvent(
            identity=identity,
            event_type="feedback",
            payload={"body": "fix this"},
            created_at=100.0,
            processed_at=101.0,
            state=EVENT_STATE_PROCESSED,
        )
        assert ProcessedEvent.from_dict(event.to_dict()) == event

    def test_event_properties(self):
        identity = EventIdentity(
            event_type="check_result",
            source_id="cr-1",
            source="github",
        )
        event = ProcessedEvent(
            identity=identity,
            event_type="check_result",
            payload={},
            created_at=100.0,
        )
        assert not event.is_processed
        assert not event.is_duplicate
        assert not event.is_interrupted
        assert not event.is_recovered

        event.state = EVENT_STATE_PROCESSED
        assert event.is_processed

        event.state = EVENT_STATE_DEDUPLICATED
        assert event.is_duplicate

        event.state = EVENT_STATE_INTERRUPTED
        assert event.is_interrupted

        event.state = EVENT_STATE_RECOVERED
        assert event.is_recovered


class TestNotificationConfig:
    def test_should_notify_first_time(self):
        config = NotificationConfig()
        assert config.should_notify(None, 100.0)

    def test_should_notify_after_interval(self):
        config = NotificationConfig(min_interval_seconds=60.0)
        assert config.should_notify(100.0, 200.0)

    def test_should_not_notify_before_interval(self):
        config = NotificationConfig(min_interval_seconds=60.0)
        assert not config.should_notify(100.0, 130.0)

    def test_disabled(self):
        config = NotificationConfig(enabled=False)
        assert not config.should_notify(None, 100.0)


class TestInterruptionRecord:
    def test_interruption_roundtrip(self):
        record = InterruptionRecord(
            reason="stop_signal",
            affected_entity="issue-42",
            occurred_at=100.0,
            recovered_at=200.0,
            recovery_action="restarted",
        )
        assert InterruptionRecord.from_dict(record.to_dict()) == record

    def test_is_recovered(self):
        record = InterruptionRecord(
            reason="branch_deleted",
            affected_entity="feat/test",
            occurred_at=100.0,
        )
        assert not record.is_recovered
        record.recovered_at = 200.0
        assert record.is_recovered


class TestEventProcessingState:
    def test_state_roundtrip(self):
        state = EventProcessingState()
        identity = EventIdentity(
            event_type="description_edit",
            source_id="evt-1",
            source="github",
        )
        event = ProcessedEvent(
            identity=identity,
            event_type="description_edit",
            payload={},
            created_at=100.0,
        )
        state.record_event(event)
        assert state.get_event(identity) is event
        # A pending event is not yet a duplicate
        assert not state.is_duplicate(identity)
        # After processing, it becomes a duplicate
        event.state = EVENT_STATE_PROCESSED
        state.record_event(event)
        assert state.is_duplicate(identity)

    def test_event_key(self):
        state = EventProcessingState()
        identity = EventIdentity(
            event_type="feedback",
            source_id="c1",
            source="github",
        )
        key = state.event_key(identity)
        assert key == "feedback|github|c1"

    def test_increment_event_counter(self):
        state = EventProcessingState()
        assert state.increment_event_counter() == 1
        assert state.increment_event_counter() == 2

    def test_state_roundtrip_full(self):
        state = EventProcessingState()
        identity = EventIdentity(
            event_type="check_result",
            source_id="cr-1",
            source="github",
        )
        event = ProcessedEvent(
            identity=identity,
            event_type="check_result",
            payload={},
            created_at=100.0,
        )
        state.record_event(event)
        state.increment_event_counter()
        restored = EventProcessingState.from_dict(state.to_dict())
        assert restored.get_event(identity) is not None
        assert restored.event_counter == 1

    def test_interruption_record_and_get(self):
        state = EventProcessingState()
        record = InterruptionRecord(
            reason="stop_signal",
            affected_entity="issue-42",
            occurred_at=100.0,
        )
        state.record_interruption(record)
        retrieved = state.get_interruption("stop_signal", "issue-42")
        assert retrieved is record

    def test_notification_config_defaults(self):
        config = NotificationConfig()
        assert config.min_interval_seconds == 300.0
        assert config.max_notifications_per_hour == 12
        assert config.enabled


class TestConstants:
    def test_event_types(self):
        assert EVENT_TYPE_DESCRIPTION_EDIT in EVENT_TYPES
        assert EVENT_TYPE_FEEDBACK in EVENT_TYPES
        assert EVENT_TYPE_CHECK_RESULT in EVENT_TYPES
        assert EVENT_TYPE_PR_CLOSED in EVENT_TYPES
        assert EVENT_TYPE_BRANCH_DELETED in EVENT_TYPES
        assert EVENT_TYPE_STOP_SIGNAL in EVENT_TYPES

    def test_event_states(self):
        all_states = {
            EVENT_STATE_PENDING,
            EVENT_STATE_PROCESSED,
            EVENT_STATE_DEDUPLICATED,
            EVENT_STATE_INTERRUPTED,
            EVENT_STATE_RECOVERED,
        }
        assert EVENT_STATE_PENDING in all_states
        assert EVENT_STATE_PROCESSED in all_states

    def test_interruption_reasons(self):
        assert INTERRUPTION_STOP_SIGNAL == "stop_signal"
        assert INTERRUPTION_BRANCH_DELETED == "branch_deleted"
        assert INTERRUPTION_ISSUE_CLOSED == "issue_closed"
        assert INTERRUPTION_PR_CLOSED == "pr_closed"
