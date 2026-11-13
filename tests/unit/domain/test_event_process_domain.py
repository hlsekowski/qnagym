"""Unit tests for the event processing domain logic."""

from qnagym.contracts.event_process import (
    EVENT_STATE_DEDUPLICATED,
    EVENT_STATE_PENDING,
    EVENT_STATE_PROCESSED,
    EventIdentity,
    EventProcessingState,
    ProcessedEvent,
)
from qnagym.domain.event_process import (
    handle_interruption,
    is_duplicate_event,
    is_interruption_reason,
    mark_event_deduplicated,
    mark_event_processed,
    order_events,
    record_event,
    record_notification,
    recover_interruption,
    should_notify,
)


def _identity(event_type="description_edit", source_id="evt-1", source="github"):
    return EventIdentity(event_type=event_type, source_id=source_id, source=source)


def _event(
    identity=None,
    event_type="description_edit",
    payload=None,
    created_at=100.0,
    processed_at=None,
    state=EVENT_STATE_PENDING,
):
    if identity is None:
        identity = _identity(event_type=event_type)
    if payload is None:
        payload = {}
    return ProcessedEvent(
        identity=identity,
        event_type=event_type,
        payload=payload,
        created_at=created_at,
        processed_at=processed_at,
        state=state,
    )


class TestOrderEvents:
    def test_orders_by_created_time(self):
        e1 = _event(created_at=200.0)
        e2 = _event(created_at=100.0)
        e3 = _event(created_at=150.0)
        ordered = order_events([e1, e2, e3])
        assert ordered[0] is e2
        assert ordered[1] is e3
        assert ordered[2] is e1

    def test_empty_list(self):
        assert order_events([]) == []


class TestIsDuplicateEvent:
    def test_new_event_not_duplicate(self):
        state = EventProcessingState()
        identity = _identity()
        assert not is_duplicate_event(state, identity)

    def test_processed_event_is_duplicate(self):
        state = EventProcessingState()
        identity = _identity()
        event = _event(identity=identity, state=EVENT_STATE_PROCESSED)
        state.record_event(event)
        assert is_duplicate_event(state, identity)


class TestRecordEvent:
    def test_record_new_event(self):
        state = EventProcessingState()
        event = record_event(
            state,
            event_type="feedback",
            source_id="c1",
            source="github",
            payload={"body": "fix"},
            created_at=100.0,
        )
        assert event.event_type == "feedback"
        assert event.state == EVENT_STATE_PENDING
        assert state.event_counter == 1

    def test_record_event_increments_counter(self):
        state = EventProcessingState()
        record_event(state, "feedback", "c1", "github", {}, 100.0)
        record_event(state, "feedback", "c2", "github", {}, 200.0)
        assert state.event_counter == 2


class TestMarkEventProcessed:
    def test_mark_processed(self):
        state = EventProcessingState()
        event = _event(state=EVENT_STATE_PENDING)
        state.record_event(event)
        mark_event_processed(state, event)
        assert event.state == EVENT_STATE_PROCESSED


class TestMarkEventDeduplicated:
    def test_mark_deduplicated(self):
        state = EventProcessingState()
        event = _event(state=EVENT_STATE_PENDING)
        state.record_event(event)
        mark_event_deduplicated(state, event)
        assert event.state == EVENT_STATE_DEDUPLICATED


class TestHandleInterruption:
    def test_record_stop_signal(self):
        state = EventProcessingState()
        interruption = handle_interruption(state, "stop_signal", "issue-42", 100.0)
        assert interruption.reason == "stop_signal"
        assert interruption.affected_entity == "issue-42"
        assert interruption.occurred_at == 100.0
        assert not interruption.is_recovered

    def test_record_branch_deleted(self):
        state = EventProcessingState()
        interruption = handle_interruption(state, "branch_deleted", "feat/test", 200.0)
        assert interruption.reason == "branch_deleted"
        assert interruption.affected_entity == "feat/test"


class TestRecoverInterruption:
    def test_recover_interruption(self):
        state = EventProcessingState()
        handle_interruption(state, "stop_signal", "issue-42", 100.0)
        recovered = recover_interruption(state, "stop_signal", "issue-42", 300.0, "restarted")
        assert recovered is not None
        assert recovered.recovered_at == 300.0
        assert recovered.recovery_action == "restarted"
        assert recovered.is_recovered

    def test_recover_nonexistent_interruption(self):
        state = EventProcessingState()
        result = recover_interruption(state, "stop_signal", "issue-99", 300.0, "restarted")
        assert result is None


class TestShouldNotify:
    def test_should_notify_first_time(self):
        state = EventProcessingState()
        should, next_at = should_notify(state, 100.0)
        assert should
        assert next_at == 100.0

    def test_should_notify_after_interval(self):
        state = EventProcessingState()
        state.last_notification_at = 100.0
        should, next_at = should_notify(state, 500.0)
        assert should
        assert next_at == 500.0

    def test_should_not_notify_before_interval(self):
        state = EventProcessingState()
        state.last_notification_at = 100.0
        should, next_at = should_notify(state, 200.0)
        assert not should
        assert next_at == 100.0


class TestRecordNotification:
    def test_record_notification(self):
        state = EventProcessingState()
        record_notification(state, 500.0)
        assert state.last_notification_at == 500.0


class TestIsInterruptionReason:
    def test_valid_reasons(self):
        assert is_interruption_reason("stop_signal")
        assert is_interruption_reason("branch_deleted")
        assert is_interruption_reason("issue_closed")
        assert is_interruption_reason("pr_closed")

    def test_invalid_reason(self):
        assert not is_interruption_reason("invalid_reason")
