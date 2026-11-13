"""Unit tests for the issue-evaluation task service."""

import tempfile

from qnagym.contracts.issue_process import (
    EVALUATION_FAIL,
    EVALUATION_PASS,
    Issue,
    IssueEvaluation,
)
from qnagym.contracts.task_model import (
    TASK_STATE_QUEUED,
    ExecutionState,
    Task,
    TaskIdentity,
)
from qnagym.services.effect_log import EffectAdapter, EffectAdapterError
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.issue_evaluation import (
    IssueEvaluationTask,
    IssueEvaluator,
)


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


class FakeAdapter(EffectAdapter):
    """Fake effect adapter recording calls."""

    def __init__(self):
        self.posted: list[str] = []
        self.pushed: list[str] = []
        self.prs: list[dict] = []
        self.fail_push = False
        self.fail_pr = False

    def post_comment(self, body: str) -> str:
        self.posted.append(body)
        return "comment-1"

    def push_branch(self, branch: str) -> str:
        if self.fail_push:
            raise EffectAdapterError("push failed")
        self.pushed.append(branch)
        return branch

    def create_pull_request(self, title: str, body: str, head: str, base: str) -> str:
        if self.fail_pr:
            raise EffectAdapterError("PR creation failed")
        self.prs.append({"title": title, "body": body, "head": head, "base": base})
        return "42"


def _service():
    return ExecutionStateService(tempfile.mkdtemp())


def _task(
    kind="issue_evaluation",
    work_item="158",
    target="158",
    revision="issue title",
    not_before=0.0,
):
    return Task(
        identity=TaskIdentity(
            kind=kind,
            work_item=work_item,
            target=target,
            revision=revision,
        ),
        created_time=1.0,
        not_before_time=not_before,
        event_time=None,
        state=TASK_STATE_QUEUED,
    )


def _issue_evaluation_task(service=None, adapter=None, evaluator=None, state_name="ie_state"):
    if service is None:
        service = _service()
    if adapter is None:
        adapter = FakeAdapter()
    if evaluator is None:
        evaluator = FakeEvaluator()
    return IssueEvaluationTask(
        service=service,
        state_name=state_name,
        evaluator=evaluator,
        adapter=adapter,
    )


class TestGatePass:
    def test_gate_pass_enqueues_effects(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_PASS)
        task = _task(not_before=100.0)
        service.save("ie_state", ExecutionState())

        ies = _issue_evaluation_task(service, adapter, evaluator)
        outcome = ies.run(task)

        assert "accept" in outcome.lower()
        assert adapter.pushed == ["feat/issue-title"]
        assert len(adapter.prs) == 1
        assert "Closes #158" in adapter.prs[0]["body"]
        assert adapter.prs[0]["body"].startswith("<!-- qnagym-workflow -->")

    def test_gate_pass_no_second_marker(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_PASS)
        task = _task(not_before=100.0)
        service.save("ie_state", ExecutionState())

        ies = _issue_evaluation_task(service, adapter, evaluator)
        ies.run(task)

        # Only one workflow marker in the PR body
        body = adapter.prs[0]["body"]
        assert body.count("<!-- qnagym-workflow -->") == 1


class TestGateFail:
    def test_gate_fail_enqueues_clarification_only(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_FAIL, reason="unclear goal")
        task = _task(not_before=100.0)
        service.save("ie_state", ExecutionState())

        ies = _issue_evaluation_task(service, adapter, evaluator)
        outcome = ies.run(task)

        assert "clarify" in outcome.lower()
        assert len(adapter.posted) == 1
        assert adapter.posted[0].startswith("<!-- qnagym-workflow -->")
        assert adapter.pushed == []
        assert adapter.prs == []

    def test_gate_fail_no_branch_created(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_FAIL, reason="unclear goal")
        task = _task(not_before=100.0)
        service.save("ie_state", ExecutionState())

        ies = _issue_evaluation_task(service, adapter, evaluator)
        ies.run(task)

        assert adapter.pushed == []
        assert adapter.prs == []


class TestNoModelCalls:
    def test_no_openai_call(self):
        service = _service()
        adapter = FakeAdapter()
        evaluator = FakeEvaluator(result=EVALUATION_PASS)
        task = _task(not_before=100.0)
        service.save("ie_state", ExecutionState())

        ies = _issue_evaluation_task(service, adapter, evaluator)
        ies.run(task)

        # FakeEvaluator is deterministic; no model involved
        assert evaluator.called == 1
        assert adapter.prs[0]["body"].startswith("<!-- qnagym-workflow -->")
