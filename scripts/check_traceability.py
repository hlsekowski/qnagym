#!/usr/bin/env python3
"""Check traceability matrix is current.

Verifies that every spec contract has corresponding code and tests.
"""

import sys
from pathlib import Path

SPEC_DIR = Path("docs/spec")
CONTRACTS_DIR = Path("src/qnagym/contracts")
DOMAIN_DIR = Path("src/qnagym/domain")
SERVICES_DIR = Path("src/qnagym/services")
ADAPTERS_DIR = Path("src/qnagym/adapters")
TESTS_CONTRACTS_DIR = Path("tests/contracts")
TESTS_UNIT_DIR = Path("tests/unit")
TESTS_INTEGRATION_DIR = Path("tests/integration")

# Expected mappings from docs/spec/traceability.md
EXPECTED = {
    "cli.md": {
        "code": [
            "adapters/cli.py",
            "services/generate.py",
            "services/refine.py",
            "services/confirm.py",
            "services/drill.py",
            "services/evaluate.py",
            "services/progress.py",
        ],
        "tests": [
            "unit/adapters/test_cli.py",
            "unit/services/test_generate.py",
            "unit/services/test_refine.py",
            "unit/services/test_confirm.py",
            "unit/services/test_drill.py",
            "unit/services/test_evaluate.py",
            "unit/services/test_progress.py",
        ],
    },
    "session.md": {
        "code": [
            "contracts/types.py",
            "contracts/validation.py",
            "contracts/session.py",
        ],
        "tests": [
            "contracts/test_types.py",
            "contracts/test_validation.py",
            "contracts/test_session_schema.py",
        ],
    },
    "config.md": {
        "code": [
            "adapters/config.py",
            "contracts/constants.py",
            "contracts/config.py",
        ],
        "tests": [
            "unit/adapters/test_config.py",
            "contracts/test_constants.py",
            "contracts/test_config_contract.py",
        ],
    },
    "flow.md": {
        "code": [
            "domain/flow.py",
            "contracts/validation.py",
            "contracts/flow.py",
        ],
        "tests": [
            "unit/domain/test_flow.py",
            "contracts/test_validation.py",
            "contracts/test_flow_contract.py",
        ],
    },
    "prompts.md": {
        "code": [
            "domain/scoring.py",
            "contracts/validation.py",
            "contracts/prompts.py",
        ],
        "tests": [
            "unit/domain/test_scoring.py",
            "contracts/test_validation.py",
            "contracts/test_prompts_contract.py",
        ],
    },
    "questions.md": {
        "code": [
            "domain/questions.py",
            "contracts/validation.py",
            "contracts/questions.py",
        ],
        "tests": [
            "contracts/test_validation.py",
            "contracts/test_questions_contract.py",
        ],
    },
}

# Contract tests mapping
CONTRACT_TESTS = {
    "cli.md": "test_cli_contract.py",
    "config.md": "test_config_contract.py",
    "flow.md": "test_flow_contract.py",
    "prompts.md": "test_prompts_contract.py",
    "questions.md": "test_questions_contract.py",
    "session.md": "test_session_schema.py",
    "constants": "test_constants.py",
}


def check_exists(path: Path, description: str) -> bool:
    if path.exists():
        print(f"  ✅ {description}: {path}")
        return True
    else:
        print(f"  ❌ {description}: {path} (MISSING)")
        return False


def main() -> int:
    all_ok = True

    print("Checking spec contracts...")
    for spec_file in SPEC_DIR.glob("*.md"):
        if spec_file.name == "traceability.md":
            continue
        if not spec_file.exists():
            print(f"  ❌ Spec file missing: {spec_file}")
            all_ok = False

    print("\nChecking code mappings...")
    for spec_file, mapping in EXPECTED.items():
        print(f"\n{spec_file}:")
        for code_file in mapping["code"]:
            path = Path("src/qnagym") / code_file
            if not check_exists(path, "code"):
                all_ok = False
        for test_file in mapping["tests"]:
            path = Path("tests") / test_file
            if not check_exists(path, "test"):
                all_ok = False

    print("\nChecking contract tests...")
    for _spec_file, test_file in CONTRACT_TESTS.items():
        path = TESTS_CONTRACTS_DIR / test_file
        if not check_exists(path, "contract test"):
            all_ok = False

    # Check traceability.md exists
    traceability = SPEC_DIR / "traceability.md"
    if not check_exists(traceability, "traceability matrix"):
        all_ok = False

    if all_ok:
        print("\n✅ All traceability checks passed!")
        return 0
    else:
        print("\n❌ Some traceability checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
