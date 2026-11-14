"""Unit tests for the workflow orchestrator service."""

import tempfile

from qnagym.contracts.issue_process import (
    EVALUATION_FAIL,
    EVALUATION_PASS,
    Issue,
    IssueEvaluation,
)
from qnagym.contracts.task_model import ExecutionState
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.issue_evaluation import IssueEvaluator
from qnagym.services.workflow_orchestrator import WorkflowOrchestrator


class FakeEvaluator(IssueEvaluator):
    """Deterministic fake evaluator for tests."""

    def __init__(self, result: str = EVALUATION_PASS, reason: str = "pass"):
        self.result = result
        self.reason = reason
        self.called = 0

    def evaluate(self, issue: Issue) -> IssueEvaluation:
        self.called += 1
        return IssueEvaluation(
            result=self.result,
            confidence=0.99,
            reason=self.reason,
            clarity_pass=self.result == EVALUATION_PASS,
            consistency_pass=self.result == EVALUATION_PASS,
            change_type="feat",
        )


class FakeAdapter:
    """Fake effect adapter recording calls."""

    def __init__(self):
        self.posted: list[str] = []
        self.pushed: list[str] = []
        self.prs: list[dict] = []

    def post_comment(self, body: str) -> str:
        self.posted.append(body)
        return "comment-1"

    def push_branch(self, branch: str) -> str:
        self.pushed.append(branch)
        return branch

    def create_pull_request(self, title: str, body: str, head: str, base: str) -> str:
        self.prs.append({"title": title, "body": body, "head": head, "base": base})
        return "42"


def _service():
    return ExecutionStateService(tempfile.mkdtemp())


def _orchestrator(service=None, adapter=None, evaluator=None, state_name="wf_state"):
    if service is None:
        service = _service()
    if adapter is None:
        adapter = FakeAdapter()
    if evaluator is None:
        evaluator = FakeEvaluator()
    return WorkflowOrchestrator(
        service=service,
        state_name=state_name,
        evaluator=evaluator,
        adapter=adapter,
    )


class TestDiscoverAndEvaluate:
    def test_gate_pass_creates_task_and_evaluates(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_PASS)
        service.save("wf_state", ExecutionState())

        orch = _orchestrator(service, adapter, evaluator)
        outcome = orch.discover_and_evaluate(
            issue_number=42,
            repository="owner/repo",
            title="Add feature",
            description="A new feature",
            now=100.0,
        )

        assert "accept" in outcome.lower()
        assert evaluator.called == 1
        assert adapter.pushed == ["feat/add-feature"]
        assert len(adapter.prs) == 1
        assert "Closes #42" in adapter.prs[0]["body"]

    def test_gate_fail_creates_task_and_clarifies(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_FAIL, reason="unclear goal")
        service.save("wf_state", ExecutionState())

        orch = _orchestrator(service, adapter, evaluator)
        outcome = orch.discover_and_evaluate(
            issue_number=42,
            repository="owner/repo",
            title="Vague issue",
            description="Do something",
            now=100.0,
        )

        assert "clarify" in outcome.lower()
        assert evaluator.called == 1
        assert len(adapter.posted) == 1
        assert adapter.pushed == []
        assert adapter.prs == []

    def test_duplicate_issue_skipped(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_PASS)
        service.save("wf_state", ExecutionState())

        orch = _orchestrator(service, adapter, evaluator)
        orch.discover_and_evaluate(
            issue_number=42,
            repository="owner/repo",
            title="Add feature",
            description="A new feature",
            now=100.0,
        )
        # Second discovery of same issue should be skipped
        outcome = orch.discover_and_evaluate(
            issue_number=42,
            repository="owner/repo",
            title="Add feature",
            description="A new feature",
            now=200.0,
        )

        assert "skipped" in outcome.lower()

    def test_state_persisted_after_evaluation(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_PASS)
        service.save("wf_state", ExecutionState())

        orch = _orchestrator(service, adapter, evaluator)
        orch.discover_and_evaluate(
            issue_number=42,
            repository="owner/repo",
            title="Add feature",
            description="A new feature",
            now=100.0,
        )

        state = orch.get_state()
        assert len(state.tasks) == 1
        task = list(state.tasks.values())[0]
        assert task.state == "Completed"

    def test_get_state(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator()
        service.save("wf_state", ExecutionState())

        orch = _orchestrator(service, adapter, evaluator)
        state = orch.get_state()
        assert isinstance(state, ExecutionState)
