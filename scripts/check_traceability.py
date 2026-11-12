#!/usr/bin/env python3
"""Check traceability matrix is current.

Consumes the authoritative mapping in docs/spec/traceability.md and
verifies that every mapped spec, code and test file exists, and that
every product contract has a mapping.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = REPO_ROOT / "docs" / "spec"
TRACEABILITY_FILE = SPEC_DIR / "traceability.md"

# The matrix itself is not a product contract.
NON_CONTRACT_SPEC_FILES = {"traceability.md"}

TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")
BACKTICK_PATH = re.compile(r"`([^`]+)`")


def split_row(line: str) -> list[str]:
    """Split a markdown table row into trimmed cell values."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(cells: list[str]) -> bool:
    return all(set(cell) <= {"-", ":"} and cell for cell in cells)


def table_rows(text: str, header_prefix: str) -> list[list[str]]:
    """Rows of every table whose header row starts with ``header_prefix``."""
    rows: list[list[str]] = []
    in_table = False
    for line in text.split("\n"):
        if not TABLE_ROW.match(line):
            in_table = False
            continue
        cells = split_row(line)
        if is_separator(cells):
            continue
        if not in_table:
            in_table = cells[0].startswith(header_prefix)
            continue
        rows.append(cells)
    return rows


def paths_in(cell: str) -> list[str]:
    """Backticked repo paths in a cell, ignoring prose and placeholders."""
    found: list[str] = []
    for match in BACKTICK_PATH.finditer(cell):
        candidate = match.group(1)
        if candidate.startswith(("http://", "https://")):
            continue
        # Strip a :symbol or ::test suffix; the file is what must exist.
        path = re.split(r"::?", candidate)[0]
        if path and path not in {"—", "-"}:
            found.append(path)
    return found


# (spec section, contract file, code paths, test paths)
ContractRow = tuple[str, str, list[str], list[str]]
# (spec section, contract module, contract test)
ContractTestRow = tuple[str, str, str]


def load_mapping() -> tuple[list[ContractRow], list[ContractTestRow]]:
    """Read the authoritative mapping from the traceability document.

    Returns product-contract rows (spec section, contract file, code paths,
    test paths) and contract-test rows (spec section, contract module,
    contract test).

    Only the table headed ``Contract | Spec section | Code | Tests`` is read.
    The ADR Traceability table is future work with ``—`` placeholders and is
    deliberately not validated; that convention is documented in the matrix.
    """
    text = TRACEABILITY_FILE.read_text()

    contract_rows: list[ContractRow] = []
    contract_test_rows: list[tuple[str, str, str]] = []
    for cells in table_rows(text, "Contract"):
        if len(cells) < 4:
            continue
        contract, section, code, tests = cells[0], cells[1], cells[2], cells[3]
        code_paths = paths_in(code)
        test_paths = paths_in(tests)
        if code_paths or test_paths:
            contract_rows.append((section, contract, code_paths, test_paths))
        modules = paths_in(code)
        if modules and test_paths and "contracts/" in modules[0]:
            contract_test_rows.append((section, modules[0], test_paths[0]))

    return contract_rows, contract_test_rows


def check_file(path: str, description: str) -> bool:
    if (REPO_ROOT / path).exists():
        print(f"  ✅ {description}: {path}")
        return True
    print(f"  ❌ {description}: {path} (MISSING)")
    return False


def mapped_contract_files(contract_rows: list[ContractRow]) -> set[str]:
    """Contract file names the mapping covers, from its Contract column."""
    return {
        Path(contract.strip().strip("`")).name
        for _section, contract, _code, _tests in contract_rows
    }


def check_contracts_have_mappings(covered: set[str]) -> list[str]:
    """Every product contract under docs/spec/ appears in the mapping."""
    errors: list[str] = []
    for spec_file in sorted(SPEC_DIR.glob("*.md")):
        if spec_file.name in NON_CONTRACT_SPEC_FILES:
            continue
        if spec_file.name not in covered:
            errors.append(
                f"{spec_file.relative_to(REPO_ROOT)}: no mapping row in "
                f"{TRACEABILITY_FILE.relative_to(REPO_ROOT)} — add one under "
                f"'Spec section | Code | Tests'"
            )
    return errors


def main() -> int:
    if not TRACEABILITY_FILE.exists():
        print(f"❌ {TRACEABILITY_FILE} is missing")
        return 1

    contract_rows, contract_test_rows = load_mapping()
    covered = mapped_contract_files(contract_rows)
    print(f"Checking {len(contract_rows)} mapping rows from {TRACEABILITY_FILE.name}...")

    errors: list[str] = []

    print("\nChecking mapped files exist...")
    for section, _contract, code_paths, test_paths in contract_rows:
        print(f"\n{section}:")
        for path in code_paths:
            if not check_file(path, "code"):
                errors.append(f"mapped code file missing: {path}")
        for path in test_paths:
            if not check_file(path, "test"):
                errors.append(f"mapped test file missing: {path}")

    print("\nChecking contract tests...")
    for _section, module, test in contract_test_rows:
        if not check_file(module, "contract module"):
            errors.append(f"mapped contract module missing: {module}")
        if not check_file(test, "contract test"):
            errors.append(f"mapped contract test missing: {test}")

    print("\nChecking every product contract has a mapping...")
    errors += check_contracts_have_mappings(covered)

    if errors:
        print(f"\n❌ Found {len(errors)} traceability problem(s):")
        for error in errors:
            print(f"  {error}")
        return 1

    print("\n✅ All traceability checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
