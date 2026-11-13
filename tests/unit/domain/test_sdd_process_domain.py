"""Unit tests for the SDD Process domain logic."""

from qnagym.contracts.sdd_process import (
    SDD_RESULT_INCOMPLETE,
    SDD_RESULT_SUCCESSFUL,
    SDDTask,
    SDDTaskIdentity,
    SDDTaskInput,
)
from qnagym.domain.sdd_process import (
    determine_result,
    is_ready_for_delivery,
    next_development_step,
)


def _identity(task_id="t1", source="issue", source_ref="42"):
    return SDDTaskIdentity(task_id=task_id, source=source, source_ref=source_ref)


def _input(
    source="issue",
    source_ref="42",
    accepted_requirements="requirements",
    branch_name="feat/test",
    issue_number=42,
    pr_number=None,
):
    return SDDTaskInput(
        source=source,
        source_ref=source_ref,
        accepted_requirements=accepted_requirements,
        branch_name=branch_name,
        issue_number=issue_number,
        pr_number=pr_number,
    )


def _task(
    identity=None,
    input_data=None,
    state="Analyzing",
    spec_changed=False,
    contract_changed=False,
    tests_updated=False,
    implementation_done=False,
    traceability_updated=False,
    local_verification_passed=False,
    pr_diff_size=0,
    pr_diff_limit=400,
    result=None,
    commit_sha=None,
):
    if identity is None:
        identity = _identity()
    if input_data is None:
        input_data = _input()
    return SDDTask(
        identity=identity,
        input=input_data,
        state=state,
        spec_changed=spec_changed,
        contract_changed=contract_changed,
        tests_updated=tests_updated,
        implementation_done=implementation_done,
        traceability_updated=traceability_updated,
        local_verification_passed=local_verification_passed,
        pr_diff_size=pr_diff_size,
        pr_diff_limit=pr_diff_limit,
        result=result,
        commit_sha=commit_sha,
    )


class TestNextDevelopmentStep:
    def test_analyzing_returns_specify(self):
        task = _task(state="Analyzing")
        assert next_development_step(task) == "Specify"

    def test_specifying_returns_update_contract(self):
        task = _task(state="Specifying")
        assert next_development_step(task) == "UpdateContract"

    def test_implementing_returns_update_traceability(self):
        task = _task(state="Implementing")
        assert next_development_step(task) == "UpdateTraceability"

    def test_verifying_returns_commit_push(self):
        task = _task(state="Verifying")
        assert next_development_step(task) == "CommitPush"

    def test_delivering_ready_returns_deliver_successful(self):
        task = _task(
            state="Delivering",
            local_verification_passed=True,
            pr_diff_size=100,
        )
        assert next_development_step(task) == "DeliverSuccessful"

    def test_delivering_not_ready_returns_deliver_incomplete(self):
        task = _task(
            state="Delivering",
            local_verification_passed=False,
            pr_diff_size=100,
        )
        assert next_development_step(task) == "DeliverIncomplete"

    def test_delivering_diff_exceeds_limit_returns_incomplete(self):
        task = _task(
            state="Delivering",
            local_verification_passed=True,
            pr_diff_size=500,
            pr_diff_limit=400,
        )
        assert next_development_step(task) == "DeliverIncomplete"


class TestIsReadyForDelivery:
    def test_all_conditions_met(self):
        task = _task(
            implementation_done=True,
            traceability_updated=True,
            local_verification_passed=True,
            pr_diff_size=100,
        )
        assert is_ready_for_delivery(task)

    def test_missing_implementation(self):
        task = _task(
            traceability_updated=True,
            local_verification_passed=True,
            pr_diff_size=100,
        )
        assert not is_ready_for_delivery(task)

    def test_missing_verification(self):
        task = _task(
            implementation_done=True,
            traceability_updated=True,
            pr_diff_size=100,
        )
        assert not is_ready_for_delivery(task)

    def test_diff_exceeds_limit(self):
        task = _task(
            implementation_done=True,
            traceability_updated=True,
            local_verification_passed=True,
            pr_diff_size=500,
            pr_diff_limit=400,
        )
        assert not is_ready_for_delivery(task)


class TestDetermineResult:
    def test_successful_result(self):
        task = _task(
            state="Completed",
            spec_changed=True,
            contract_changed=True,
            tests_updated=True,
            implementation_done=True,
            traceability_updated=True,
            local_verification_passed=True,
            pr_diff_size=100,
            commit_sha="abc123",
        )
        result = determine_result(task)
        assert result.result == SDD_RESULT_SUCCESSFUL
        assert result.is_successful
        assert not result.is_incomplete
        assert result.commit_sha == "abc123"

    def test_incomplete_missing_steps(self):
        task = _task(
            spec_changed=False,
            tests_updated=False,
            implementation_done=False,
            local_verification_passed=False,
            pr_diff_size=100,
        )
        result = determine_result(task)
        assert result.result == SDD_RESULT_INCOMPLETE
        assert result.is_incomplete
        assert not result.is_successful
        assert "specification not updated" in result.diagnostics
        assert "tests not updated" in result.diagnostics

    def test_incomplete_diff_exceeds_limit(self):
        task = _task(
            state="Completed",
            spec_changed=True,
            tests_updated=True,
            implementation_done=True,
            traceability_updated=True,
            local_verification_passed=True,
            pr_diff_size=500,
            pr_diff_limit=400,
        )
        result = determine_result(task)
        assert result.result == SDD_RESULT_INCOMPLETE
        assert "exceeds limit" in result.diagnostics
