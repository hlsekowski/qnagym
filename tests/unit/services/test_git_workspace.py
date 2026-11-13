"""Unit tests for the local git workspace service."""

from qnagym.services.git_workspace import (
    GitWorkspace,
    GitWorkspaceConflict,
    create_workspace,
)


def _make_commit(ws: GitWorkspace, file_name: str, content: str, message: str) -> None:
    path = ws.repo_path / file_name
    path.write_text(content)
    ws._run(["add", file_name])
    ws._run(["commit", "-m", message])


class TestInit:
    def test_init_creates_main_branch(self):
        ws = GitWorkspace()
        ws.init()
        assert ws.current_branch() == "main"
        assert ws.is_clean()

    def test_init_creates_initial_commit(self):
        ws = GitWorkspace()
        ws.init()
        result = ws._run(["log", "--oneline"], check=False)
        assert "initial commit" in result.stdout


class TestCreateBranch:
    def test_create_branch_from_main(self):
        ws = GitWorkspace()
        ws.init()
        ws.create_branch("feat/test-branch")
        assert ws.current_branch() == "feat/test-branch"

    def test_branch_name_follows_convention(self):
        ws = GitWorkspace()
        ws.init()
        ws.create_branch("fix/some-description")
        assert ws.current_branch().startswith("fix/")

    def test_feat_branch_name_shape(self):
        ws = GitWorkspace()
        ws.init()
        ws.create_branch("feat/local-git-workspace")
        assert ws.current_branch() == "feat/local-git-workspace"


class TestFastForwardSync:
    def test_clean_fast_forward(self):
        ws = GitWorkspace()
        ws.init()
        ws.create_branch("feat/test-branch")
        # No new commits on main, so fast-forward is a no-op (clean)
        ws.fast_forward_sync("main")
        assert ws.current_branch() == "feat/test-branch"

    def test_fast_forward_with_new_main_commit(self):
        ws = GitWorkspace()
        ws.init()
        ws.create_branch("feat/test-branch")
        # Switch back to main and make a commit
        ws._run(["checkout", "main"])
        _make_commit(ws, "file.txt", "content", "add file on main")
        # Switch to feature branch and fast-forward
        ws._run(["checkout", "feat/test-branch"])
        ws.fast_forward_sync("main")
        # The feature branch should now include the main commit
        result = ws._run(["log", "--oneline"], check=False)
        assert "add file on main" in result.stdout

    def test_conflict_detected(self):
        ws = GitWorkspace()
        ws.init()
        ws.create_branch("feat/test-branch")
        # Make a commit on the feature branch
        _make_commit(ws, "feature.txt", "feature content", "feature commit")
        # Switch to main and make a conflicting commit
        ws._run(["checkout", "main"])
        _make_commit(ws, "feature.txt", "main content", "main commit")
        # Switch to feature branch and try fast-forward - should conflict
        ws._run(["checkout", "feat/test-branch"])
        try:
            ws.fast_forward_sync("main")
            raise AssertionError("Should have raised GitWorkspaceConflict")
        except GitWorkspaceConflict:
            pass


class TestStatus:
    def test_status_clean_after_init(self):
        ws = GitWorkspace()
        ws.init()
        assert ws.is_clean()

    def test_status_dirty_after_change(self):
        ws = GitWorkspace()
        ws.init()
        (ws.repo_path / "new_file.txt").write_text("hello")
        assert not ws.is_clean()


class TestCreateWorkspace:
    def test_create_workspace(self):
        ws = create_workspace()
        assert isinstance(ws, GitWorkspace)
        assert ws.current_branch() == "main"
        assert ws.is_clean()
