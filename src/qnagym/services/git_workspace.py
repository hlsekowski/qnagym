"""Local git workspace service.

Mirrors docs/adr/0004-worker-task-model.md §7 and docs/workflow.md.
Drives system git in a temporary repository: creates a branch from main
using the workflow.md name shape, reports status, and fast-forward syncs.
If sync would conflict, records the conflict and stops. Does not push.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any


class GitWorkspaceError(Exception):
    """Error during git workspace operations."""


class GitWorkspaceConflict(GitWorkspaceError):
    """A fast-forward sync would conflict."""


class GitWorkspace:
    """A disposable local git workspace for one work item."""

    def __init__(self, repo_path: str | Path | None = None):
        if repo_path is None:
            self.repo_path = Path(tempfile.mkdtemp(prefix="qnagym-workspace-"))
        else:
            self.repo_path = Path(repo_path)
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    def _run(
        self,
        args: list[str],
        check: bool = True,
    ) -> subprocess.CompletedProcess[Any]:
        """Run a git command in the workspace."""
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check,
        )
        return result

    def init(self, initial_branch: str = "main") -> None:
        """Initialize a new git repo with an initial commit on the given branch."""
        self._run(["init", "--initial-branch", initial_branch])
        self._run(["config", "user.email", "qnagym@local"])
        self._run(["config", "user.name", "qnagym"])
        # Create an initial commit so the branch exists
        readme = self.repo_path / "README.md"
        readme.write_text("# qnagym workspace\n")
        self._run(["add", "README.md"])
        self._run(["commit", "-m", "initial commit"])
        self._initialized = True

    def current_branch(self) -> str:
        """Return the current branch name."""
        result = self._run(["branch", "--show-current"], check=False)
        return str(result.stdout.strip())

    def status(self) -> str:
        """Return the git status output."""
        result = self._run(["status", "--porcelain"], check=False)
        return str(result.stdout.strip())

    def create_branch(self, branch_name: str) -> None:
        """Create a new branch from the current HEAD."""
        self._run(["checkout", "-b", branch_name])

    def fast_forward_sync(self, remote_branch: str = "main") -> None:
        """Fast-forward the current branch to the remote branch.

        Raises:
            GitWorkspaceConflict: If the sync would conflict (not a
                clean fast-forward).
        """
        # Fetch from the remote (in a temp repo, the "remote" is the
        # local main branch ref)
        result = self._run(
            ["merge", "--ff-only", remote_branch],
            check=False,
        )
        if result.returncode != 0:
            raise GitWorkspaceConflict(f"Fast-forward sync to {remote_branch} would conflict")

    def is_clean(self) -> bool:
        """Return True if the working tree is clean."""
        return self.status() == ""

    def __enter__(self) -> GitWorkspace:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        pass


def create_workspace() -> GitWorkspace:
    """Create and initialize a new temporary git workspace."""
    ws = GitWorkspace()
    ws.init()
    return ws
