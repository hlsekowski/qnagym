"""PR check monitoring service (orchestration).

Mirrors docs/adr/0006-pr-process.md §2. Classifies check results and
tracks the correction-attempt budget; performs no GitHub I/O.
"""

from __future__ import annotations

from qnagym.contracts.pr_process import CheckResult
from qnagym.domain.pr_checks import (
    ACTION_AWAIT,
    ACTION_CORRECT,
    ACTION_EXHAUSTED,
    ACTION_UNRESOLVABLE,
    CheckDecision,
    CorrectionBatch,
    classify_check,
    decide_check_action,
)


class PRChecksError(Exception):
    """Error during PR check monitoring."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def monitor_check(
    result: CheckResult,
    batch: CorrectionBatch,
) -> CheckDecision:
    """Decide what to do about one PR check result.

    Args:
        result: The check result event.
        batch: The current correction batch, mutated when an attempt is
            recorded by the caller.

    Returns:
        The action the PR Process should take.
    """
    return decide_check_action(result, batch)


def record_correction(batch: CorrectionBatch, description: str) -> None:
    """Record one correction attempt against the batch budget."""
    batch.record_attempt(description)


def request_retry(batch: CorrectionBatch) -> None:
    """Start a new batch on an explicit retry, preserving history."""
    batch.start_new_batch()


def all_checks_clear(results: list[CheckResult]) -> bool:
    """True when no check is failing.

    Pending, running, cancelled, skipped and infrastructure-failed are
    not failures, so they do not block clearance.
    """
    return all(classify_check(result) != "failed" for result in results)


__all__ = [
    "ACTION_AWAIT",
    "ACTION_CORRECT",
    "ACTION_EXHAUSTED",
    "ACTION_UNRESOLVABLE",
    "PRChecksError",
    "all_checks_clear",
    "monitor_check",
    "record_correction",
    "request_retry",
]
