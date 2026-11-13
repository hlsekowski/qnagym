"""PR lifecycle state machine (pure business logic, no I/O).

Mirrors docs/adr/0006-pr-process.md §3. Tracks a PR from monitoring
through post-merge completion; performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

from qnagym.contracts.constants import PR_LIFECYCLE_STATES

# Events that drive transitions.
EVENT_CHECKS_PENDING = "ChecksPending"
EVENT_CHECKS_PASS_CLEAR = "ChecksPassClear"
EVENT_CHECKS_PASS_PENDING = "ChecksPassPending"
EVENT_CLARIFICATION_RESOLVED = "ClarificationResolved"
EVENT_NEW_FEEDBACK = "NewFeedback"
EVENT_PR_CLOSED = "PRClosed"
EVENT_PR_REOPENED = "PRReopened"
EVENT_ISSUE_CLOSED = "IssueClosed"
EVENT_PR_MERGED = "PRMerged"
EVENT_POST_MERGE_STARTED = "PostMergeStarted"
EVENT_POST_MERGE_OK = "PostMergeOk"
EVENT_POST_MERGE_FAILED = "PostMergeFailed"

# The two post-merge steps, tracked separately so a retry covers only
# whichever did not finish (ADR 0006 §3).
POST_MERGE_STEPS = ("issue_closed", "local_synced")

TRANSITIONS: dict[str, dict[str, str]] = {
    "Monitoring": {
        EVENT_CHECKS_PENDING: "Monitoring",
        EVENT_ISSUE_CLOSED: "Monitoring",  # warn only, continue eligible SDD
        EVENT_CHECKS_PASS_CLEAR: "ChecksPassClear",
        EVENT_CHECKS_PASS_PENDING: "ChecksPassPending",
        EVENT_PR_CLOSED: "ClosedAnomaly",
        EVENT_PR_MERGED: "Merged",
    },
    "ChecksPassClear": {
        EVENT_NEW_FEEDBACK: "Monitoring",
        EVENT_CHECKS_PENDING: "Monitoring",
    },
    "ChecksPassPending": {
        EVENT_CLARIFICATION_RESOLVED: "Monitoring",
        EVENT_NEW_FEEDBACK: "Monitoring",
    },
    "ClosedAnomaly": {
        EVENT_PR_REOPENED: "Monitoring",  # history and exhausted limits preserved
    },
    "Merged": {
        EVENT_POST_MERGE_STARTED: "PostMerge",
    },
    "PostMerge": {
        EVENT_POST_MERGE_OK: "Done",
        EVENT_POST_MERGE_FAILED: "PostMergeBlocked",
    },
    "PostMergeBlocked": {
        EVENT_POST_MERGE_OK: "PostMerge",
    },
    "Done": {},
}


@dataclass
class PRLifecycle:
    """The lifecycle state of one PR, plus its post-merge progress."""

    state: str = "Monitoring"
    issue_closed: bool = False
    local_synced: bool = False

    @property
    def post_merge_complete(self) -> bool:
        return self.issue_closed and self.local_synced

    @property
    def outstanding_post_merge_steps(self) -> tuple[str, ...]:
        """Steps a retry still needs to cover."""
        return tuple(
            step
            for step, done in (
                ("issue_closed", self.issue_closed),
                ("local_synced", self.local_synced),
            )
            if not done
        )


class LifecycleError(Exception):
    """An event is not valid for the current state."""


def transition(lifecycle: PRLifecycle, event: str) -> str:
    """Apply an event and return the new state.

    Raises:
        LifecycleError: If the event is not valid in the current state.
    """
    if lifecycle.state not in PR_LIFECYCLE_STATES:
        raise LifecycleError(f"unknown state {lifecycle.state!r}")

    allowed = TRANSITIONS.get(lifecycle.state, {})
    if event not in allowed:
        raise LifecycleError(f"event {event!r} is not valid in state {lifecycle.state!r}")

    lifecycle.state = allowed[event]
    return lifecycle.state


def record_post_merge_step(lifecycle: PRLifecycle, step: str) -> None:
    """Record that one post-merge step completed."""
    if step not in POST_MERGE_STEPS:
        raise LifecycleError(f"unknown post-merge step {step!r}")
    setattr(lifecycle, step, True)
