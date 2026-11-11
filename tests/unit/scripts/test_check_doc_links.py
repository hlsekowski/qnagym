"""Unit tests for the documentation link checker."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "check_doc_links.py"

_spec = importlib.util.spec_from_file_location("check_doc_links", SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
check_doc_links = importlib.util.module_from_spec(_spec)
sys.modules["check_doc_links"] = check_doc_links
_spec.loader.exec_module(check_doc_links)


@pytest.fixture
def doc_file(tmp_path: Path):
    """Write a markdown file under a temp repo root and return (write, root)."""

    def _write(name: str, content: str) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    return _write, tmp_path


class TestLooksLikeRepoPath:
    def test_repo_path_is_detected(self):
        assert check_doc_links.looks_like_repo_path("src/qnagym/contracts/constants.py")

    def test_glob_is_not_a_path(self):
        assert not check_doc_links.looks_like_repo_path("docs/spec/*.md")

    def test_env_path_is_not_a_repo_path(self):
        assert not check_doc_links.looks_like_repo_path("~/.config/qnagym/config.toml")
        assert not check_doc_links.looks_like_repo_path("$XDG_CONFIG_HOME/qnagym/config.toml")

    def test_placeholder_is_not_a_repo_path(self):
        assert not check_doc_links.looks_like_repo_path("<data_dir>/<id>.json")

    def test_unknown_root_is_not_a_repo_path(self):
        assert not check_doc_links.looks_like_repo_path("contracts/prompts.py")


class TestSlugify:
    def test_plain_heading(self):
        assert check_doc_links.slugify("State Machine") == "state-machine"

    def test_heading_with_backticks_and_punctuation(self):
        assert check_doc_links.slugify("`--model` flag") == "--model-flag"


class TestCheckFile:
    def test_relative_link_resolves(self, doc_file):
        write, root = doc_file
        write("docs/target.md", "# Target\n\n## Section\n")
        source = write("docs/source.md", "[t](target.md#section)\n")
        assert check_doc_links.check_file(source, root) == []

    def test_missing_link_target_fails(self, doc_file):
        write, root = doc_file
        source = write("docs/source.md", "[t](missing.md)\n")
        errors = check_doc_links.check_file(source, root)
        assert len(errors) == 1
        assert "missing.md" in errors[0]

    def test_missing_anchor_fails(self, doc_file):
        write, root = doc_file
        write("docs/target.md", "# Target\n\n## Section\n")
        source = write("docs/source.md", "[t](target.md#nope)\n")
        errors = check_doc_links.check_file(source, root)
        assert len(errors) == 1
        assert "#nope" in errors[0]

    def test_link_escaping_repo_root_fails(self, doc_file):
        write, root = doc_file
        source = write("docs/source.md", "[t](../../outside.md)\n")
        errors = check_doc_links.check_file(source, root)
        assert len(errors) == 1
        assert "outside the repository" in errors[0]

    def test_absolute_blob_url_fails(self, doc_file):
        write, root = doc_file
        source = write(
            "docs/source.md",
            "[c](https://github.com/hlsekowski/qnagym/blob/main/src/x.py)\n",
        )
        errors = check_doc_links.check_file(source, root)
        assert len(errors) == 1
        assert "relative link" in errors[0]

    def test_issue_url_is_allowed(self, doc_file):
        write, root = doc_file
        source = write("docs/source.md", "[#9](https://github.com/hlsekowski/qnagym/issues/9)\n")
        assert check_doc_links.check_file(source, root) == []

    def test_external_url_is_allowed(self, doc_file):
        write, root = doc_file
        source = write("docs/source.md", "[s](https://semver.org/spec/v2.0.0.html)\n")
        assert check_doc_links.check_file(source, root) == []

    def test_missing_backticked_path_fails(self, doc_file):
        write, root = doc_file
        source = write("docs/source.md", "See `src/qnagym/absent.py`.\n")
        errors = check_doc_links.check_file(source, root)
        assert len(errors) == 1
        assert "src/qnagym/absent.py" in errors[0]

    def test_existing_backticked_path_passes(self, doc_file):
        write, root = doc_file
        source = write("docs/source.md", "See `docs/spec/*.md`.\n")
        assert check_doc_links.check_file(source, root) == []


class TestCheckAdrReferences:
    def test_unknown_adr_fails(self, doc_file):
        write, _root = doc_file
        source = write("docs/source.md", "See ADR 9999 for details.\n")
        errors = check_doc_links.check_adr_references([source])
        assert len(errors) == 1
        assert "ADR 9999" in errors[0]

    def test_known_adr_passes(self, doc_file):
        write, _root = doc_file
        source = write("docs/source.md", "See ADR 0003 for details.\n")
        assert check_doc_links.check_adr_references([source]) == []
