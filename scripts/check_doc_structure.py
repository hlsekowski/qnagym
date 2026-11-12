#!/usr/bin/env python3
"""Check documentation structure does not regress.

Enforces the structure rules that would otherwise live only in prose:
the AGENTS.md line budget, the document header convention, two-hop
reachability from AGENTS.md, and recognised ADR status values.

Link-graph helpers are imported from check_doc_links.py so the two
checkers cannot disagree about what a link is.
"""

import importlib.util
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent

_spec = importlib.util.spec_from_file_location(
    "check_doc_links", SCRIPTS_DIR / "check_doc_links.py"
)
assert _spec is not None and _spec.loader is not None
check_doc_links = importlib.util.module_from_spec(_spec)
sys.modules["check_doc_links"] = check_doc_links
_spec.loader.exec_module(check_doc_links)

# Single definition site for the AGENTS.md budget. Set from the result of
# issue #58 (32 lines) plus headroom for a legitimate gotcha or routing row.
AGENTS_MD_LINE_BUDGET = 40

# Single definition site for the README.md budget, from constitution C2.
README_MD_LINE_BUDGET = 80

# Header fields every living document under docs/ must open with.
REQUIRED_HEADER_FIELDS = ("Purpose", "Read when", "Owns")

# "Read when" must name a concrete trigger. Banned phrases agreed in #55 Q5.
VAGUE_READ_WHEN = (
    "when needed",
    "as reference",
    "for context",
    "general guidance",
    "overview",
    "background",
)

# Recognised ADR status values.
RECOGNISED_ADR_STATUSES = ("Accepted", "Proposed", "Superseded", "Deprecated", "Rejected")

# Files intentionally unreachable from AGENTS.md within two hops.
UNREACHABLE_ALLOWLIST: set[str] = set()

AGENTS_MD = Path("AGENTS.md")
README_MD = Path("README.md")
ADR_DIR = Path("docs/adr")

HEADER_FIELD = re.compile(r"^> \*\*(Purpose|Read when|Owns):\*\*\s*(.+)$", re.MULTILINE)
ADR_STATUS = re.compile(r"^## Status\s*\n\s*(\S.*)$", re.MULTILINE)


def status_value(line: str) -> str:
    """The recognised status word at the start of a Status line.

    A Status line may carry an annotation after the value, e.g.
    "Accepted. §6–§10 elevated to ADR 0006 …". The value is the first
    word; anything after it is annotation.
    """
    return line.strip().split(". ")[0].split(" ")[0].strip()


def doc_files() -> list[Path]:
    """Living markdown files under docs/, excluding the allowlist."""
    return [
        path
        for path in check_doc_links.tracked_markdown()
        if (REPO_ROOT / path).is_file()
        and Path("docs") in path.parents
        and not check_doc_links.is_allowlisted(path)
    ]


def check_line_budget(path: Path, budget: int) -> list[str]:
    """A file must stay within its line budget."""
    lines = (REPO_ROOT / path).read_text().count("\n")
    if lines > budget:
        return [
            f"{path}: {lines} lines exceeds the budget of {budget} — "
            f"remove a line or raise the budget in scripts/check_doc_structure.py "
            f"with a reason"
        ]
    return []


def check_agents_budget() -> list[str]:
    """AGENTS.md must stay within the line budget."""
    return check_line_budget(AGENTS_MD, AGENTS_MD_LINE_BUDGET)


def check_readme_budget() -> list[str]:
    """README.md must stay within the line budget (constitution C2)."""
    return check_line_budget(README_MD, README_MD_LINE_BUDGET)


def check_headers(files: list[Path]) -> list[str]:
    """Every living document opens with Purpose, Read when and Owns."""
    errors: list[str] = []
    for path in files:
        text = (REPO_ROOT / path).read_text()
        found = dict(HEADER_FIELD.findall(text))
        for field in REQUIRED_HEADER_FIELDS:
            if field not in found:
                errors.append(
                    f"{path}: missing header field '> **{field}:**' — "
                    f"see docs/documentation.md for the convention"
                )
            elif not found[field].strip():
                errors.append(f"{path}: header field '{field}' is empty")
        read_when = found.get("Read when", "").lower()
        for phrase in VAGUE_READ_WHEN:
            if phrase in read_when:
                errors.append(
                    f"{path}: 'Read when' uses the vague phrase '{phrase}' — "
                    f"name a concrete trigger instead"
                )
    return errors


def reachable_from_agents() -> set[Path]:
    """Files reachable from AGENTS.md within two link hops."""
    agents = REPO_ROOT / AGENTS_MD
    hop1 = check_doc_links.edges(agents.read_text(), agents.parent, REPO_ROOT)
    hop1 = {path for path in hop1 if path.exists()}
    hop2: set[Path] = set()
    for path in hop1:
        if path.is_file():
            hop2 |= check_doc_links.edges(path.read_text(), path.parent, REPO_ROOT)
    return hop1 | {path for path in hop2 if path.exists()}


def check_reachability(files: list[Path]) -> list[str]:
    """Every living document is reachable from AGENTS.md within two hops."""
    reachable = reachable_from_agents()
    errors: list[str] = []
    for path in files:
        resolved = (REPO_ROOT / path).resolve()
        if resolved not in reachable:
            errors.append(
                f"{path}: not reachable from {AGENTS_MD} within 2 link hops — "
                f"add a routing row, or allowlist it in "
                f"scripts/check_doc_structure.py with a reason"
            )
    return errors


def check_adr_statuses() -> list[str]:
    """Every ADR has a Status field whose value is recognised."""
    errors: list[str] = []
    for path in sorted((REPO_ROOT / ADR_DIR).glob("*.md")):
        match = ADR_STATUS.search(path.read_text())
        if not match:
            errors.append(f"{path.relative_to(REPO_ROOT)}: no '## Status' field")
            continue
        value = status_value(match.group(1))
        if value not in RECOGNISED_ADR_STATUSES:
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: status '{value}' "
                f"is not one of {', '.join(RECOGNISED_ADR_STATUSES)}"
            )
    return errors


def main() -> int:
    files = doc_files()
    print(f"Checking documentation structure across {len(files)} files...")

    errors: list[str] = []
    errors += check_agents_budget()
    errors += check_readme_budget()
    errors += check_headers(files)
    errors += check_reachability(files)
    errors += check_adr_statuses()

    if errors:
        print(f"\n❌ Found {len(errors)} structure problem(s):")
        for error in errors:
            print(f"  {error}")
        return 1

    print("\n✅ Documentation structure is within budget and conventions!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
