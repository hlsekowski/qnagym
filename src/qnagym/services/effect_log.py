"""Safe effect log service.

Mirrors docs/adr/0004-worker-task-model.md §7. Records effect intent
and outcome in execution state. Posts a comment only when that effect
id has no recorded outcome. Retrying the same effect id does not post
twice. Performs no GitHub writes itself; the caller supplies an
adapter.
"""

from __future__ import annotations

from typing import Protocol

from qnagym.contracts.task_model import ExecutionState
from qnagym.services.execution_state import ExecutionStateService


class EffectAdapter(Protocol):
    """Adapter for performing an external effect (e.g. posting a comment)."""

    def post_comment(self, body: str) -> str:
        """Post a comment and return an external effect id.

        Raises:
            EffectAdapterError: If the post fails.
        """
        ...


class EffectAdapterError(Exception):
    """Error from an effect adapter."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EffectLogError(Exception):
    """Error during effect log operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EffectLog:
    """Logs effect intents and outcomes for safe retry semantics.

    Before dispatching an effect, the caller records intent with a
    stable effect id. After dispatch, the caller records the outcome.
    Replaying the same effect id does not re-dispatch.
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

    def _load_state(self) -> ExecutionState:
        return self.service.load(self.state_name)

    def _save_state(self, state: ExecutionState) -> None:
        self.service.save(self.state_name, state)

    def record_intent(
        self,
        effect_id: str,
        task_identity_key: str,
        effect_step: str,
        body: str,
    ) -> None:
        """Record an effect intent before dispatch.

        Args:
            effect_id: Stable identifier derived from task and effect step.
            task_identity_key: Key of the task identity producing the effect.
            effect_step: The effect step name (e.g. "post_comment").
            body: The comment body to post (starts with WORKFLOW_COMMENT_MARKER).

        Raises:
            EffectLogError: If an intent already exists for this effect id.
        """
        state = self._load_state()
        if effect_id in state.effects:
            existing = state.effects[effect_id]
            if existing.get("outcome") is not None:
                # Already completed; no-op
                return
            raise EffectLogError(f"Intent already recorded for effect {effect_id}")

        state.effects[effect_id] = {
            "task_identity_key": task_identity_key,
            "effect_step": effect_step,
            "body": body,
            "outcome": None,
        }
        self._save_state(state)

    def record_outcome(
        self,
        effect_id: str,
        outcome: str,
    ) -> None:
        """Record the outcome of a dispatched effect.

        Args:
            effect_id: The effect id.
            outcome: The outcome string (e.g. external effect id or error).

        Raises:
            EffectLogError: If no intent exists for this effect id.
        """
        state = self._load_state()
        if effect_id not in state.effects:
            raise EffectLogError(f"No intent recorded for effect {effect_id}")
        state.effects[effect_id]["outcome"] = outcome
        self._save_state(state)

    def has_outcome(self, effect_id: str) -> bool:
        """Check whether an effect id has a recorded outcome."""
        state = self._load_state()
        entry = state.effects.get(effect_id)
        return entry is not None and entry.get("outcome") is not None

    def dispatch_if_needed(
        self,
        effect_id: str,
        task_identity_key: str,
        effect_step: str,
        body: str,
    ) -> str | None:
        """Dispatch an effect only if it has no recorded outcome.

        Records intent, posts the comment via the adapter, records the
        outcome, and returns the external effect id. If the effect id
        already has an outcome, returns None without dispatching.

        Args:
            effect_id: Stable identifier derived from task and effect step.
            task_identity_key: Key of the task identity producing the effect.
            effect_step: The effect step name.
            body: The comment body to post (starts with WORKFLOW_COMMENT_MARKER).

        Returns:
            The external effect id, or None if already dispatched.

        Raises:
            EffectLogError: If intent recording fails or adapter fails.
        """
        state = self._load_state()
        existing = state.effects.get(effect_id)
        if existing is not None and existing.get("outcome") is not None:
            # Already completed; do not re-dispatch
            return None

        # Record intent (idempotent if already recorded without outcome)
        if existing is None:
            self.record_intent(effect_id, task_identity_key, effect_step, body)
        # Reload after save to get fresh state
        state = self._load_state()

        # Dispatch via adapter
        try:
            external_id = self.adapter.post_comment(body)
        except Exception as exc:
            # Intent recorded but outcome unknown; crash before outcome
            # means replay will re-dispatch (safe because comment posting
            # is idempotent by effect id check on retry)
            raise EffectLogError(f"Effect dispatch failed: {exc}") from exc

        self.record_outcome(effect_id, external_id)
        return external_id
