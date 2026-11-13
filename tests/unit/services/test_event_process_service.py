"""Unit tests for the event process service."""

from qnagym.services.event_process import (
    check_notification,
    create_event_processing_state,
    get_ordered_events,
    process_event,
    record_interruption_event,
    record_notification_sent,
    recover_from_interruption,
)


class TestCreateEventProcessingState:
    def test_create_default_state(self):
        state = create_event_processing_state()
        assert state.event_counter == 0
        assert state.last_notification_at is None
        assert state.notification_config.enabled

    def test_create_custom_config(self):
        state = create_event_processing_state(
            min_interval_seconds=60.0,
            max_notifications_per_hour=5,
            enabled=False,
        )
        assert state.notification_config.min_interval_seconds == 60.0
        assert state.notification_config.max_notifications_per_hour == 5
        assert not state.notification_config.enabled


class TestProcessEvent:
    def test_process_new_event(self):
        state = create_event_processing_state()
        event, action = process_event(
            state,
            event_type="description_edit",
            source_id="evt-1",
            source="github",
            payload={"body": "edit"},
            created_at=100.0,
        )
        assert action == "Process"
        assert event.event_type == "description_edit"
        assert event.state == "Processed"

    def test_process_duplicate_event(self):
        state = create_event_processing_state()
        process_event(
            state,
            event_type="description_edit",
            source_id="evt-1",
            source="github",
            payload={"body": "edit"},
            created_at=100.0,
        )
        event, action = process_event(
            state,
            event_type="description_edit",
            source_id="evt-1",
            source="github",
            payload={"body": "edit2"},
            created_at=200.0,
        )
        assert action == "Deduplicate"
        assert event.state == "Deduplicated"


class TestRecordInterruption:
    def test_record_stop_signal(self):
        state = create_event_processing_state()
        record = record_interruption_event(
            state,
            reason="stop_signal",
            affected_entity="issue-42",
            occurred_at=100.0,
        )
        assert record.reason == "stop_signal"
        assert record.affected_entity == "issue-42"
        assert record.occurred_at == 100.0
        assert not record.is_recovered

    def test_recover_interruption(self):
        state = create_event_processing_state()
        record_interruption_event(
            state,
            reason="branch_deleted",
            affected_entity="feat/test",
            occurred_at=100.0,
        )
        recovered = recover_from_interruption(
            state,
            reason="branch_deleted",
            affected_entity="feat/test",
            recovered_at=200.0,
            recovery_action="recreated branch",
        )
        assert recovered is not None
        assert recovered.recovered_at == 200.0
        assert recovered.recovery_action == "recreated branch"
        assert recovered.is_recovered


class TestNotification:
    def test_should_notify_first_time(self):
        state = create_event_processing_state()
        should, next_at = check_notification(state, 100.0)
        assert should
        assert next_at == 100.0

    def test_record_notification(self):
        state = create_event_processing_state()
        record_notification_sent(state, 500.0)
        assert state.last_notification_at == 500.0


class TestGetOrderedEvents:
    def test_get_ordered_events(self):
        state = create_event_processing_state()
        process_event(
            state,
            event_type="feedback",
            source_id="c2",
            source="github",
            payload={},
            created_at=200.0,
        )
        process_event(
            state,
            event_type="description_edit",
            source_id="c1",
            source="github",
            payload={},
            created_at=100.0,
        )
        events = get_ordered_events(state)
        assert len(events) == 2
        assert events[0].created_at == 100.0
        assert events[1].created_at == 200.0
