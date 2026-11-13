"""Issue Process service (orchestration).

Mirrors docs/adr/0005-issue-process.md. Orchestrates issue intake,
evaluation, sealing, and handoff to SDD; performs no GitHub I/O.
"""

from __future__ import annotations

from qnagym.contracts.issue_process import (
    ACTION_ACCEPT_AND_SEAL,
    Issue,
    IssueDecision,
    IssueEvaluation,
    IssueIdentity,
)
from qnagym.domain.issue_process import (
    decide_issue,
    evaluate_issue,
)


class IssueProcessError(Exception):
    """Error during Issue Process orchestration."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


def evaluate_and_decide(
    issue: Issue,
    description: str,
    change_type: str | None,
    confidence: float,
    clarity_pass: bool,
    consistency_pass: bool,
    now: float,
) -> IssueDecision:
    """Evaluate an issue and decide the action.

    Args:
        issue: The issue being evaluated.
        description: The issue description text.
        change_type: The identified change type, or None.
        confidence: The model's self-reported confidence (0-1).
        clarity_pass: Whether clarity criteria pass.
        consistency_pass: Whether consistency criteria pass.
        now: Current time as Unix epoch seconds.

    Returns:
        The decision for the issue process.
    """
    evaluation = evaluate_issue(
        description=description,
        change_type=change_type,
        confidence=confidence,
        clarity_pass=clarity_pass,
        consistency_pass=consistency_pass,
    )

    issue.evaluation_count += 1
    issue.last_evaluation_result = evaluation.result
    issue.last_evaluation_reason = evaluation.reason

    return decide_issue(issue, evaluation, now)


def create_issue(
    number: int,
    repository: str,
    title: str,
    description: str,
    is_exception: bool = False,
    is_reopened: bool = False,
) -> Issue:
    """Create a new issue in Pending state.

    Args:
        number: The issue number.
        repository: The repository name.
        title: The issue title.
        description: The issue description.
        is_exception: Whether the issue is labelled exception.
        is_reopened: Whether the issue was reopened.

    Returns:
        The new issue.
    """
    import hashlib

    description_hash = hashlib.sha256(description.encode("utf-8")).hexdigest()

    return Issue(
        identity=IssueIdentity(number=number, repository=repository),
        title=title,
        description=description,
        description_hash=description_hash,
        is_exception=is_exception,
        is_reopened=is_reopened,
    )


def accept_and_seal(
    issue: Issue,
    evaluation: IssueEvaluation,
    branch_name: str | None = None,
) -> IssueDecision:
    """Accept and seal an issue (ADR 0005 §4).

    Records the accepted description as the requirements baseline,
    creates and links the development branch, and hands off to SDD.
    """
    return IssueDecision(
        ACTION_ACCEPT_AND_SEAL,
        "issue accepted and sealed",
        seal=True,
        create_branch=True,
        branch_name=branch_name,
        comment=(
            "Issue accepted and sealed. The accepted description is the requirements baseline. "
            "Later description edits do not change the sealed baseline; scope changes go through "
            "the PR feedback path."
        ),
    )


__all__ = [
    "IssueProcessError",
    "accept_and_seal",
    "create_issue",
    "evaluate_and_decide",
]
