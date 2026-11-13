"""Execution state service (orchestration).

Mirrors docs/adr/0004-worker-task-model.md §6. Orchestrates durable
execution state persistence with atomic writes and corruption handling;
performs no GitHub or model I/O.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path

from qnagym.contracts.task_model import ExecutionState
from qnagym.domain.execution_state import (
    ExecutionStateError,
    deserialize_state,
    serialize_state,
)


class ExecutionStateServiceError(Exception):
    """Error during execution state service operations."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        super().__init__(message)


class ExecutionStateService:
    """Service for durable execution state persistence.

    Mirrors docs/adr/0004-worker-task-model.md §6. Provides atomic
    read/write of execution state with corruption handling.
    """

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, name: str) -> Path:
        """Get the file path for an execution state name."""
        if not name or name in {".", ".."}:
            raise ExecutionStateError(f"Invalid state name: {name!r}")
        return self.data_dir / f"{name}.json"

    def save(self, name: str, state: ExecutionState) -> None:
        """Persist an execution state atomically.

        Args:
            name: The name of the state to save.
            state: The execution state to persist.

        Raises:
            ExecutionStateError: If the name is invalid or write fails.
        """
        path = self._path_for(name)
        content = json.dumps(serialize_state(state), indent=2) + "\n"
        self._write_atomic(path, content)

    def load(self, name: str) -> ExecutionState:
        """Load an execution state by name.

        Args:
            name: The name of the state to load.

        Returns:
            The deserialized ExecutionState.

        Raises:
            ExecutionStateServiceError: If the state does not exist or is corrupt.
        """
        path = self._path_for(name)
        if not path.is_file():
            raise ExecutionStateServiceError(f"No execution state: {name}")
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ExecutionStateServiceError(f"Cannot read state {name}: {exc}") from exc
        return deserialize_state(json.loads(content))

    def exists(self, name: str) -> bool:
        """Check if an execution state exists.

        Args:
            name: The name of the state to check.

        Returns:
            True if the state exists, False otherwise.
        """
        return self._path_for(name).is_file()

    def delete(self, name: str) -> None:
        """Delete an execution state.

        Args:
            name: The name of the state to delete.

        Raises:
            ExecutionStateServiceError: If the state does not exist.
        """
        path = self._path_for(name)
        if not path.is_file():
            raise ExecutionStateServiceError(f"No execution state: {name}")
        path.unlink()

    def list_all(self) -> list[str]:
        """List all execution state names.

        Returns:
            Sorted list of state names.
        """
        return sorted(p.stem for p in self.data_dir.glob("*.json"))

    def _write_atomic(self, path: Path, content: str) -> None:
        """Write content to a file atomically using temp file + rename.

        Args:
            path: The path to write to.
            content: The content to write.

        Raises:
            ExecutionStateError: If the write fails.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            os.replace(temp_name, path)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temp_name)
            raise
