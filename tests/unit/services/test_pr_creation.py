"""Unit tests for the PR creation service."""

import tempfile

from qnagym.contracts.task_model import ExecutionState
from qnagym.services.effect_log import EffectAdapterError
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.pr_creation import PRCreation, PRCreationError


class FakeAdapter:
    """Fake effect adapter recording calls."""

    def __init__(self):
        self.pushed: list[str] = []
        self.prs: list[dict] = []
        self.fail_push = False
        self.fail_pr = False

    def post_comment(self, body: str) -> str:
        raise NotImplementedError("not used by PR creation")

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


def _pr_creation(service=None, adapter=None, state_name="pr_state"):
    if service is None:
        service = _service()
    if adapter is None:
        adapter = FakeAdapter()
    return PRCreation(service=service, state_name=state_name, adapter=adapter)


class TestPushAndOpenPR:
    def test_successful_push_and_pr(self):
        service = _service()
        adapter = FakeAdapter()
        pr = _pr_creation(service, adapter)
        state = ExecutionState()
        service.save("pr_state", state)

        result = pr.push_and_open_pr(
            effect_id="eff-1",
            task_identity_key="task-1",
            branch="feat/test",
            title="Test PR",
            body="PR body",
            closes_issue=157,
        )

        assert result == "42"
        assert adapter.pushed == ["feat/test"]
        assert len(adapter.prs) == 1
        assert adapter.prs[0]["title"] == "Test PR"
        assert "Closes #157" in adapter.prs[0]["body"]

    def test_no_closes_issue_when_not_supplied(self):
        service = _service()
        adapter = FakeAdapter()
        pr = _pr_creation(service, adapter)
        state = ExecutionState()
        service.save("pr_state", state)

        pr.push_and_open_pr(
            effect_id="eff-1",
            task_identity_key="task-1",
            branch="feat/test",
            title="Test PR",
            body="PR body",
        )

        assert "Closes #" not in adapter.prs[0]["body"]

    def test_replay_does_not_open_second_pr(self):
        service = _service()
        adapter = FakeAdapter()
        pr = _pr_creation(service, adapter)
        state = ExecutionState()
        service.save("pr_state", state)

        pr.push_and_open_pr(
            effect_id="eff-1",
            task_identity_key="task-1",
            branch="feat/test",
            title="Test PR",
            body="PR body",
        )
        result = pr.push_and_open_pr(
            effect_id="eff-1",
            task_identity_key="task-1",
            branch="feat/test",
            title="Test PR",
            body="PR body",
        )

        assert result is None
        assert len(adapter.pushed) == 1
        assert len(adapter.prs) == 1

    def test_failed_push_leaves_no_outcome(self):
        service = _service()
        adapter = FakeAdapter()
        adapter.fail_push = True
        pr = _pr_creation(service, adapter)
        state = ExecutionState()
        service.save("pr_state", state)

        try:
            pr.push_and_open_pr(
                effect_id="eff-1",
                task_identity_key="task-1",
                branch="feat/test",
                title="Test PR",
                body="PR body",
            )
            raise AssertionError("Should have raised PRCreationError")
        except PRCreationError:
            pass

        # No outcome recorded
        loaded = service.load("pr_state")
        assert loaded.effects["eff-1"]["outcome"] is None

        # A later retry can push
        adapter.fail_push = False
        result = pr.push_and_open_pr(
            effect_id="eff-1",
            task_identity_key="task-1",
            branch="feat/test",
            title="Test PR",
            body="PR body",
        )
        assert result == "42"
        assert len(adapter.pushed) == 1

    def test_failed_pr_creation_records_partial_outcome(self):
        service = _service()
        adapter = FakeAdapter()
        adapter.fail_pr = True
        pr = _pr_creation(service, adapter)
        state = ExecutionState()
        service.save("pr_state", state)

        try:
            pr.push_and_open_pr(
                effect_id="eff-1",
                task_identity_key="task-1",
                branch="feat/test",
                title="Test PR",
                body="PR body",
            )
            raise AssertionError("Should have raised PRCreationError")
        except PRCreationError:
            pass

        # Partial outcome recorded (push only)
        loaded = service.load("pr_state")
        assert loaded.effects["eff-1"]["outcome"] == "push_only:feat/test"


class TestPRCreationError:
    def test_error_has_message(self):
        err = PRCreationError("something went wrong")
        assert err.message == "something went wrong"
        assert str(err) == "something went wrong"
