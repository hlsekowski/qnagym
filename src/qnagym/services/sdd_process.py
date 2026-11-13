"""SDD Process service (orchestration).

Mirrors docs/adr/0007-sdd-process.md. Orchestrates SDD task lifecycle,
development cycle, and result handoff to the PR Process; performs no
GitHub I/O.
"""

from __future__ import annotations

from qnagym.contracts.sdd_process import SDDResult, SDDTask, SDDTaskIdentity, SDDTaskInput
from qnagym.domain.sdd_process import (
    determine_result,
    next_development_step,
)


class SDDProcessError(Exception):
    """Error during SDD Process orchestration."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


def create_sdd_task(
    task_id: str,
    source: str,
    source_ref: str,
    accepted_requirements: str,
    branch_name: str | None = None,
    issue_number: int | None = None,
    pr_number: int | None = None,
    feedback_reference: str | None = None,
    check_evidence: str | None = None,
) -> SDDTask:
    """Create a new SDD task in Analyzing state.

    Args:
        task_id: Unique task identifier.
        source: "issue" or "pr".
        source_ref: Issue number or PR number.
        accepted_requirements: The accepted requirements baseline.
        branch_name: The development branch name.
        issue_number: The originating issue number, if any.
        pr_number: The originating PR number, if any.
        feedback_reference: Reference to evaluated PR feedback, if any.
        check_evidence: Reference to failed-check evidence, if any.

    Returns:
        The new SDD task.
    """
    return SDDTask(
        identity=SDDTaskIdentity(
            task_id=task_id,
            source=source,
            source_ref=source_ref,
        ),
        input=SDDTaskInput(
            source=source,
            source_ref=source_ref,
            accepted_requirements=accepted_requirements,
            branch_name=branch_name,
            issue_number=issue_number,
            pr_number=pr_number,
            feedback_reference=feedback_reference,
            check_evidence=check_evidence,
        ),
    )


def advance_task(task: SDDTask) -> str:
    """Advance an SDD task to the next development cycle step.

    Args:
        task: The SDD task to advance.

    Returns:
        The next action to take.
    """
    return next_development_step(task)


def deliver_task(task: SDDTask) -> SDDResult:
    """Determine and return the SDD result for delivery to the PR Process.

    Args:
        task: The SDD task to deliver.

    Returns:
        The SDD result (Successful or Incomplete).
    """
    return determine_result(task)


__all__ = [
    "SDDProcessError",
    "advance_task",
    "create_sdd_task",
    "deliver_task",
]
