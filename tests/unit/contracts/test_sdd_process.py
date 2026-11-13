"""Unit tests for SDD Process contracts."""

from qnagym.contracts.sdd_process import (
    SDD_RESULT_INCOMPLETE,
    SDD_RESULT_SUCCESSFUL,
    SDD_TASK_STATE_ANALYZING,
    SDD_TASK_STATE_COMPLETED,
    SDD_TASK_STATE_INCOMPLETE,
    SDD_TASK_STATES,
    TERMINAL_SDD_STATES,
    SDDResult,
    SDDTask,
    SDDTaskIdentity,
    SDDTaskInput,
)


class TestSDDTaskIdentity:
    def test_identity_roundtrip(self):
        identity = SDDTaskIdentity(task_id="t1", source="issue", source_ref="42")
        assert SDDTaskIdentity.from_dict(identity.to_dict()) == identity


class TestSDDTaskInput:
    def test_input_roundtrip(self):
        input_data = SDDTaskInput(
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
            branch_name="feat/test",
            issue_number=42,
        )
        assert SDDTaskInput.from_dict(input_data.to_dict()) == input_data

    def test_input_defaults(self):
        input_data = SDDTaskInput(
            source="pr",
            source_ref="10",
            accepted_requirements="requirements",
        )
        assert input_data.branch_name is None
        assert input_data.issue_number is None
        assert input_data.pr_number is None


class TestSDDTask:
    def test_task_roundtrip(self):
        identity = SDDTaskIdentity(task_id="t1", source="issue", source_ref="42")
        input_data = SDDTaskInput(
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
        )
        task = SDDTask(
            identity=identity,
            input=input_data,
            state="Specifying",
            spec_changed=True,
            pr_diff_size=50,
        )
        assert SDDTask.from_dict(task.to_dict()) == task

    def test_is_terminal(self):
        identity = SDDTaskIdentity(task_id="t1", source="issue", source_ref="42")
        input_data = SDDTaskInput(
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
        )
        task = SDDTask(identity=identity, input=input_data)
        assert not task.is_terminal
        task.state = SDD_TASK_STATE_COMPLETED
        assert task.is_terminal
        task.state = SDD_TASK_STATE_INCOMPLETE
        assert task.is_terminal

    def test_pr_diff_within_limit(self):
        identity = SDDTaskIdentity(task_id="t1", source="issue", source_ref="42")
        input_data = SDDTaskInput(
            source="issue",
            source_ref="42",
            accepted_requirements="requirements",
        )
        task = SDDTask(identity=identity, input=input_data, pr_diff_size=300, pr_diff_limit=400)
        assert task.pr_diff_within_limit
        task.pr_diff_size = 500
        assert not task.pr_diff_within_limit


class TestSDDResult:
    def test_result_roundtrip(self):
        result = SDDResult(
            result=SDD_RESULT_SUCCESSFUL,
            issue_number=42,
            pr_number=10,
            branch_name="feat/test",
            spec_references=["spec.md#cli"],
            pr_diff_size=150,
        )
        assert SDDResult.from_dict(result.to_dict()) == result

    def test_is_successful_and_incomplete(self):
        successful = SDDResult(result=SDD_RESULT_SUCCESSFUL)
        incomplete = SDDResult(result=SDD_RESULT_INCOMPLETE)
        assert successful.is_successful
        assert not successful.is_incomplete
        assert not incomplete.is_successful
        assert incomplete.is_incomplete


class TestConstants:
    def test_task_states(self):
        assert SDD_TASK_STATE_ANALYZING in SDD_TASK_STATES
        assert SDD_TASK_STATE_COMPLETED in SDD_TASK_STATES
        assert SDD_TASK_STATE_INCOMPLETE in SDD_TASK_STATES

    def test_terminal_states(self):
        assert SDD_TASK_STATE_COMPLETED in TERMINAL_SDD_STATES
        assert SDD_TASK_STATE_INCOMPLETE in TERMINAL_SDD_STATES
        assert SDD_TASK_STATE_ANALYZING not in TERMINAL_SDD_STATES

    def test_result_types(self):
        assert SDD_RESULT_SUCCESSFUL == "Successful"
        assert SDD_RESULT_INCOMPLETE == "Incomplete"
