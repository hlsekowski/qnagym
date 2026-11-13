"""Execution state domain logic (pure business logic, no I/O).

Mirrors docs/adr/0004-worker-task-model.md §6. Implements execution state
validation and serialization helpers; performs no I/O.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from qnagym.contracts.task_model import ExecutionState


class ExecutionStateError(Exception):
    """Error during execution state domain operations."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


def serialize_state(state: ExecutionState) -> dict[str, Any]:
    """Serialize an ExecutionState to a dictionary.

    Args:
        state: The execution state to serialize.

    Returns:
        Dictionary representation of the execution state.
    """
    return state.to_dict()


def deserialize_state(data: str | dict[str, Any]) -> ExecutionState:
    """Deserialize an ExecutionState from a dictionary or JSON string.

    Args:
        data: Dictionary or JSON string representation of the execution state.

    Returns:
        The deserialized ExecutionState.

    Raises:
        ExecutionStateError: If the data is invalid or corrupt.
    """
    if isinstance(data, str):
        try:
            parsed: dict = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ExecutionStateError(f"Corrupt execution state: {exc}") from exc
    else:
        parsed = data
    try:
        return ExecutionState.from_dict(parsed)
    except (KeyError, TypeError, ValueError) as exc:
        raise ExecutionStateError(f"Corrupt execution state: {exc}") from exc


def is_corrupt(data: str | dict[str, Any]) -> bool:
    """Check if data represents a corrupt execution state.

    Args:
        data: JSON string or dictionary to check.

    Returns:
        True if the data is corrupt, False otherwise.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return True
    try:
        deserialize_state(data)
        return False
    except ExecutionStateError:
        return True


def merge_states(base: ExecutionState, overlay: ExecutionState) -> ExecutionState:
    """Merge two execution states, with overlay taking precedence.

    Args:
        base: The base execution state.
        overlay: The overlay execution state (takes precedence).

    Returns:
        A new ExecutionState with merged data.
    """
    merged = ExecutionState()
    merged.tasks = {**base.tasks, **overlay.tasks}
    merged.attempts = {**base.attempts, **overlay.attempts}
    merged.claims = {**base.claims, **overlay.claims}
    merged.observation_watermark = max(base.observation_watermark, overlay.observation_watermark)
    merged.processed_event_ids = base.processed_event_ids | overlay.processed_event_ids
    merged.generation_counter = max(base.generation_counter, overlay.generation_counter)
    merged.correction_attempts = {**base.correction_attempts, **overlay.correction_attempts}
    return merged


def validate_state(state: ExecutionState) -> list[str]:
    """Validate an execution state and return list of problems.

    Args:
        state: The execution state to validate.

    Returns:
        List of problem descriptions, empty if valid.
    """
    problems = []
    for key, task in state.tasks.items():
        if task.identity.kind != key.split("|")[0]:
            problems.append(f"Task key mismatch: {key} vs {task.identity.kind}")
        if task.identity.work_item != (task.identity.work_item or ""):
            problems.append(f"Task work_item mismatch: {key}")
    return problems
