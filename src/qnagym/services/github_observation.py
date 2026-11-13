"""GitHub observation service (read-only).

Mirrors docs/adr/0004-worker-task-model.md §5. Reads GitHub issues,
issue comments, and check runs via stdlib urllib, advances the
observation watermark in execution state, and maps results into
event_process types. Performs no GitHub writes.
"""

from __future__ import annotations

import calendar
import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any

from qnagym.contracts.constants import WORKFLOW_COMMENT_MARKER
from qnagym.contracts.event_process import (
    EVENT_TYPE_CHECK_RESULT,
    EVENT_TYPE_DESCRIPTION_EDIT,
    EVENT_TYPE_FEEDBACK,
    EVENT_TYPE_ISSUE_CLOSED,
    EventIdentity,
    ProcessedEvent,
)
from qnagym.contracts.task_model import ExecutionState
from qnagym.services.execution_state import ExecutionStateService

logger = logging.getLogger(__name__)


class GitHubObservationError(Exception):
    """Base error for GitHub observation."""


class InfrastructureFailure(GitHubObservationError):
    """GitHub returned an infrastructure failure (401, 403, 429, 5xx)."""


class GitHubTransport:
    """HTTP transport for GitHub API requests using stdlib urllib."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def get(self, path: str, params: Mapping[str, str] | None = None) -> Any:
        """GET a path and return parsed JSON."""
        url = f"{self.base_url}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        req = urllib.request.Request(url)
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 429) or 500 <= exc.code < 600:
                raise InfrastructureFailure(f"GitHub API error {exc.code}") from exc
            raise GitHubObservationError(f"GitHub API error {exc.code}") from exc


def _format_time(epoch: float) -> str:
    """Format a Unix epoch timestamp as ISO 8601 for the GitHub API."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def _parse_time(iso_str: str | None) -> float:
    """Parse an ISO 8601 timestamp to Unix epoch seconds."""
    if not iso_str:
        return 0.0
    try:
        return float(calendar.timegm(time.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")))
    except ValueError:
        return 0.0


class GitHubObservation:
    """Read-only GitHub observation into the event model.

    Lists issues, issue comments, and check runs since the observation
    watermark, maps them to ProcessedEvent objects, and advances the
    watermark in execution state.
    """

    def __init__(
        self,
        transport: GitHubTransport,
        service: ExecutionStateService,
        state_name: str,
        owner: str,
        repo: str,
    ):
        self.transport = transport
        self.service = service
        self.state_name = state_name
        self.owner = owner
        self.repo = repo

    def _load_state(self) -> ExecutionState:
        return self.service.load(self.state_name)

    def _save_state(self, state: ExecutionState) -> None:
        self.service.save(self.state_name, state)

    def _event_key(self, event_type: str, source_id: str) -> str:
        """Composite key for processed_event_ids deduplication."""
        return f"{event_type}|{source_id}"

    def _is_processed(self, state: ExecutionState, event_type: str, source_id: str) -> bool:
        return self._event_key(event_type, source_id) in state.processed_event_ids

    def _mark_processed(self, state: ExecutionState, event_type: str, source_id: str) -> None:
        state.processed_event_ids.add(self._event_key(event_type, source_id))

    def _paginate(self, path: str, params: dict[str, str] | None = None) -> list[Any]:
        """Fetch all pages of a GitHub API list endpoint."""
        results: list[Any] = []
        params = dict(params or {})
        params.setdefault("per_page", "100")
        page = 1
        while True:
            params["page"] = str(page)
            data = self.transport.get(path, params)
            if not data:
                break
            results.extend(data)
            if len(data) < int(params["per_page"]):
                break
            page += 1
        return results

    def _map_issue(self, issue: dict[str, Any], state: ExecutionState) -> ProcessedEvent | None:
        """Map a GitHub issue to a ProcessedEvent, or None if already processed."""
        source_id = str(issue["number"])
        issue_state = issue.get("state", "open")
        event_type = (
            EVENT_TYPE_ISSUE_CLOSED if issue_state == "closed" else EVENT_TYPE_DESCRIPTION_EDIT
        )

        if self._is_processed(state, event_type, source_id):
            return None

        self._mark_processed(state, event_type, source_id)
        return ProcessedEvent(
            identity=EventIdentity(
                event_type=event_type,
                source_id=source_id,
                source="github",
            ),
            event_type=event_type,
            payload={
                "issue_number": issue["number"],
                "title": issue.get("title", ""),
                "body": issue.get("body", ""),
                "state": issue_state,
            },
            created_at=_parse_time(issue.get("updated_at")),
        )

    def _map_comment(self, comment: dict[str, Any], state: ExecutionState) -> ProcessedEvent | None:
        """Map a GitHub issue comment to a ProcessedEvent, or None if skipped."""
        source_id = str(comment["id"])
        event_type = EVENT_TYPE_FEEDBACK

        if self._is_processed(state, event_type, source_id):
            return None

        body = comment.get("body", "")
        if body.startswith(WORKFLOW_COMMENT_MARKER):
            # Workflow-authored comments are data, not instructions (D8).
            self._mark_processed(state, event_type, source_id)
            return None

        self._mark_processed(state, event_type, source_id)
        return ProcessedEvent(
            identity=EventIdentity(
                event_type=event_type,
                source_id=source_id,
                source="github",
            ),
            event_type=event_type,
            payload={
                "comment_id": comment["id"],
                "body": body,
                "author": comment.get("user", {}).get("login", ""),
            },
            created_at=_parse_time(comment.get("updated_at")),
        )

    def _map_check_run(
        self, check_run: dict[str, Any], state: ExecutionState
    ) -> ProcessedEvent | None:
        """Map a GitHub check run to a ProcessedEvent, or None if already processed."""
        source_id = str(check_run["id"])
        event_type = EVENT_TYPE_CHECK_RESULT

        if self._is_processed(state, event_type, source_id):
            return None

        self._mark_processed(state, event_type, source_id)
        return ProcessedEvent(
            identity=EventIdentity(
                event_type=event_type,
                source_id=source_id,
                source="github",
            ),
            event_type=event_type,
            payload={
                "check_run_id": check_run["id"],
                "name": check_run.get("name", ""),
                "status": check_run.get("status", ""),
                "conclusion": check_run.get("conclusion"),
            },
            created_at=_parse_time(check_run.get("started_at")),
        )

    def observe(self, now: float) -> list[ProcessedEvent]:
        """Run one observation cycle.

        Args:
            now: Current time as Unix epoch seconds.

        Returns:
            List of newly processed events.

        Raises:
            InfrastructureFailure: On unauthorized, rate-limit, or server errors.
        """
        state = self._load_state()
        watermark = state.observation_watermark
        since = _format_time(watermark) if watermark > 0 else None
        events: list[ProcessedEvent] = []

        # List issues since watermark
        issue_params: dict[str, str] = {"state": "all"}
        if since:
            issue_params["since"] = since
        for issue in self._paginate(f"/repos/{self.owner}/{self.repo}/issues", issue_params):
            event = self._map_issue(issue, state)
            if event is not None:
                events.append(event)

        # List issue comments since watermark
        comment_params: dict[str, str] = {}
        if since:
            comment_params["since"] = since
        for comment in self._paginate(
            f"/repos/{self.owner}/{self.repo}/issues/comments", comment_params
        ):
            event = self._map_comment(comment, state)
            if event is not None:
                events.append(event)

        # List check runs (no since parameter; rely on processed_event_ids dedup)
        for check_run in self._paginate(f"/repos/{self.owner}/{self.repo}/check-runs"):
            event = self._map_check_run(check_run, state)
            if event is not None:
                events.append(event)

        # Advance watermark and save atomically
        state.observation_watermark = now
        self._save_state(state)

        return events
