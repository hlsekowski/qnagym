"""Event processing domain logic (pure business logic, no I/O).

Mirrors docs/adr/0003 follow-up item 5. Implements event ordering,
interruption handling, recovery, deduplication, and notification
frequency; performs no GitHub I/O.
"""

from __future__ import annotations

from typing import Any

from qnagym.contracts.event_process import (
    EVENT_STATE_DEDUPLICATED,
    EVENT_STATE_PENDING,
    EVENT_STATE_PROCESSED,
    INTERRUPTION_BRANCH_DELETED,
    INTERRUPTION_ISSUE_CLOSED,
    INTERRUPTION_PR_CLOSED,
    INTERRUPTION_STOP_SIGNAL,
    EventIdentity,
    EventProcessingState,
    InterruptionRecord,
    ProcessedEvent,
)

# Actions the event processing can produce.
ACTION_PROCESS = "Process"
ACTION_DEDUPLICATE = "Deduplicate"
ACTION_INTERRUPT = "Interrupt"
ACTION_RECOVER = "Recover"
ACTION_NOTIFY = "Notify"
ACTION_NONE = "None"


def order_events(events: list[ProcessedEvent]) -> list[ProcessedEvent]:
    """Order events by event time, then creation time (ADR 0004 §4).

    When event time is absent, tasks are ordered by created time, then
    by a deterministic tiebreaker (event type, source, source ID).
    """

    def sort_key(event: ProcessedEvent) -> tuple[float, float, str, str, str]:
        # Use created_at as event time fallback
        event_time = event.created_at
        return (
            event_time,
            event.created_at,
            event.event_type,
            event.identity.source,
            event.identity.source_id,
        )

    return sorted(events, key=sort_key)


def is_duplicate_event(state: EventProcessingState, identity: EventIdentity) -> bool:
    """Check whether an event has already been processed (deduplication).

    Same event processed once (ADR 0003 follow-up item 5).
    """
    return state.is_duplicate(identity)


def record_event(
    state: EventProcessingState,
    event_type: str,
    source_id: str,
    source: str,
    payload: dict[str, Any],
    created_at: float,
) -> ProcessedEvent:
    """Record a new event for deduplication tracking.

    Args:
        state: The event processing state.
        event_type: The type of event.
        source_id: The GitHub event ID, comment ID, etc.
        source: "github" or "local".
        payload: The event payload.
        created_at: When the event occurred.

    Returns:
        The recorded ProcessedEvent.
    """
    state.increment_event_counter()
    identity = EventIdentity(
        event_type=event_type,
        source_id=source_id,
        source=source,
    )
    event = ProcessedEvent(
        identity=identity,
        event_type=event_type,
        payload=payload,
        created_at=created_at,
        state=EVENT_STATE_PENDING,
    )
    state.record_event(event)
    return event


def mark_event_processed(state: EventProcessingState, event: ProcessedEvent) -> None:
    """Mark an event as processed."""
    event.state = EVENT_STATE_PROCESSED
    event.processed_at = event.created_at  # will be set by caller
    state.record_event(event)


def mark_event_deduplicated(state: EventProcessingState, event: ProcessedEvent) -> None:
    """Mark an event as deduplicated (already processed)."""
    event.state = EVENT_STATE_DEDUPLICATED
    state.record_event(event)


def handle_interruption(
    state: EventProcessingState,
    reason: str,
    affected_entity: str,
    occurred_at: float,
) -> InterruptionRecord:
    """Record an interruption event (ADR 0003 follow-up item 5).

    Interruption reasons:
    - stop_signal: GitHub-side stop signal
    - branch_deleted: development branch deleted
    - issue_closed: issue closed before PR exists
    - pr_closed: PR closed without merge
    """
    interruption = InterruptionRecord(
        reason=reason,
        affected_entity=affected_entity,
        occurred_at=occurred_at,
    )
    state.record_interruption(interruption)
    return interruption


def recover_interruption(
    state: EventProcessingState,
    reason: str,
    affected_entity: str,
    recovered_at: float,
    recovery_action: str,
) -> InterruptionRecord | None:
    """Recover from an interruption (ADR 0003 follow-up item 5).

    Recovery mechanisms for worker/task state after interruption.
    """
    interruption = state.get_interruption(reason, affected_entity)
    if interruption is None:
        return None

    interruption.recovered_at = recovered_at
    interruption.recovery_action = recovery_action
    state.record_interruption(interruption)
    return interruption


def should_notify(state: EventProcessingState, now: float) -> tuple[bool, float | None]:
    """Check whether a notification should be sent based on frequency limits.

    Returns (should_notify, next_notification_at).
    """
    config = state.notification_config
    if not config.should_notify(state.last_notification_at, now):
        return False, state.last_notification_at

    return True, now


def record_notification(state: EventProcessingState, now: float) -> None:
    """Record that a notification was sent."""
    state.last_notification_at = now


def is_interruption_reason(reason: str) -> bool:
    """Check whether a reason is a valid interruption reason."""
    return reason in {
        INTERRUPTION_STOP_SIGNAL,
        INTERRUPTION_BRANCH_DELETED,
        INTERRUPTION_ISSUE_CLOSED,
        INTERRUPTION_PR_CLOSED,
    }


__all__ = [
    "ACTION_DEDUPLICATE",
    "ACTION_INTERRUPT",
    "ACTION_NONE",
    "ACTION_NOTIFY",
    "ACTION_PROCESS",
    "ACTION_RECOVER",
    "handle_interruption",
    "is_duplicate_event",
    "is_interruption_reason",
    "mark_event_deduplicated",
    "mark_event_processed",
    "order_events",
    "record_event",
    "record_notification",
    "recover_interruption",
    "should_notify",
]
