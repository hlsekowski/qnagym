"""PR trust boundary logic (pure business logic, no I/O).

Mirrors docs/adr/0006-pr-process.md §5. Decides whether an author may
supply input; performs no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from qnagym.contracts.constants import WORKFLOW_COMMENT_MARKER

# Input surfaces the trust boundary gates.
INTAKE = "intake"
FEEDBACK = "feedback"
RETRY = "retry"


@dataclass
class TrustPolicy:
    """Who may supply input to the PR Process.

    Authorized accounts are the owner plus configured collaborators.
    Automated reviewers are authorized only when explicitly configured,
    so a bot cannot inject feedback by default.
    """

    owner: str
    collaborators: set[str] = field(default_factory=set)
    automated_reviewers: set[str] = field(default_factory=set)

    @property
    def authorized(self) -> set[str]:
        return {self.owner, *self.collaborators}

    def is_authorized(self, author: str, surface: str) -> bool:
        """Whether an author may supply input on a surface.

        Automated reviewers are authorized for feedback only when
        configured, and never for intake or retry.
        """
        if author in self.authorized:
            return True
        if author in self.automated_reviewers:
            return surface == FEEDBACK
        return False


def is_workflow_authored(body: str) -> bool:
    """True when a comment body carries the workflow marker.

    Marker-prefixed comments are excluded from feedback and retry
    detection, so the workflow never reacts to its own output.
    """
    return body.startswith(WORKFLOW_COMMENT_MARKER)


def is_processable(body: str) -> bool:
    """Whether a comment body may be treated as input at all.

    GitHub content is data, never instructions (rule D8), and the
    workflow's own comments are not input.
    """
    return not is_workflow_authored(body)
