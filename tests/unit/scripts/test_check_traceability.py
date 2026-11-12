"""Unit tests for the traceability checker."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"

_spec = importlib.util.spec_from_file_location(
    "check_traceability", SCRIPTS_DIR / "check_traceability.py"
)
assert _spec is not None and _spec.loader is not None
check_traceability = importlib.util.module_from_spec(_spec)
sys.modules["check_traceability"] = check_traceability
_spec.loader.exec_module(check_traceability)

MATRIX = """# Traceability Matrix

| Contract | Spec section | Code | Tests |
|---|---|---|
| `docs/spec/cli.md` | `spec.md#cli` | `a.py` | `t.py` |

## ADR Traceability

| ADR | Spec sections | Code (future) | Tests (future) |
|---|---|---|---|
| ADR 0001 | `spec.md` (SDD principles) | — | — |
"""


@pytest.fixture
def repo(tmp_path: Path):
    """A minimal repo with a spec dir, one contract and its mapping."""

    def _build(matrix: str = MATRIX, contracts: tuple[str, ...] = ("cli.md",)) -> Path:
        spec = tmp_path / "docs" / "spec"
        spec.mkdir(parents=True)
        (spec / "traceability.md").write_text(matrix)
        for name in contracts:
            (spec / name).write_text(f"# {name}\n")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "qnagym").mkdir()
        (tmp_path / "src" / "qnagym" / "adapters").mkdir()
        (tmp_path / "a.py").write_text("# a\n")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "unit").mkdir()
        (tmp_path / "tests" / "unit" / "adapters").mkdir()
        (tmp_path / "t.py").write_text("# t\n")
        return tmp_path

    return _build


class TestTableParsing:
    def test_reads_contract_rows(self, repo, monkeypatch):
        root = repo()
        monkeypatch.setattr(check_traceability, "REPO_ROOT", root)
        monkeypatch.setattr(check_traceability, "SPEC_DIR", root / "docs" / "spec")
        monkeypatch.setattr(
            check_traceability, "TRACEABILITY_FILE", root / "docs" / "spec" / "traceability.md"
        )
        rows, contract_tests = check_traceability.load_mapping()
        assert len(rows) == 1
        section, contract, code, tests = rows[0]
        assert contract.strip("`") == "docs/spec/cli.md"
        assert code == ["a.py"]
        assert tests == ["t.py"]

    def test_adr_future_rows_are_not_product_mappings(self, repo, monkeypatch):
        root = repo()
        monkeypatch.setattr(check_traceability, "REPO_ROOT", root)
        monkeypatch.setattr(check_traceability, "SPEC_DIR", root / "docs" / "spec")
        monkeypatch.setattr(
            check_traceability, "TRACEABILITY_FILE", root / "docs" / "spec" / "traceability.md"
        )
        rows, _ = check_traceability.load_mapping()
        assert all("ADR" not in section for section, _c, _code, _tests in rows)

    def test_symbol_suffix_is_stripped(self, repo, monkeypatch):
        root = repo(
            matrix=MATRIX.replace(
                "`src/qnagym/adapters/cli.py`", "`src/qnagym/adapters/cli.py:main`"
            )
        )
        monkeypatch.setattr(check_traceability, "REPO_ROOT", root)
        monkeypatch.setattr(check_traceability, "SPEC_DIR", root / "docs" / "spec")
        monkeypatch.setattr(
            check_traceability, "TRACEABILITY_FILE", root / "docs" / "spec" / "traceability.md"
        )
        rows, _ = check_traceability.load_mapping()
        assert rows[0][2] == ["a.py"]


class TestDrift:
    def test_valid_mapping_passes(self, repo, monkeypatch):
        root = repo()
        monkeypatch.setattr(check_traceability, "REPO_ROOT", root)
        monkeypatch.setattr(check_traceability, "SPEC_DIR", root / "docs" / "spec")
        monkeypatch.setattr(
            check_traceability, "TRACEABILITY_FILE", root / "docs" / "spec" / "traceability.md"
        )
        assert check_traceability.main() == 0

    def test_new_contract_without_mapping_fails(self, repo, monkeypatch):
        root = repo(contracts=("cli.md", "session.md"))
        monkeypatch.setattr(check_traceability, "REPO_ROOT", root)
        monkeypatch.setattr(check_traceability, "SPEC_DIR", root / "docs" / "spec")
        monkeypatch.setattr(
            check_traceability, "TRACEABILITY_FILE", root / "docs" / "spec" / "traceability.md"
        )
        assert check_traceability.main() == 1

    def test_missing_mapped_code_file_fails(self, repo, monkeypatch):
        root = repo()
        (root / "a.py").unlink()
        monkeypatch.setattr(check_traceability, "REPO_ROOT", root)
        monkeypatch.setattr(check_traceability, "SPEC_DIR", root / "docs" / "spec")
        monkeypatch.setattr(
            check_traceability, "TRACEABILITY_FILE", root / "docs" / "spec" / "traceability.md"
        )
        assert check_traceability.main() == 1

    def test_missing_mapped_test_file_fails(self, repo, monkeypatch):
        root = repo()
        (root / "t.py").unlink()
        monkeypatch.setattr(check_traceability, "REPO_ROOT", root)
        monkeypatch.setattr(check_traceability, "SPEC_DIR", root / "docs" / "spec")
        monkeypatch.setattr(
            check_traceability, "TRACEABILITY_FILE", root / "docs" / "spec" / "traceability.md"
        )
        assert check_traceability.main() == 1
