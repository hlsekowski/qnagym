#!/usr/bin/env python3
"""Check documentation links and paths resolve.

Verifies that markdown links, anchors and backticked repo paths in
README.md, AGENTS.md and docs/** resolve on the current checkout.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Documentation roots to check.
DOC_ROOTS = (Path("README.md"), Path("AGENTS.md"), Path("docs"))

# Top-level directories a backticked repo path may be rooted in.
KNOWN_ROOTS = ("src", "tests", "scripts", "docs", "data", "example", ".github")

# Absolute blob/<branch> URLs to this repository are branch-dependent; use
# relative links. Issue and pull-request URLs have no relative equivalent and
# are allowed.
REPO_BLOB_PREFIX = "https://github.com/hlsekowski/qnagym/blob/"

# Paths intentionally excluded from checking.
ALLOWLIST: set[str] = set()

MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BACKTICK_PATH = re.compile(r"`([^`]+)`")
HEADING = re.compile(r"^#+\s+(.*)$", re.MULTILINE)


def tracked_markdown() -> list[Path]:
    """Markdown files tracked by git under the documentation roots."""
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    files = []
    for name in result.stdout.split():
        path = Path(name)
        if any(path == root or root in path.parents for root in DOC_ROOTS):
            files.append(path)
    return files


def is_allowlisted(path: Path) -> bool:
    return any(path == Path(entry) or Path(entry) in path.parents for entry in ALLOWLIST)


def slugify(heading: str) -> str:
    """GitHub anchor slug: strip backticks, lowercase, drop punctuation."""
    text = re.sub(r"`([^`]*)`", r"\1", heading.strip()).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


def heading_slugs(path: Path) -> set[str]:
    return {slugify(m.group(1)) for m in HEADING.finditer(path.read_text())}


def looks_like_repo_path(text: str) -> bool:
    """A backticked string that names a repository path."""
    if text.startswith(("http://", "https://", "~", "$", "<", "./", "../")):
        return False
    if "*" in text or " " in text or "\n" in text:
        return False
    if not text.startswith(KNOWN_ROOTS):
        return False
    return bool(re.search(r"\.[a-zA-Z]{1,4}$", text))


def edges(text: str, base: Path, root: Path) -> set[Path]:
    """Paths a document links to: markdown links, plus backticked repo paths.

    A link to a directory counts as an edge to every markdown file inside it,
    because a rendered directory listing reaches them all in one hop.
    """
    found: set[Path] = set()
    for match in MARKDOWN_LINK.finditer(text):
        target = match.group(2)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        file_part = target.partition("#")[0]
        if not file_part:
            continue
        resolved = (base / file_part).resolve()
        found.add(resolved)
        if resolved.is_dir():
            found |= {child.resolve() for child in resolved.rglob("*.md")}
    for match in BACKTICK_PATH.finditer(text):
        candidate = match.group(1)
        if candidate.endswith(".md"):
            found.add((root / candidate).resolve())
    return found


def check_file(path: Path, repo_root: Path | None = None) -> list[str]:
    """Return one message per unresolved reference in ``path``."""
    root = (repo_root or REPO_ROOT).resolve()
    errors: list[str] = []
    text = path.read_text()

    for match in MARKDOWN_LINK.finditer(text):
        target = match.group(2)
        line = text[: match.start()].count("\n") + 1

        if target.startswith(("http://", "https://", "mailto:", "#")):
            if target.startswith(REPO_BLOB_PREFIX):
                errors.append(
                    f"{path}:{line}: absolute repository URL {target} "
                    "- use a relative link (branch-independent)"
                )
            continue

        file_part, _, anchor = target.partition("#")
        if not file_part:
            continue

        resolved = (path.parent / file_part).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            errors.append(f"{path}:{line}: link {target} resolves outside the repository")
            continue
        if not resolved.exists():
            errors.append(f"{path}:{line}: link target does not exist: {target}")
            continue

        if anchor and anchor not in heading_slugs(resolved):
            errors.append(f"{path}:{line}: anchor #{anchor} not found in {file_part}")

    for match in BACKTICK_PATH.finditer(text):
        candidate = match.group(1)
        if not looks_like_repo_path(candidate):
            continue
        line = text[: match.start()].count("\n") + 1
        if not (REPO_ROOT / candidate).exists():
            errors.append(f"{path}:{line}: path does not exist: {candidate}")

    return errors


def check_adr_references(files: list[Path]) -> list[str]:
    """Textual 'ADR NNNN' references must map to an existing ADR file."""
    errors: list[str] = []
    existing = set()
    for path in (REPO_ROOT / "docs" / "adr").glob("*.md"):
        match = re.match(r"(\d{4})-", path.name)
        if match:
            existing.add(int(match.group(1)))

    for path in files:
        text = path.read_text()
        for match in re.finditer(r"ADR (\d{4})", text):
            if int(match.group(1)) not in existing:
                line = text[: match.start()].count("\n") + 1
                errors.append(f"{path}:{line}: ADR {match.group(1)} has no file in docs/adr/")
    return errors


def main() -> int:
    files = [path for path in tracked_markdown() if not is_allowlisted(path)]
    print(f"Checking {len(files)} documentation files for unresolved references...")

    errors: list[str] = []
    for path in files:
        errors.extend(check_file(path))
    errors.extend(check_adr_references(files))

    if errors:
        print(f"\n❌ Found {len(errors)} unresolved reference(s):")
        for error in errors:
            print(f"  {error}")
        return 1

    print("\n✅ All documentation links and paths resolve!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
