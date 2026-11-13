"""Event processing service (orchestration).

Mirrors docs/adr/0003 follow-up item 5. Orchestrates event ordering,
interruption handling, recovery, deduplication, and notification
frequency; performs no GitHub I/O.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.event_process import (
    EventIdentity,
    EventProcessingState,
    InterruptionRecord,
    NotificationConfig,
    ProcessedEvent,
)
from qnagym.domain.event_process import (
    ACTION_DEDUPLICATE,
    ACTION_PROCESS,
    handle_interruption,
    is_interruption_reason,
    mark_event_deduplicated,
    mark_event_processed,
    order_events,
    record_event,
    record_notification,
    recover_interruption,
    should_notify,
)


class EventProcessError(Exception):
    """Error during event processing orchestration."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


def create_event_processing_state(
    min_interval_seconds: float = 300.0,
    max_notifications_per_hour: int = 12,
    enabled: bool = True,
) -> EventProcessingState:
    """Create a new event processing state.

    Args:
        min_interval_seconds: Minimum seconds between notifications.
        max_notifications_per_hour: Maximum notifications per hour.
        enabled: Whether notifications are enabled.

    Returns:
        The new EventProcessingState.
    """
    return EventProcessingState(
        notification_config=NotificationConfig(
            min_interval_seconds=min_interval_seconds,
            max_notifications_per_hour=max_notifications_per_hour,
            enabled=enabled,
        )
    )


def process_event(
    state: EventProcessingState,
    event_type: str,
    source_id: str,
    source: str,
    payload: dict[str, Any],
    created_at: float,
) -> tuple[ProcessedEvent, str]:
    """Process an event with deduplication.

    Args:
        state: The event processing state.
        event_type: The type of event.
        source_id: The GitHub event ID, comment ID, etc.
        source: "github" or "local".
        payload: The event payload.
        created_at: When the event occurred.

    Returns:
        (event, action) where action is "Process" or "Deduplicate".
    """
    identity = EventIdentity(
        event_type=event_type,
        source_id=source_id,
        source=source,
    )

    existing = state.get_event(identity)
    if existing is not None and existing.is_processed:
        mark_event_deduplicated(state, existing)
        return existing, ACTION_DEDUPLICATE

    event = record_event(state, event_type, source_id, source, payload, created_at)
    mark_event_processed(state, event)
    return event, ACTION_PROCESS


def record_interruption_event(
    state: EventProcessingState,
    reason: str,
    affected_entity: str,
    occurred_at: float,
) -> InterruptionRecord:
    """Record an interruption event.

    Args:
        state: The event processing state.
        reason: The interruption reason.
        affected_entity: The affected entity (issue number, PR number, etc.).
        occurred_at: When the interruption occurred.

    Returns:
        The InterruptionRecord.
    """
    if not is_interruption_reason(reason):
        raise EventProcessError(f"invalid interruption reason: {reason}")

    return handle_interruption(state, reason, affected_entity, occurred_at)


def recover_from_interruption(
    state: EventProcessingState,
    reason: str,
    affected_entity: str,
    recovered_at: float,
    recovery_action: str,
) -> InterruptionRecord | None:
    """Recover from an interruption.

    Args:
        state: The event processing state.
        reason: The interruption reason.
        affected_entity: The affected entity.
        recovered_at: When recovery occurred.
        recovery_action: The recovery action taken.

    Returns:
        The recovered InterruptionRecord, or None if no interruption found.
    """
    return recover_interruption(state, reason, affected_entity, recovered_at, recovery_action)


def check_notification(state: EventProcessingState, now: float) -> tuple[bool, float | None]:
    """Check whether a notification should be sent.

    Args:
        state: The event processing state.
        now: Current time as Unix epoch seconds.

    Returns:
        (should_notify, next_notification_at).
    """
    return should_notify(state, now)


def record_notification_sent(state: EventProcessingState, now: float) -> None:
    """Record that a notification was sent."""
    record_notification(state, now)


def get_ordered_events(state: EventProcessingState) -> list[ProcessedEvent]:
    """Get all events ordered by event time, then creation time."""
    return order_events(list(state.processed_events.values()))


__all__ = [
    "EventProcessError",
    "check_notification",
    "create_event_processing_state",
    "get_ordered_events",
    "process_event",
    "record_interruption_event",
    "record_notification_sent",
    "recover_from_interruption",
]
