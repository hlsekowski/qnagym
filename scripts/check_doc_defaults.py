#!/usr/bin/env python3
"""Check documented defaults match src/ config.

Verifies that constants in docs/ match constants in src/qnagym/contracts/constants.py.
"""

import re
import sys
from pathlib import Path

CONSTANTS_FILE = Path("src/qnagym/contracts/constants.py")

# Patterns to extract constants from constants.py
PATTERNS = {
    "DEFAULT_BASE_URL": r'DEFAULT_BASE_URL\s*=\s*"([^"]+)"',
    "DEFAULT_MODEL": r'DEFAULT_MODEL\s*=\s*"([^"]+)"',
    "DEFAULT_API_KEY": r'DEFAULT_API_KEY\s*=\s*"([^"]+)"',
    "DEFAULT_DATA_DIR": r'DEFAULT_DATA_DIR\s*=\s*Path\("([^"]+)"\)',
    "DEFAULT_TEMPERATURE": r"DEFAULT_TEMPERATURE\s*=\s*([\d.]+)",
    "DEFAULT_MAX_TOKENS": r"DEFAULT_MAX_TOKENS\s*=\s*(\d+)",
    "DEFAULT_TIMEOUT": r"DEFAULT_TIMEOUT\s*=\s*(\d+)",
    "FALLBACK_COUNT": r"FALLBACK_COUNT\s*=\s*(\d+)",
    "QUESTION_COUNT_MIN": r"QUESTION_COUNT_MIN\s*=\s*(\d+)",
    "QUESTION_COUNT_MAX": r"QUESTION_COUNT_MAX\s*=\s*(\d+)",
    "MINUTES_PER_QUESTION": r"MINUTES_PER_QUESTION\s*=\s*(\d+)",
    "MIN_MATERIAL_CHARS": r"MIN_MATERIAL_CHARS\s*=\s*(\d+)",
    "CONFIDENCE_SHOW_BELOW": r"CONFIDENCE_SHOW_BELOW\s*=\s*([\d.]+)",
    "ALTERNATIVE_DELTA": r"ALTERNATIVE_DELTA\s*=\s*([\d.]+)",
    "VALID_STATUSES": r"VALID_STATUSES\s*=\s*\{([^}]+)\}",
    "CLARIFYING_QUESTIONS": r"CLARIFYING_QUESTIONS\s*=\s*\[([^\]]+)\]",
    "STANDARD_USE_MODELS": r"STANDARD_USE_MODELS\s*=\s*\{([^}]+)\}",
    "AVOID_MODELS": r"AVOID_MODELS\s*=\s*\{([^}]+)\}",
}


def extract_constants() -> dict[str, str]:
    """Extract constants from constants.py."""
    content = CONSTANTS_FILE.read_text()
    constants = {}
    for name, pattern in PATTERNS.items():
        match = re.search(pattern, content)
        if match:
            constants[name] = match.group(1).strip()
        else:
            constants[name] = "NOT_FOUND"
    return constants


def check_docs(constants: dict[str, str]) -> list[str]:
    """Check docs for hardcoded values that should reference constants."""
    errors = []

    # Files to check
    doc_files = [
        Path("README.md"),
        Path("docs/spec.md"),
        Path("docs/spec/cli.md"),
        Path("docs/spec/session.md"),
        Path("docs/spec/config.md"),
        Path("docs/spec/flow.md"),
        Path("docs/spec/prompts.md"),
        Path("docs/spec/questions.md"),
        Path("docs/constitution.md"),
        Path("docs/rules.md"),
        Path("docs/development.md"),
        Path("docs/ai_provider_policy.md"),
    ]

    # Patterns that should not be hardcoded in docs
    forbidden_patterns = [
        (r"http://127\.0\.0\.1:11434/v1", "DEFAULT_BASE_URL"),
        (r"gemma3:12b", "DEFAULT_MODEL"),
        (r"ollama", "DEFAULT_API_KEY"),
        (r"data/sessions", "DEFAULT_DATA_DIR"),
        (r"temperature.*0\.0", "DEFAULT_TEMPERATURE"),
        (r"max_tokens.*4096", "DEFAULT_MAX_TOKENS"),
        (r"timeout.*60", "DEFAULT_TIMEOUT"),
        (r"FALLBACK_COUNT.*5", "FALLBACK_COUNT"),
        (r"QUESTION_COUNT_MIN.*3", "QUESTION_COUNT_MIN"),
        (r"QUESTION_COUNT_MAX.*15", "QUESTION_COUNT_MAX"),
        (r"MINUTES_PER_QUESTION.*6", "MINUTES_PER_QUESTION"),
        (r"MIN_MATERIAL_CHARS.*20", "MIN_MATERIAL_CHARS"),
        (r"CONFIDENCE_SHOW_BELOW.*0\.95", "CONFIDENCE_SHOW_BELOW"),
        (r"ALTERNATIVE_DELTA.*0\.05", "ALTERNATIVE_DELTA"),
    ]

    for doc_file in doc_files:
        if not doc_file.exists():
            continue
        content = doc_file.read_text()
        for pattern, const_name in forbidden_patterns:
            if re.search(pattern, content):
                # Allow in code blocks that show config examples
                # Check if it's in a code block showing TOML/env example
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        # Check context - allow in config examples
                        context = "\n".join(lines[max(0, i - 2) : i + 3])
                        ctx_lower = context.lower()
                        if (
                            "toml" in ctx_lower
                            or "env" in ctx_lower
                            or "example" in ctx_lower
                            or "default" in ctx_lower
                        ):
                            continue
                        errors.append(
                            f"{doc_file}:{i + 1}: Hardcoded value matching "
                            f"{const_name} - use reference instead"
                        )

    return errors


def main() -> int:
    print("Extracting constants from src/qnagym/contracts/constants.py...")
    constants = extract_constants()

    print("Checking docs for hardcoded defaults...")
    errors = check_docs(constants)

    if errors:
        print("\n❌ Found hardcoded values in docs that should reference constants:")
        for error in errors:
            print(f"  {error}")
        return 1
    else:
        print("\n✅ All documented defaults match constants!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
