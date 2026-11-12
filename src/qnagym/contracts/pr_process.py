"""PR Process contract module.

Mirrors docs/adr/0006-pr-process.md §1–§5. Pure data shapes and closed
vocabularies; no orchestration logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from qnagym.contracts.constants import (
    CHECK_STATUSES,
    CORRECTION_ATTEMPT_STEPS,
    EVALUATION_RESULTS,
    FEEDBACK_EVENT_TYPES,
    MAX_CORRECTION_ATTEMPTS_PER_BATCH,
    MESSAGE_ROUTING_TARGETS,
    NON_FAILURE_CHECK_STATUSES,
    PR_LIFECYCLE_EVENTS,
    PR_LIFECYCLE_STATES,
    WORKFLOW_COMMENT_MARKER,
)

__all__ = [
    "CHECK_STATUSES",
    "CORRECTION_ATTEMPT_STEPS",
    "EVALUATION_RESULTS",
    "FEEDBACK_EVENT_TYPES",
    "MAX_CORRECTION_ATTEMPTS_PER_BATCH",
    "MESSAGE_ROUTING_TARGETS",
    "NON_FAILURE_CHECK_STATUSES",
    "PR_LIFECYCLE_EVENTS",
    "PR_LIFECYCLE_STATES",
    "WORKFLOW_COMMENT_MARKER",
    "FeedbackEvent",
    "EvaluationResult",
    "CheckResult",
    "CorrectionAttempt",
    "PRMessage",
]


@dataclass
class FeedbackEvent:
    """A feedback item observed on a PR (ADR 0006 §1)."""

    event_type: str
    author: str
    body: str
    comment_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeedbackEvent:
        return cls(
            event_type=str(data.get("event_type", "")),
            author=str(data.get("author", "")),
            body=str(data.get("body", "")),
            comment_id=str(data.get("comment_id", "")),
        )


@dataclass
class EvaluationResult:
    """The outcome of evaluating one feedback item (ADR 0006 §1)."""

    result: str
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvaluationResult:
        return cls(
            result=str(data.get("result", "")),
            confidence=float(data.get("confidence", 0.0)),
            reason=str(data.get("reason", "")),
        )


@dataclass
class CheckResult:
    """A PR check result event (ADR 0006 §2)."""

    name: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckResult:
        return cls(name=str(data.get("name", "")), status=str(data.get("status", "")))


@dataclass
class CorrectionAttempt:
    """One bounded correction attempt within a batch (ADR 0006 §2)."""

    step: str
    batch: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorrectionAttempt:
        return cls(step=str(data.get("step", "")), batch=int(data.get("batch", 0)))


@dataclass
class PRMessage:
    """A workflow-authored message and where it is routed (ADR 0006 §4)."""

    target: str
    what_happened: str
    evidence: str
    decision: str
    completed: str
    pending: str
    automation_state: str
    user_next_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PRMessage:
        return cls(
            target=str(data.get("target", "")),
            what_happened=str(data.get("what_happened", "")),
            evidence=str(data.get("evidence", "")),
            decision=str(data.get("decision", "")),
            completed=str(data.get("completed", "")),
            pending=str(data.get("pending", "")),
            automation_state=str(data.get("automation_state", "")),
            user_next_step=str(data.get("user_next_step", "")),
        )
