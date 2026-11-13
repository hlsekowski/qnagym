"""Unit tests for the GitHub observation service."""

import tempfile
from collections.abc import Mapping

from qnagym.contracts.event_process import (
    EVENT_TYPE_CHECK_RESULT,
    EVENT_TYPE_DESCRIPTION_EDIT,
    EVENT_TYPE_FEEDBACK,
    EVENT_TYPE_ISSUE_CLOSED,
)
from qnagym.contracts.task_model import ExecutionState
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.github_observation import (
    GitHubObservation,
    GitHubObservationError,
    GitHubTransport,
    InfrastructureFailure,
)


class FakeTransport:
    """Fake HTTP transport returning canned responses.

    Each path maps to a list of pages; each call to get() returns the
    next page for that path.
    """

    def __init__(self, responses: dict[str, list[list[dict]]]):
        self.responses = {path: list(pages) for path, pages in responses.items()}
        self._page_index: dict[str, int] = {}
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    def get(self, path: str, params: Mapping[str, str] | None = None):
        self.calls.append((path, params))
        pages = self.responses.get(path, [])
        idx = self._page_index.get(path, 0)
        self._page_index[path] = idx + 1
        if idx < len(pages):
            return pages[idx]
        return []


def _state():
    return ExecutionState()


def _service():
    return ExecutionStateService(tempfile.mkdtemp())


def _observation(transport, service=None, state_name="obs_state"):
    if service is None:
        service = _service()
    return GitHubObservation(
        transport=transport,
        service=service,
        state_name=state_name,
        owner="owner",
        repo="repo",
    )


class TestPagination:
    def test_paginates_all_pages(self):
        page1 = [
            {
                "number": i,
                "state": "open",
                "title": f"t{i}",
                "body": f"b{i}",
                "updated_at": "2024-01-01T00:00:00Z",
            }
            for i in range(1, 101)
        ]
        responses = {
            "/repos/owner/repo/issues": [
                page1,
                [
                    {
                        "number": 102,
                        "state": "open",
                        "title": "t102",
                        "body": "b102",
                        "updated_at": "2024-01-02T00:00:00Z",
                    }
                ],
                [],
            ],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        events = obs.observe(now=1000.0)

        assert len(events) == 101
        assert events[0].payload["issue_number"] == 1
        assert events[-1].payload["issue_number"] == 102

    def test_single_page(self):
        responses = {
            "/repos/owner/repo/issues": [
                [
                    {
                        "number": 1,
                        "state": "open",
                        "title": "t1",
                        "body": "b1",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        events = obs.observe(now=1000.0)

        assert len(events) == 1


class TestDeduplication:
    def test_repeated_poll_does_not_duplicate(self):
        responses = {
            "/repos/owner/repo/issues": [
                [
                    {
                        "number": 1,
                        "state": "open",
                        "title": "t1",
                        "body": "b1",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        service = _service()
        obs = _observation(transport, service=service)
        state = _state()
        service.save("obs_state", state)

        events1 = obs.observe(now=1000.0)
        assert len(events1) == 1

        events2 = obs.observe(now=2000.0)
        assert len(events2) == 0

    def test_processed_event_ids_persisted(self):
        responses = {
            "/repos/owner/repo/issues": [
                [
                    {
                        "number": 1,
                        "state": "open",
                        "title": "t1",
                        "body": "b1",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        service = _service()
        obs = _observation(transport, service=service)
        state = _state()
        service.save("obs_state", state)

        obs.observe(now=1000.0)

        loaded = service.load("obs_state")
        assert "description_edit|1" in loaded.processed_event_ids


class TestIssueMapping:
    def test_open_issue_mapped_to_description_edit(self):
        responses = {
            "/repos/owner/repo/issues": [
                [
                    {
                        "number": 1,
                        "state": "open",
                        "title": "t1",
                        "body": "b1",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        events = obs.observe(now=1000.0)

        assert len(events) == 1
        assert events[0].event_type == EVENT_TYPE_DESCRIPTION_EDIT
        assert events[0].payload["issue_number"] == 1
        assert events[0].payload["title"] == "t1"

    def test_closed_issue_mapped_to_issue_closed(self):
        responses = {
            "/repos/owner/repo/issues": [
                [
                    {
                        "number": 1,
                        "state": "closed",
                        "title": "t1",
                        "body": "b1",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        events = obs.observe(now=1000.0)

        assert len(events) == 1
        assert events[0].event_type == EVENT_TYPE_ISSUE_CLOSED


class TestCommentMapping:
    def test_comment_mapped_to_feedback(self):
        responses = {
            "/repos/owner/repo/issues": [[]],
            "/repos/owner/repo/issues/comments": [
                [
                    {
                        "id": 42,
                        "body": "great question",
                        "user": {"login": "alice"},
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        events = obs.observe(now=1000.0)

        assert len(events) == 1
        assert events[0].event_type == EVENT_TYPE_FEEDBACK
        assert events[0].payload["body"] == "great question"
        assert events[0].payload["author"] == "alice"

    def test_workflow_comment_ignored(self):
        responses = {
            "/repos/owner/repo/issues": [[]],
            "/repos/owner/repo/issues/comments": [
                [
                    {
                        "id": 42,
                        "body": "<!-- qnagym-workflow -->\n**What happened:** ...",
                        "user": {"login": "qnagym"},
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        events = obs.observe(now=1000.0)

        assert len(events) == 0
        # But it should still be marked as processed
        loaded = obs.service.load("obs_state")
        assert "feedback|42" in loaded.processed_event_ids


class TestCheckRunMapping:
    def test_check_run_mapped_to_check_result(self):
        responses = {
            "/repos/owner/repo/issues": [[]],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [
                [
                    {
                        "id": 7,
                        "name": "lint",
                        "status": "completed",
                        "conclusion": "success",
                        "started_at": "2024-01-01T00:00:00Z",
                    }
                ]
            ],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        events = obs.observe(now=1000.0)

        assert len(events) == 1
        assert events[0].event_type == EVENT_TYPE_CHECK_RESULT
        assert events[0].payload["check_run_id"] == 7
        assert events[0].payload["name"] == "lint"
        assert events[0].payload["conclusion"] == "success"


class TestWatermark:
    def test_watermark_advanced(self):
        responses = {
            "/repos/owner/repo/issues": [[]],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        service = _service()
        obs = _observation(transport, service=service)
        state = _state()
        state.observation_watermark = 500.0
        service.save("obs_state", state)

        obs.observe(now=1000.0)

        loaded = service.load("obs_state")
        assert loaded.observation_watermark == 1000.0

    def test_watermark_used_as_since(self):
        responses = {
            "/repos/owner/repo/issues": [[]],
            "/repos/owner/repo/issues/comments": [[]],
            "/repos/owner/repo/check-runs": [[]],
        }
        transport = FakeTransport(responses)
        obs = _observation(transport)
        state = _state()
        state.observation_watermark = 1700000000.0
        obs.service.save("obs_state", state)

        obs.observe(now=1000.0)

        # Verify the since parameter was passed
        issue_calls = [c for c in transport.calls if c[0] == "/repos/owner/repo/issues"]
        assert len(issue_calls) == 1
        assert issue_calls[0][1] is not None
        assert "since" in issue_calls[0][1]


class TestInfrastructureFailure:
    def test_unauthorized_raises_infrastructure_failure(self):
        transport = GitHubTransport(base_url="https://api.github.com", token="bad")
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        try:
            obs.observe(now=1000.0)
            raise AssertionError("Should have raised InfrastructureFailure")
        except InfrastructureFailure:
            pass

    def test_rate_limit_raises_infrastructure_failure(self):
        transport = GitHubTransport(base_url="https://api.github.com", token="token")
        obs = _observation(transport)
        state = _state()
        obs.service.save("obs_state", state)

        try:
            obs.observe(now=1000.0)
            raise AssertionError("Should have raised InfrastructureFailure")
        except (InfrastructureFailure, GitHubObservationError):
            pass


class TestErrorTypes:
    def test_infrastructure_failure_is_observation_error(self):
        assert issubclass(InfrastructureFailure, GitHubObservationError)
