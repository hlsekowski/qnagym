"""Task execution model contracts (pure data shapes, no logic).

Mirrors docs/adr/0004-worker-task-model.md. Defines the worker/task
vocabulary, scheduling, time, observation and execution-state rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# --- Task kinds (ADR 0004 §1) ---

TASK_KIND_ISSUE_EVALUATION = "issue_evaluation"
TASK_KIND_SDD_CYCLE = "sdd_cycle"
TASK_KIND_FEEDBACK_EVALUATION = "feedback_evaluation"
TASK_KIND_CHECK_RESULT_HANDLING = "check_result_handling"
TASK_KIND_POST_MERGE_COMPLETION = "post_merge_completion"
TASK_KIND_OBSERVATION = "observation"

TASK_KINDS = frozenset(
    {
        TASK_KIND_ISSUE_EVALUATION,
        TASK_KIND_SDD_CYCLE,
        TASK_KIND_FEEDBACK_EVALUATION,
        TASK_KIND_CHECK_RESULT_HANDLING,
        TASK_KIND_POST_MERGE_COMPLETION,
        TASK_KIND_OBSERVATION,
    }
)

# --- Priority classes (ADR 0004 §1, §3) ---

PRIORITY_SHORT = "short"
PRIORITY_LONG = "long"

PRIORITY_CLASSES = frozenset({PRIORITY_SHORT, PRIORITY_LONG})

# Task kind -> priority class mapping (implementation specification concern)
TASK_KIND_PRIORITY: dict[str, str] = {
    TASK_KIND_ISSUE_EVALUATION: PRIORITY_SHORT,
    TASK_KIND_SDD_CYCLE: PRIORITY_LONG,
    TASK_KIND_FEEDBACK_EVALUATION: PRIORITY_SHORT,
    TASK_KIND_CHECK_RESULT_HANDLING: PRIORITY_SHORT,
    TASK_KIND_POST_MERGE_COMPLETION: PRIORITY_SHORT,
    TASK_KIND_OBSERVATION: PRIORITY_SHORT,
}

# --- Task states (ADR 0004 §2) ---

TASK_STATE_QUEUED = "Queued"
TASK_STATE_RUNNING = "Running"
TASK_STATE_COMPLETED = "Completed"
TASK_STATE_FAILED = "Failed"
TASK_STATE_OBSOLETE = "Obsolete"

TASK_STATES = frozenset(
    {
        TASK_STATE_QUEUED,
        TASK_STATE_RUNNING,
        TASK_STATE_COMPLETED,
        TASK_STATE_FAILED,
        TASK_STATE_OBSOLETE,
    }
)

# Terminal states
TERMINAL_STATES = frozenset({TASK_STATE_COMPLETED, TASK_STATE_FAILED, TASK_STATE_OBSOLETE})

# --- Task identity fields (ADR 0004 §3) ---

# A task is identified by: kind, work_item, target, revision/generation.
# Identity uniqueness prevents duplicate logical tasks.


@dataclass(frozen=True)
class TaskIdentity:
    """The immutable identity of a logical task (ADR 0004 §3).

    A logical task may span multiple execution attempts. An explicit
    generation is included when a new logical task is authorized by an
    explicit retry request.
    """

    kind: str
    work_item: str | None
    target: str
    revision: str
    generation: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskIdentity:
        return cls(
            kind=str(data["kind"]),
            work_item=data.get("work_item"),
            target=str(data["target"]),
            revision=str(data["revision"]),
            generation=int(data.get("generation", 0)),
        )


@dataclass
class Task:
    """A bounded unit of execution for one step of one process (ADR 0004 §1).

    Times are Unix epoch seconds, UTC (ADR 0004 §4).
    """

    identity: TaskIdentity
    created_time: float
    not_before_time: float
    event_time: float | None
    state: str = TASK_STATE_QUEUED
    priority: str = PRIORITY_SHORT
    max_duration: float = 300.0
    retry_limit: int = 3
    attempt_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "created_time": self.created_time,
            "not_before_time": self.not_before_time,
            "event_time": self.event_time,
            "state": self.state,
            "priority": self.priority,
            "max_duration": self.max_duration,
            "retry_limit": self.retry_limit,
            "attempt_count": self.attempt_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            identity=TaskIdentity.from_dict(data["identity"]),
            created_time=float(data["created_time"]),
            not_before_time=float(data["not_before_time"]),
            event_time=data.get("event_time"),
            state=str(data.get("state", TASK_STATE_QUEUED)),
            priority=str(data.get("priority", PRIORITY_SHORT)),
            max_duration=float(data.get("max_duration", 300.0)),
            retry_limit=int(data.get("retry_limit", 3)),
            attempt_count=int(data.get("attempt_count", 0)),
        )

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def is_eligible(self) -> bool:
        """A task is eligible when not-before time reached and not terminal."""
        return self.state == TASK_STATE_QUEUED and not self.is_terminal


@dataclass
class ExecutionAttempt:
    """One run of a logical task (ADR 0004 §2).

    Attempt number, outcome, retry deadline, and claim are tracked in
    execution state. Infrastructure retries are additional execution
    attempts of the same logical task; they do not create a new identity.
    """

    attempt_number: int
    outcome: str | None = None
    retry_deadline: float | None = None
    claim_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionAttempt:
        return cls(
            attempt_number=int(data["attempt_number"]),
            outcome=data.get("outcome"),
            retry_deadline=data.get("retry_deadline"),
            claim_id=data.get("claim_id"),
        )


@dataclass
class Claim:
    """Exclusive right of one worker to run one task, with an expiry (ADR 0004 §7)."""

    task_identity: TaskIdentity
    worker_id: str
    expiry_time: float
    fencing_generation: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Claim:
        return cls(
            task_identity=TaskIdentity.from_dict(data["task_identity"]),
            worker_id=str(data["worker_id"]),
            expiry_time=float(data["expiry_time"]),
            fencing_generation=int(data["fencing_generation"]),
        )

    def is_expired(self, now: float) -> bool:
        return now >= self.expiry_time


@dataclass
class ExecutionState:
    """Durable local records that must survive restarts (ADR 0004 §6).

    Holds logical task identities and lifecycle states, execution attempt
    counters and retry deadlines, correction-attempt accounting, explicit
    retry authorizations, observation watermarks, claim ownership and
    fencing generations, and scheduling information.
    """

    tasks: dict[str, Task] = field(default_factory=dict)
    attempts: dict[str, list[ExecutionAttempt]] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    observation_watermark: float = 0.0
    processed_event_ids: set[str] = field(default_factory=set)
    generation_counter: int = 0
    correction_attempts: dict[str, int] = field(default_factory=dict)

    def task_key(self, identity: TaskIdentity) -> str:
        """Stable key for a task identity."""
        return (
            f"{identity.kind}|{identity.work_item or ''}|"
            f"{identity.target}|{identity.revision}|{identity.generation}"
        )

    def get_task(self, identity: TaskIdentity) -> Task | None:
        return self.tasks.get(self.task_key(identity))

    def put_task(self, task: Task) -> None:
        self.tasks[self.task_key(task.identity)] = task

    def get_attempts(self, identity: TaskIdentity) -> list[ExecutionAttempt]:
        return self.attempts.get(self.task_key(identity), [])

    def add_attempt(self, identity: TaskIdentity, attempt: ExecutionAttempt) -> None:
        key = self.task_key(identity)
        self.attempts.setdefault(key, []).append(attempt)

    def get_claim(self, task_key: str) -> Claim | None:
        return self.claims.get(task_key)

    def put_claim(self, claim: Claim) -> None:
        self.claims[self.task_key(claim.task_identity)] = claim

    def remove_claim(self, task_key: str) -> None:
        self.claims.pop(task_key, None)

    def increment_generation(self) -> int:
        self.generation_counter += 1
        return self.generation_counter

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": {k: t.to_dict() for k, t in self.tasks.items()},
            "attempts": {k: [a.to_dict() for a in v] for k, v in self.attempts.items()},
            "claims": {k: c.to_dict() for k, c in self.claims.items()},
            "observation_watermark": self.observation_watermark,
            "processed_event_ids": sorted(self.processed_event_ids),
            "generation_counter": self.generation_counter,
            "correction_attempts": self.correction_attempts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionState:
        state = cls()
        state.tasks = {k: Task.from_dict(v) for k, v in data.get("tasks", {}).items()}
        state.attempts = {
            k: [ExecutionAttempt.from_dict(a) for a in v]
            for k, v in data.get("attempts", {}).items()
        }
        state.claims = {k: Claim.from_dict(v) for k, v in data.get("claims", {}).items()}
        state.observation_watermark = float(data.get("observation_watermark", 0.0))
        state.processed_event_ids = set(data.get("processed_event_ids", []))
        state.generation_counter = int(data.get("generation_counter", 0))
        state.correction_attempts = dict(data.get("correction_attempts", {}))
        return state
