"""Session store adapter (I/O boundary).

Mirrors docs/spec/session.md.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import uuid
from pathlib import Path, PureWindowsPath

from qnagym.contracts.types import Session, SessionStoreProtocol


def new_session_id() -> str:
    return str(uuid.uuid4())


class SessionStore(SessionStoreProtocol):
    def new_session_id(self) -> str:
        return new_session_id()

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def path_for(self, session_id: str) -> Path:
        if not session_id or session_id in {".", ".."}:
            raise ValueError("session id must be a non-empty filename component")
        windows_path = PureWindowsPath(session_id)
        if (
            "/" in session_id
            or "\\" in session_id
            or windows_path.is_absolute()
            or windows_path.drive
        ):
            raise ValueError("session id must be a single filename component")
        return self.data_dir / f"{session_id}.json"

    def save(self, session: Session) -> Path:
        session.touch()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.path_for(session.id)
        content = json.dumps(session.to_dict(), indent=2) + "\n"
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.data_dir)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            os.replace(temp_name, path)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temp_name)
            raise
        return path

    def load(self, session_id: str) -> Session:
        """Load a session by UUID or by absolute/relative JSON path.

        If ``session_id`` is an existing file path, it is loaded directly.
        Otherwise it is treated as a session UUID and resolved under
        ``self.data_dir`` as ``{session_id}.json``.
        """
        path = Path(session_id)
        if path.is_file():
            return Session.from_dict(json.loads(path.read_text(encoding="utf-8")))
        file_path = self.path_for(session_id)
        if not file_path.is_file():
            raise FileNotFoundError(f"No session {session_id} in {self.data_dir}")
        return Session.from_dict(json.loads(file_path.read_text(encoding="utf-8")))

    def list_all(self) -> list[Session]:
        """Return all sessions in the data dir, newest first."""
        files = sorted(
            self.data_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [Session.from_dict(json.loads(f.read_text(encoding="utf-8"))) for f in files]

    def delete(self, session_id: str) -> None:
        """Delete the session file for ``session_id`` (UUID or path)."""
        path = Path(session_id)
        if not path.is_file():
            path = self.path_for(session_id)
        if not path.is_file():
            raise FileNotFoundError(f"No session {session_id} in {self.data_dir}")
        path.unlink()

    def latest(self) -> Session:
        files = sorted(
            self.data_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not files:
            raise FileNotFoundError(f"No sessions in {self.data_dir}")
        return Session.from_dict(json.loads(files[0].read_text(encoding="utf-8")))
