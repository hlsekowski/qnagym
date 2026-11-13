"""SDD Process domain logic (pure business logic, no I/O).

Mirrors docs/adr/0007-sdd-process.md. Implements SDD task lifecycle,
development cycle state transitions, and result determination;
performs no GitHub I/O.
"""

from __future__ import annotations

from qnagym.contracts.sdd_process import (
    SDD_RESULT_INCOMPLETE,
    SDD_RESULT_SUCCESSFUL,
    SDD_TASK_STATE_ANALYZING,
    SDD_TASK_STATE_DELIVERING,
    SDD_TASK_STATE_IMPLEMENTING,
    SDD_TASK_STATE_SPECIFYING,
    SDD_TASK_STATE_VERIFYING,
    SDDResult,
    SDDTask,
)

# Actions the SDD process can produce.
ACTION_ANALYZE = "Analyze"
ACTION_SPECIFY = "Specify"
ACTION_UPDATE_CONTRACT = "UpdateContract"
ACTION_UPDATE_TESTS = "UpdateTests"
ACTION_IMPLEMENT = "Implement"
ACTION_UPDATE_TRACEABILITY = "UpdateTraceability"
ACTION_VERIFY = "Verify"
ACTION_COMMIT_PUSH = "CommitPush"
ACTION_DELIVER_SUCCESSFUL = "DeliverSuccessful"
ACTION_DELIVER_INCOMPLETE = "DeliverIncomplete"
ACTION_NONE = "None"


def next_development_step(task: SDDTask) -> str:
    """Return the next development cycle step for an SDD task.

    Follows the spec-first sequence from ADR 0007 §4:
    Analyze -> Specify -> UpdateContract(if data shape changes) ->
    UpdateTests -> Implement -> UpdateTraceability -> Verify ->
    CommitPush -> Deliver.
    """
    state = task.state

    if state == SDD_TASK_STATE_ANALYZING:
        return ACTION_SPECIFY
    if state == SDD_TASK_STATE_SPECIFYING:
        return ACTION_UPDATE_CONTRACT if task.input.accepted_requirements else ACTION_UPDATE_TESTS
    if state == SDD_TASK_STATE_IMPLEMENTING:
        return ACTION_UPDATE_TRACEABILITY
    if state == SDD_TASK_STATE_VERIFYING:
        return ACTION_COMMIT_PUSH
    if state == SDD_TASK_STATE_DELIVERING:
        if task.local_verification_passed and task.pr_diff_within_limit:
            return ACTION_DELIVER_SUCCESSFUL
        return ACTION_DELIVER_INCOMPLETE

    return ACTION_NONE


def is_ready_for_delivery(task: SDDTask) -> bool:
    """Check whether an SDD task is ready for delivery.

    A task is ready when implementation is done, traceability is updated,
    local verification passed, and PR diff is within the C2 limit.
    """
    return (
        task.implementation_done
        and task.traceability_updated
        and task.local_verification_passed
        and task.pr_diff_within_limit
    )


def determine_result(task: SDDTask) -> SDDResult:
    """Determine the SDD result for a task (ADR 0007 §7).

    Returns a Successful result when all cycle steps are complete and
    verification passed; otherwise an Incomplete result with evidence
    and diagnostics.
    """
    if task.is_complete and task.local_verification_passed and task.pr_diff_within_limit:
        return SDDResult(
            result=SDD_RESULT_SUCCESSFUL,
            issue_number=task.input.issue_number,
            pr_number=task.input.pr_number,
            branch_name=task.input.branch_name,
            commit_sha=task.commit_sha,
            spec_references=[],
            local_verification="passed",
            pr_diff_size=task.pr_diff_size,
            pr_diff_limit=task.pr_diff_limit,
        )

    missing = []
    if not task.spec_changed:
        missing.append("specification not updated")
    if not task.tests_updated:
        missing.append("tests not updated")
    if not task.implementation_done:
        missing.append("implementation not done")
    if not task.traceability_updated:
        missing.append("traceability not updated")
    if not task.local_verification_passed:
        missing.append("local verification not passed")
    if not task.pr_diff_within_limit:
        missing.append(f"PR diff {task.pr_diff_size} exceeds limit {task.pr_diff_limit}")

    return SDDResult(
        result=SDD_RESULT_INCOMPLETE,
        issue_number=task.input.issue_number,
        pr_number=task.input.pr_number,
        branch_name=task.input.branch_name,
        commit_sha=task.commit_sha,
        spec_references=[],
        local_verification="passed" if task.local_verification_passed else "not passed",
        pr_diff_size=task.pr_diff_size,
        pr_diff_limit=task.pr_diff_limit,
        evidence="; ".join(missing) if missing else "incomplete delivery",
        work_completed=", ".join(
            step
            for step, done in (
                ("spec", task.spec_changed),
                ("contract", task.contract_changed),
                ("tests", task.tests_updated),
                ("implementation", task.implementation_done),
                ("traceability", task.traceability_updated),
            )
            if done
        ),
        diagnostics="; ".join(missing) if missing else "verification not complete",
    )


__all__ = [
    "ACTION_ANALYZE",
    "ACTION_COMMIT_PUSH",
    "ACTION_DELIVER_INCOMPLETE",
    "ACTION_DELIVER_SUCCESSFUL",
    "ACTION_IMPLEMENT",
    "ACTION_NONE",
    "ACTION_SPECIFY",
    "ACTION_UPDATE_CONTRACT",
    "ACTION_UPDATE_TESTS",
    "ACTION_UPDATE_TRACEABILITY",
    "ACTION_VERIFY",
    "determine_result",
    "is_ready_for_delivery",
    "next_development_step",
]
