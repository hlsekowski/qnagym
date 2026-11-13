"""PR check observation service.

Mirrors docs/adr/0006-pr-process.md §2 and docs/workflow.md step 8.
Reads check runs through the GitHubTransport adapter from issue #154
and updates the existing pr_checks CorrectionBatch state. Cancelled,
skipped, and infrastructure-failed checks do not consume
MAX_CORRECTION_ATTEMPTS_PER_BATCH. Does not push a fix.
"""

from __future__ import annotations

from qnagym.contracts.pr_process import CheckResult
from qnagym.domain.pr_checks import (
    CorrectionBatch,
    decide_check_action,
)
from qnagym.services.github_observation import GitHubTransport


class PRCheckObservationError(Exception):
    """Error during PR check observation."""


class PRCheckObservation:
    """Observes PR check runs and updates the correction-attempt batch.

    Reads check runs via GitHubTransport, classifies each result, and
    updates the CorrectionBatch. Cancelled, skipped, and
    infrastructure-failed checks are non-failures and do not consume
    correction attempts.
    """

    def __init__(
        self,
        transport: GitHubTransport,
        owner: str,
        repo: str,
    ):
        self.transport = transport
        self.owner = owner
        self.repo = repo

    def _fetch_check_runs(self) -> list[CheckResult]:
        """Fetch check runs from GitHub via the transport adapter."""
        data = self.transport.get(f"/repos/{self.owner}/{self.repo}/check-runs")
        if not data:
            return []
        results: list[CheckResult] = []
        for item in data:
            results.append(
                CheckResult(
                    name=str(item.get("name", "")),
                    status=str(item.get("status", "")),
                )
            )
        return results

    def observe(self, batch: CorrectionBatch) -> list[tuple[CheckResult, str]]:
        """Run one observation cycle.

        Args:
            batch: The current correction-attempt batch.

        Returns:
            List of (check_result, action) pairs for each observed check.

        Raises:
            PRCheckObservationError: If the fetch fails.
        """
        try:
            check_runs = self._fetch_check_runs()
        except Exception as exc:
            raise PRCheckObservationError(f"Failed to fetch check runs: {exc}") from exc

        observations: list[tuple[CheckResult, str]] = []
        for result in check_runs:
            decision = decide_check_action(result, batch)
            observations.append((result, decision.action))
        return observations

    def observe_all_clear(self, batch: CorrectionBatch) -> bool:
        """Check whether all observed checks are clear (no failures).

        Args:
            batch: The current correction-attempt batch.

        Returns:
            True when no check is failing.
        """
        check_runs = self._fetch_check_runs()
        from qnagym.services.pr_checks import all_checks_clear

        return all_checks_clear(check_runs)
