"""Unit tests for the documentation structure checker."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"

_spec = importlib.util.spec_from_file_location(
    "check_doc_structure", SCRIPTS_DIR / "check_doc_structure.py"
)
assert _spec is not None and _spec.loader is not None
check_doc_structure = importlib.util.module_from_spec(_spec)
sys.modules["check_doc_structure"] = check_doc_structure
_spec.loader.exec_module(check_doc_structure)

HEADER = "> **Purpose:** What it is.\n> **Read when:** A concrete trigger.\n> **Owns:** A fact.\n"


@pytest.fixture
def repo(tmp_path: Path):
    """A minimal repo root with AGENTS.md and one headed document."""

    def _build(agents: str = "# Agent instructions\n\n" + HEADER, doc: str = HEADER) -> Path:
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        (tmp_path / "AGENTS.md").write_text(agents)
        (tmp_path / "docs" / "target.md").write_text(doc)
        return tmp_path

    return _build


class TestAgentsBudget:
    def test_within_budget_passes(self, repo, monkeypatch):
        root = repo()
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        assert check_doc_structure.check_agents_budget() == []

    def test_over_budget_fails(self, repo, monkeypatch):
        root = repo(agents="# Agent instructions\n" + "line\n" * 60)
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_agents_budget()
        assert len(errors) == 1
        assert "exceeds the budget" in errors[0]


class TestHeaders:
    def test_complete_header_passes(self, repo, monkeypatch):
        root = repo()
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        files = [Path("docs/target.md")]
        assert check_doc_structure.check_headers(files) == []

    def test_missing_field_fails(self, repo, monkeypatch):
        root = repo(doc="> **Purpose:** What it is.\n> **Read when:** A trigger.\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_headers([Path("docs/target.md")])
        assert len(errors) == 1
        assert "Owns" in errors[0]

    def test_empty_field_fails(self, repo, monkeypatch):
        root = repo(doc="> **Purpose:** What it is.\n> **Read when:** A trigger.\n> **Owns:** \n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_headers([Path("docs/target.md")])
        assert any("empty" in e for e in errors)

    @pytest.mark.parametrize("phrase", check_doc_structure.VAGUE_READ_WHEN)
    def test_vague_read_when_fails(self, repo, monkeypatch, phrase):
        root = repo(doc=f"> **Purpose:** X.\n> **Read when:** {phrase}.\n> **Owns:** Y.\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_headers([Path("docs/target.md")])
        assert len(errors) == 1
        assert phrase in errors[0]


class TestReachability:
    def test_linked_document_passes(self, repo, monkeypatch):
        root = repo(agents="# Agent instructions\n\n[target](docs/target.md)\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        assert check_doc_structure.check_reachability([Path("docs/target.md")]) == []

    def test_unlinked_document_fails(self, repo, monkeypatch):
        root = repo(agents="# Agent instructions\n\nNothing links anywhere.\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_reachability([Path("docs/target.md")])
        assert len(errors) == 1
        assert "not reachable" in errors[0]

    def test_two_hops_passes(self, repo, monkeypatch):
        root = repo(
            agents="# Agent instructions\n\n[mid](docs/mid.md)\n",
        )
        (root / "docs" / "mid.md").write_text("[target](target.md)\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        assert check_doc_structure.check_reachability([Path("docs/target.md")]) == []

    def test_three_hops_fails(self, repo, monkeypatch):
        root = repo(agents="# Agent instructions\n\n[a](docs/a.md)\n")
        (root / "docs" / "a.md").write_text("[b](b.md)\n")
        (root / "docs" / "b.md").write_text("[target](target.md)\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_reachability([Path("docs/target.md")])
        assert len(errors) == 1


class TestAdrStatuses:
    def _write_adr(self, root: Path, body: str) -> None:
        (root / "docs" / "adr").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "adr" / "0001-test.md").write_text(body)

    @pytest.mark.parametrize("status", check_doc_structure.RECOGNISED_ADR_STATUSES)
    def test_recognised_status_passes(self, repo, monkeypatch, status):
        root = repo()
        self._write_adr(root, f"# ADR 0001: Test\n\n## Status\n\n{status}\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        assert check_doc_structure.check_adr_statuses() == []

    def test_unrecognised_status_fails(self, repo, monkeypatch):
        root = repo()
        self._write_adr(root, "# ADR 0001: Test\n\n## Status\n\nDraft\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_adr_statuses()
        assert len(errors) == 1
        assert "Draft" in errors[0]

    def test_missing_status_fails(self, repo, monkeypatch):
        root = repo()
        self._write_adr(root, "# ADR 0001: Test\n\n## Context\n\nNo status here.\n")
        monkeypatch.setattr(check_doc_structure, "REPO_ROOT", root)
        errors = check_doc_structure.check_adr_statuses()
        assert len(errors) == 1
        assert "no '## Status' field" in errors[0]
