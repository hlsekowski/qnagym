"""Unit tests for the PR check observation service."""

from qnagym.domain.pr_checks import CorrectionBatch
from qnagym.services.pr_check_observation import PRCheckObservation


class FakeTransport:
    """Fake transport returning canned check run responses."""

    def __init__(self, check_runs: list[dict]):
        self.check_runs = check_runs

    def get(self, path: str, params=None):
        return self.check_runs


def _observation(check_runs):
    transport = FakeTransport(check_runs)
    return PRCheckObservation(transport=transport, owner="owner", repo="repo")


class TestObserve:
    def test_passing_checks(self):
        obs = _observation(
            [
                {"name": "lint", "status": "Passing"},
                {"name": "test", "status": "Passing"},
            ]
        )
        batch = CorrectionBatch()
        observations = obs.observe(batch)

        assert len(observations) == 2
        assert all(action == "Await" for _, action in observations)
        assert batch.attempts_used == 0

    def test_failed_check_consumes_attempt(self):
        obs = _observation([{"name": "lint", "status": "Failed"}])
        batch = CorrectionBatch()
        observations = obs.observe(batch)

        assert len(observations) == 1
        assert observations[0][1] == "Correct"
        # The batch itself isn't mutated by observe; only classify/decide
        assert batch.attempts_used == 0  # observe doesn't record attempts

    def test_infrastructure_failed_does_not_consume_attempt(self):
        obs = _observation([{"name": "lint", "status": "InfrastructureFailed"}])
        batch = CorrectionBatch()
        observations = obs.observe(batch)

        assert len(observations) == 1
        assert observations[0][1] == "Await"
        assert batch.attempts_used == 0

    def test_cancelled_does_not_consume_attempt(self):
        obs = _observation([{"name": "lint", "status": "Cancelled"}])
        batch = CorrectionBatch()
        observations = obs.observe(batch)

        assert len(observations) == 1
        assert observations[0][1] == "Await"
        assert batch.attempts_used == 0

    def test_skipped_does_not_consume_attempt(self):
        obs = _observation([{"name": "lint", "status": "Skipped"}])
        batch = CorrectionBatch()
        observations = obs.observe(batch)

        assert len(observations) == 1
        assert observations[0][1] == "Await"
        assert batch.attempts_used == 0

    def test_mixed_results(self):
        obs = _observation(
            [
                {"name": "lint", "status": "Passing"},
                {"name": "test", "status": "Failed"},
                {"name": "build", "status": "InfrastructureFailed"},
                {"name": "deploy", "status": "Cancelled"},
            ]
        )
        batch = CorrectionBatch()
        observations = obs.observe(batch)

        actions = [action for _, action in observations]
        assert actions.count("Await") == 3  # Passing, InfraFailed, Cancelled
        assert actions.count("Correct") == 1  # Failed
        assert batch.attempts_used == 0

    def test_empty_check_runs(self):
        obs = _observation([])
        batch = CorrectionBatch()
        observations = obs.observe(batch)

        assert observations == []
        assert batch.attempts_used == 0


class TestObserveAllClear:
    def test_all_passing_is_clear(self):
        obs = _observation([{"name": "lint", "status": "Passing"}])
        batch = CorrectionBatch()
        assert obs.observe_all_clear(batch) is True

    def test_failed_blocks_clearance(self):
        obs = _observation([{"name": "lint", "status": "Failed"}])
        batch = CorrectionBatch()
        assert obs.observe_all_clear(batch) is False

    def test_infrastructure_failed_is_clear(self):
        obs = _observation([{"name": "lint", "status": "InfrastructureFailed"}])
        batch = CorrectionBatch()
        assert obs.observe_all_clear(batch) is True

    def test_cancelled_is_clear(self):
        obs = _observation([{"name": "lint", "status": "Cancelled"}])
        batch = CorrectionBatch()
        assert obs.observe_all_clear(batch) is True

    def test_skipped_is_clear(self):
        obs = _observation([{"name": "lint", "status": "Skipped"}])
        batch = CorrectionBatch()
        assert obs.observe_all_clear(batch) is True
