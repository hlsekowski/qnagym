"""PR check monitoring logic (pure business logic, no I/O).

Mirrors docs/adr/0006-pr-process.md §2. Decides what a check result
means and tracks the correction-attempt budget; performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from qnagym.contracts.constants import (
    MAX_CORRECTION_ATTEMPTS_PER_BATCH,
    NON_FAILURE_CHECK_STATUSES,
)
from qnagym.contracts.pr_process import CheckResult

# Actions the monitoring loop can produce.
ACTION_AWAIT = "Await"
ACTION_CORRECT = "Correct"
ACTION_EXHAUSTED = "Exhausted"
ACTION_UNRESOLVABLE = "Unresolvable"


@dataclass
class CheckDecision:
    """What the PR Process should do about one check result."""

    action: str
    reason: str


@dataclass
class CorrectionBatch:
    """The correction-attempt budget for one batch.

    A batch ends when its attempt limit is exhausted. A new batch starts
    only on an explicit retry request; reopening the PR does not reset
    the counter (ADR 0006 §2).
    """

    limit: int = MAX_CORRECTION_ATTEMPTS_PER_BATCH
    attempts_used: int = 0
    history: list[str] = field(default_factory=list)

    @property
    def exhausted(self) -> bool:
        return self.attempts_used >= self.limit

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.attempts_used)

    def record_attempt(self, description: str) -> None:
        """Record one correction attempt against the budget."""
        self.attempts_used += 1
        self.history.append(description)

    def start_new_batch(self) -> None:
        """Start a new batch on an explicit retry, preserving history."""
        self.attempts_used = 0


def classify_check(result: CheckResult) -> str:
    """Classify a check status as awaiting, failing, or non-failing.

    Cancelled, skipped and infrastructure-failed are not development
    failures: they are awaited or re-run, and they do not spend an
    attempt (ADR 0006 §2; docs/workflow.md step 8).
    """
    if result.status == "Failed":
        return "failed"
    if result.status in NON_FAILURE_CHECK_STATUSES:
        return "non-failure"
    return "unknown"


def decide_check_action(result: CheckResult, batch: CorrectionBatch) -> CheckDecision:
    """Decide the action for one check result.

    Args:
        result: The check result event.
        batch: The current correction batch.

    Returns:
        The action the PR Process should take.
    """
    kind = classify_check(result)

    if kind == "non-failure":
        return CheckDecision(ACTION_AWAIT, f"{result.status} is not a development failure")

    if kind == "unknown":
        return CheckDecision(ACTION_UNRESOLVABLE, f"unrecognised status {result.status!r}")

    if batch.exhausted:
        return CheckDecision(
            ACTION_EXHAUSTED,
            f"batch exhausted after {batch.attempts_used} attempts",
        )

    return CheckDecision(
        ACTION_CORRECT,
        f"{batch.remaining} attempt(s) left in this batch",
    )
