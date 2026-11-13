"""Issue Process domain logic (pure business logic, no I/O).

Mirrors docs/adr/0005-issue-process.md. Implements issue evaluation,
decision gate, sealing, and reopening logic; performs no GitHub I/O.
"""

from __future__ import annotations

from qnagym.contracts.constants import CONFIDENCE_SHOW_BELOW
from qnagym.contracts.issue_process import (
    ACTION_ACCEPT_AND_SEAL,
    ACTION_EXCLUDE_REOPENED,
    ACTION_NONE,
    ACTION_POST_REOPENED_NOTICE,
    ACTION_POST_SEALED_EDIT_NOTICE,
    ACTION_REPORT_AMBIGUOUS_LINK,
    ACTION_REQUEST_CLARIFICATION,
    ACTION_WITHDRAW,
    EVALUATION_AMBIGUOUS,
    EVALUATION_FAIL,
    EVALUATION_INCONSISTENT,
    EVALUATION_PASS,
    Issue,
    IssueDecision,
    IssueEvaluation,
)


def evaluate_issue(
    description: str,
    change_type: str | None,
    confidence: float,
    clarity_pass: bool,
    consistency_pass: bool,
) -> IssueEvaluation:
    """Evaluate one issue against clarity and consistency criteria.

    Args:
        description: The issue description text.
        change_type: The identified change type, or None if unclear.
        confidence: The model's self-reported confidence (0-1).
        clarity_pass: Whether clarity criteria pass.
        consistency_pass: Whether consistency criteria pass.

    Returns:
        The evaluation result.
    """
    if not clarity_pass:
        result = EVALUATION_FAIL
        reason = (
            "clarity criteria not met: goal, acceptance criteria, change type, or scope unclear"
        )
    elif not consistency_pass:
        result = EVALUATION_INCONSISTENT
        reason = "consistency criteria not met: conflicts with constitution, rules, spec, or ADRs"
    elif confidence <= CONFIDENCE_SHOW_BELOW:
        result = EVALUATION_FAIL
        reason = (
            f"confidence {confidence} at or below decision gate threshold {CONFIDENCE_SHOW_BELOW}"
        )
    else:
        result = EVALUATION_PASS
        reason = "issue passes clarity and consistency criteria"

    return IssueEvaluation(
        result=result,
        confidence=confidence,
        reason=reason,
        clarity_pass=clarity_pass,
        consistency_pass=consistency_pass,
        change_type=change_type,
    )


def decide_issue(
    issue: Issue,
    evaluation: IssueEvaluation,
    now: float,
    debounce_hours: float = 20.0,
) -> IssueDecision:
    """Decide the action for one evaluated issue (ADR 0005 §4-§7).

    Args:
        issue: The issue being evaluated.
        evaluation: The evaluation result.
        now: Current time as Unix epoch seconds.
        debounce_hours: Hours to wait after an edit before evaluating.

    Returns:
        The decision for the issue process.
    """
    # Reopened issues are not processed (ADR 0005 §1)
    if issue.is_reopened:
        return IssueDecision(
            ACTION_EXCLUDE_REOPENED,
            "reopened issues are not processed",
            comment=(
                "This issue was reopened. Reopened issues are not processed by the Issue Process."
            ),
        )

    # Exception issues are excluded (ADR 0005 §1)
    if issue.is_exception:
        return IssueDecision(
            ACTION_NONE,
            "issue is labelled exception and excluded from intake",
        )

    # Ambiguous development links stop the workflow (ADR 0005 §4)
    if evaluation.result == EVALUATION_AMBIGUOUS:
        return IssueDecision(
            ACTION_REPORT_AMBIGUOUS_LINK,
            "ambiguous development links detected",
            comment=(
                "Ambiguous development links detected. The workflow stops until you resolve them."
            ),
        )

    # Gate not passed: request clarification (ADR 0005 §4)
    if evaluation.result != EVALUATION_PASS:
        return IssueDecision(
            ACTION_REQUEST_CLARIFICATION,
            evaluation.reason,
            comment=f"Evaluation did not pass the decision gate: {evaluation.reason}",
        )

    # Gate passed: accept and seal (ADR 0005 §4)
    branch_name = None
    if evaluation.change_type and evaluation.change_type in {
        "feat",
        "fix",
        "chore",
        "docs",
    }:
        short_desc = issue.title.lower().replace(" ", "-")[:40]
        branch_name = f"{evaluation.change_type}/{short_desc}"

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


def handle_description_edit(
    issue: Issue,
    new_description: str,
    new_hash: str,
    now: float,
    debounce_hours: float = 20.0,
) -> IssueDecision:
    """Handle a description edit to a not-yet-sealed issue.

    Each edit schedules evaluation for debounce_hours after the edit.
    Each new edit replaces the scheduled time.
    """
    if issue.is_sealed:
        return IssueDecision(
            ACTION_POST_SEALED_EDIT_NOTICE,
            "sealed description unchanged; edit will not be taken into account",
            comment=(
                "The sealed description is unchanged. This edit will not be taken into account. "
                "Scope changes go through the PR feedback path."
            ),
        )

    return IssueDecision(
        ACTION_NONE,
        f"evaluation scheduled in {debounce_hours} hours",
        scheduled_evaluation_at=now + debounce_hours * 3600,
    )


def handle_reopened_issue(issue: Issue) -> IssueDecision:
    """Handle a reopened issue (ADR 0005 §1, ADR 0003 §4)."""
    return IssueDecision(
        ACTION_POST_REOPENED_NOTICE,
        "reopened issue is an anomaly; not processed",
        comment=(
            "This issue was reopened. Reopened issues are not processed by the Issue Process. "
            "If similar work is needed, please submit a new issue."
        ),
    )


def handle_issue_closed(issue: Issue, pr_exists: bool) -> IssueDecision:
    """Handle issue closure (ADR 0005 §7).

    An issue closed before any PR exists withdraws its work item.
    Closing an issue while a PR is open does not withdraw the work item.
    """
    if pr_exists:
        return IssueDecision(
            ACTION_NONE,
            "issue closed while PR is open; PR Process handles it",
        )

    return IssueDecision(
        ACTION_WITHDRAW,
        "issue closed before any PR exists; work item withdrawn",
    )


__all__ = [
    "decide_issue",
    "evaluate_issue",
    "handle_description_edit",
    "handle_issue_closed",
    "handle_reopened_issue",
]
