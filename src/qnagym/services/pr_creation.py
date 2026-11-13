"""Pull request creation service (safe effect).

Mirrors docs/adr/0004-worker-task-model.md §7. Pushes a branch and
opens one PR against main using the effect log from issue #155 for
idempotency. Never calls merge (rule D7).
"""

from __future__ import annotations

from qnagym.contracts.task_model import ExecutionState
from qnagym.services.effect_log import (
    EffectAdapter,
    EffectAdapterError,
    EffectLogError,
)
from qnagym.services.execution_state import ExecutionStateService


class PRCreationError(Exception):
    """Error during PR creation."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class PRCreation:
    """Pushes a branch and opens one PR as a safe effect.

    Uses the effect log to ensure idempotency: replaying the same
    effect id does not open a second PR.
    """

    def __init__(
        self,
        service: ExecutionStateService,
        state_name: str,
        adapter: EffectAdapter,
    ):
        self.service = service
        self.state_name = state_name
        self.adapter = adapter

    def push_and_open_pr(
        self,
        effect_id: str,
        task_identity_key: str,
        branch: str,
        title: str,
        body: str,
        base: str = "main",
        closes_issue: int | None = None,
    ) -> str | None:
        """Push a branch and open one PR as a safe effect.

        Args:
            effect_id: Stable identifier derived from task and effect step.
            task_identity_key: Key of the task identity producing the effect.
            branch: The branch name to push.
            title: The PR title.
            body: The PR body.
            base: The target branch (default "main").
            closes_issue: Optional issue number to reference in the body.

        Returns:
            The PR number as a string, or None if already opened.

        Raises:
            PRCreationError: If push or PR creation fails.
        """
        state = self._load_state()
        existing = state.effects.get(effect_id)
        if existing is not None and existing.get("outcome") is not None:
            # Already completed; do not re-dispatch
            return None

        # Build the PR body with optional "Closes #<issue>"
        full_body = body
        if closes_issue is not None:
            full_body = f"{body}\n\nCloses #{closes_issue}"

        # Record intent (idempotent if already recorded without outcome)
        if existing is None:
            self._record_intent(effect_id, task_identity_key, "push_and_open_pr", full_body)

        # Push the branch
        try:
            self.adapter.push_branch(branch)
        except EffectAdapterError as exc:
            # Push failed: no outcome recorded, so a later retry can push
            raise PRCreationError(f"Push failed: {exc}") from exc

        # Create the PR
        try:
            pr_number = self.adapter.create_pull_request(title, full_body, branch, base)
        except EffectAdapterError as exc:
            # PR creation failed after push; record partial outcome
            self._record_outcome(effect_id, f"push_only:{branch}")
            raise PRCreationError(f"PR creation failed: {exc}") from exc

        # Record success
        self._record_outcome(effect_id, pr_number)
        return pr_number

    def _load_state(self) -> ExecutionState:
        return self.service.load(self.state_name)

    def _save_state(self, state: ExecutionState) -> None:
        self.service.save(self.state_name, state)

    def _record_intent(
        self,
        effect_id: str,
        task_identity_key: str,
        effect_step: str,
        body: str,
    ) -> None:
        state = self._load_state()
        if effect_id in state.effects:
            existing = state.effects[effect_id]
            if existing.get("outcome") is not None:
                return
            raise EffectLogError(f"Intent already recorded for effect {effect_id}")
        state.effects[effect_id] = {
            "task_identity_key": task_identity_key,
            "effect_step": effect_step,
            "body": body,
            "outcome": None,
        }
        self._save_state(state)

    def _record_outcome(self, effect_id: str, outcome: str) -> None:
        state = self._load_state()
        if effect_id not in state.effects:
            raise EffectLogError(f"No intent recorded for effect {effect_id}")
        state.effects[effect_id]["outcome"] = outcome
        self._save_state(state)
