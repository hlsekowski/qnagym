"""PR lifecycle service (orchestration).

Mirrors docs/adr/0006-pr-process.md §3. Applies lifecycle events and
tracks post-merge completion; performs no I/O.
"""

from __future__ import annotations

from qnagym.domain.pr_lifecycle import (
    POST_MERGE_STEPS,
    LifecycleError,
    PRLifecycle,
    record_post_merge_step,
    transition,
)

__all__ = [
    "POST_MERGE_STEPS",
    "PRLifecycle",
    "PRLifecycleError",
    "apply_event",
    "complete_post_merge_step",
]


class PRLifecycleError(Exception):
    """An event is not valid for the PR's current state."""

    def __init__(self, message: str, exit_code: int = 2):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def apply_event(lifecycle: PRLifecycle, event: str) -> str:
    """Apply a lifecycle event and return the new state.

    Raises:
        PRLifecycleError: If the event is not valid in the current state.
    """
    try:
        return transition(lifecycle, event)
    except LifecycleError as exc:
        raise PRLifecycleError(str(exc)) from exc


def complete_post_merge_step(lifecycle: PRLifecycle, step: str) -> None:
    """Record that one post-merge step completed.

    Raises:
        PRLifecycleError: If the step is not a known post-merge step.
    """
    try:
        record_post_merge_step(lifecycle, step)
    except LifecycleError as exc:
        raise PRLifecycleError(str(exc)) from exc
