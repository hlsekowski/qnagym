"""Event processing contracts (pure data shapes, no logic).

Mirrors docs/adr/0003 follow-up item 5. Defines event ordering,
interruption, recovery, deduplication, and notification frequency
for the Issue, SDD, and PR processes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# --- Event types ---

EVENT_TYPE_DESCRIPTION_EDIT = "description_edit"
EVENT_TYPE_FEEDBACK = "feedback"
EVENT_TYPE_CHECK_RESULT = "check_result"
EVENT_TYPE_PR_CLOSED = "pr_closed"
EVENT_TYPE_PR_REOPENED = "pr_reopened"
EVENT_TYPE_ISSUE_CLOSED = "issue_closed"
EVENT_TYPE_ISSUE_REOPENED = "issue_reopened"
EVENT_TYPE_BRANCH_DELETED = "branch_deleted"
EVENT_TYPE_STOP_SIGNAL = "stop_signal"

EVENT_TYPES = frozenset(
    {
        EVENT_TYPE_DESCRIPTION_EDIT,
        EVENT_TYPE_FEEDBACK,
        EVENT_TYPE_CHECK_RESULT,
        EVENT_TYPE_PR_CLOSED,
        EVENT_TYPE_PR_REOPENED,
        EVENT_TYPE_ISSUE_CLOSED,
        EVENT_TYPE_ISSUE_REOPENED,
        EVENT_TYPE_BRANCH_DELETED,
        EVENT_TYPE_STOP_SIGNAL,
    }
)

# --- Event states ---

EVENT_STATE_PENDING = "Pending"
EVENT_STATE_PROCESSED = "Processed"
EVENT_STATE_DEDUPLICATED = "Deduplicated"
EVENT_STATE_INTERRUPTED = "Interrupted"
EVENT_STATE_RECOVERED = "Recovered"

EVENT_STATES = frozenset(
    {
        EVENT_STATE_PENDING,
        EVENT_STATE_PROCESSED,
        EVENT_STATE_DEDUPLICATED,
        EVENT_STATE_INTERRUPTED,
        EVENT_STATE_RECOVERED,
    }
)

# --- Interruption reasons ---

INTERRUPTION_STOP_SIGNAL = "stop_signal"
INTERRUPTION_BRANCH_DELETED = "branch_deleted"
INTERRUPTION_ISSUE_CLOSED = "issue_closed"
INTERRUPTION_PR_CLOSED = "pr_closed"

INTERRUPTION_REASONS = frozenset(
    {
        INTERRUPTION_STOP_SIGNAL,
        INTERRUPTION_BRANCH_DELETED,
        INTERRUPTION_ISSUE_CLOSED,
        INTERRUPTION_PR_CLOSED,
    }
)


@dataclass(frozen=True)
class EventIdentity:
    """The immutable identity of an event for deduplication."""

    event_type: str
    source_id: str  # GitHub event ID, comment ID, check run ID, etc.
    source: str  # "github" or "local"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventIdentity:
        return cls(
            event_type=str(data["event_type"]),
            source_id=str(data["source_id"]),
            source=str(data["source"]),
        )


@dataclass
class ProcessedEvent:
    """A processed event record for deduplication (ADR 0003 follow-up item 5)."""

    identity: EventIdentity
    event_type: str
    payload: dict[str, Any]
    created_at: float
    processed_at: float | None = None
    state: str = EVENT_STATE_PENDING
    interruption_reason: str | None = None
    recovered: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "event_type": self.event_type,
            "payload": self.payload,
            "created_at": self.created_at,
            "processed_at": self.processed_at,
            "state": self.state,
            "interruption_reason": self.interruption_reason,
            "recovered": self.recovered,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessedEvent:
        return cls(
            identity=EventIdentity.from_dict(data["identity"]),
            event_type=str(data["event_type"]),
            payload=dict(data.get("payload") or {}),
            created_at=float(data["created_at"]),
            processed_at=data.get("processed_at"),
            state=str(data.get("state", EVENT_STATE_PENDING)),
            interruption_reason=data.get("interruption_reason"),
            recovered=bool(data.get("recovered", False)),
        )

    @property
    def is_processed(self) -> bool:
        return self.state == EVENT_STATE_PROCESSED

    @property
    def is_duplicate(self) -> bool:
        return self.state == EVENT_STATE_DEDUPLICATED

    @property
    def is_interrupted(self) -> bool:
        return self.state == EVENT_STATE_INTERRUPTED

    @property
    def is_recovered(self) -> bool:
        return self.state == EVENT_STATE_RECOVERED


@dataclass
class NotificationConfig:
    """Configurable notification frequency (ADR 0003 follow-up item 5)."""

    min_interval_seconds: float = 300.0  # 5 minutes default
    max_notifications_per_hour: int = 12
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationConfig:
        return cls(
            min_interval_seconds=float(data.get("min_interval_seconds", 300.0)),
            max_notifications_per_hour=int(data.get("max_notifications_per_hour", 12)),
            enabled=bool(data.get("enabled", True)),
        )

    def should_notify(self, last_notification_at: float | None, now: float) -> bool:
        """Check whether a notification should be sent based on frequency limits."""
        if not self.enabled:
            return False
        if last_notification_at is None:
            return True
        return (now - last_notification_at) >= self.min_interval_seconds


@dataclass
class InterruptionRecord:
    """A record of an interruption event (ADR 0003 follow-up item 5)."""

    reason: str
    affected_entity: str  # issue number, PR number, branch name, etc.
    occurred_at: float
    recovered_at: float | None = None
    recovery_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InterruptionRecord:
        return cls(
            reason=str(data["reason"]),
            affected_entity=str(data["affected_entity"]),
            occurred_at=float(data["occurred_at"]),
            recovered_at=data.get("recovered_at"),
            recovery_action=data.get("recovery_action"),
        )

    @property
    def is_recovered(self) -> bool:
        return self.recovered_at is not None


@dataclass
class EventProcessingState:
    """Durable state for event processing (ADR 0003 follow-up item 5).

    Holds processed events for deduplication, interruption records,
    and notification state.
    """

    processed_events: dict[str, ProcessedEvent] = field(default_factory=dict)
    interruptions: dict[str, InterruptionRecord] = field(default_factory=dict)
    notification_config: NotificationConfig = field(default_factory=NotificationConfig)
    last_notification_at: float | None = None
    event_counter: int = 0

    def event_key(self, identity: EventIdentity) -> str:
        """Stable key for an event identity."""
        return f"{identity.event_type}|{identity.source}|{identity.source_id}"

    def get_event(self, identity: EventIdentity) -> ProcessedEvent | None:
        return self.processed_events.get(self.event_key(identity))

    def record_event(self, event: ProcessedEvent) -> None:
        self.processed_events[self.event_key(event.identity)] = event

    def is_duplicate(self, identity: EventIdentity) -> bool:
        existing = self.get_event(identity)
        return existing is not None and existing.is_processed

    def record_interruption(self, interruption: InterruptionRecord) -> None:
        self.interruptions[f"{interruption.reason}|{interruption.affected_entity}"] = interruption

    def get_interruption(self, reason: str, affected_entity: str) -> InterruptionRecord | None:
        return self.interruptions.get(f"{reason}|{affected_entity}")

    def increment_event_counter(self) -> int:
        self.event_counter += 1
        return self.event_counter

    def to_dict(self) -> dict[str, Any]:
        return {
            "processed_events": {k: e.to_dict() for k, e in self.processed_events.items()},
            "interruptions": {k: i.to_dict() for k, i in self.interruptions.items()},
            "notification_config": self.notification_config.to_dict(),
            "last_notification_at": self.last_notification_at,
            "event_counter": self.event_counter,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventProcessingState:
        state = cls()
        state.processed_events = {
            k: ProcessedEvent.from_dict(v) for k, v in data.get("processed_events", {}).items()
        }
        state.interruptions = {
            k: InterruptionRecord.from_dict(v) for k, v in data.get("interruptions", {}).items()
        }
        state.notification_config = NotificationConfig.from_dict(
            data.get("notification_config", {})
        )
        state.last_notification_at = data.get("last_notification_at")
        state.event_counter = int(data.get("event_counter", 0))
        return state
