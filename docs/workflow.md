# Workflow

> **Purpose:** The agent development workflow as ordered steps, each with a trigger and exactly one next document.
> **Read when:** starting any change — creating a branch, updating a spec, opening a PR, or handling PR feedback.
> **Owns:** the executable step list of the development workflow. Rationale lives in the ADRs; product behaviour lives in `docs/spec/`.

## Steps

Each step has the form `when <trigger> → <action> → next: <one doc>`.

### 1. Branch

**when** starting any change → create a dedicated branch from `main` → next: [`docs/spec.md`](spec.md)

```bash
git checkout -b <type>/<short-description>
```

Branch types: `feat/...`, `fix/...`, `chore/...`, `docs/...`. Rule D6 in [`docs/rules.md`](rules.md) requires a dedicated branch for every modification; no direct commits to `main`.

### 2. Spec

**when** the change affects product behaviour or a data shape → update the spec contract that covers the task → next: [`docs/spec/traceability.md`](spec/traceability.md)

Modify the relevant `docs/spec/*.md` contract section. Constitution principle C5 ("Spec before code") requires the spec to exist before implementation.

### 3. Contract

**when** a data shape changed → update `src/qnagym/contracts/*.py` → next: [`docs/testing.md`](testing.md)

### 4. Tests

**when** a contract changed → add or modify tests in `tests/contracts/` and `tests/unit/` → next: [`docs/testing.md`](testing.md)

### 5. Implement

**when** the contract and its tests exist → change application code to satisfy them → next: [`docs/testing.md`](testing.md)

### 6. Verify locally

**when** implementation is complete → run the checks → next: [`docs/development.md`](development.md)

```bash
pytest                      # mocked HTTP, no live model
ruff check . && ruff format --check .
python3 -m mypy src/qnagym
python3 scripts/check_traceability.py
python3 scripts/check_doc_defaults.py
python3 scripts/check_doc_links.py
python3 scripts/check_doc_structure.py
```

Stage new files before running the path and depth checkers: they inspect git-tracked files only, so an untracked file's broken link reaches CI instead of failing locally.

#### Which checks a change type requires

Every change type runs the full list above. The table states what each type must *additionally* satisfy, so a change is not treated as complete while a check it affects is unrun.

| Change type | Additionally required |
|---|---|
| `feat/` — product behaviour | spec contract updated before code; `check_traceability.py` covers the new section; contract and unit tests added |
| `fix/` — defect | a test that fails without the fix; spec corrected if the contract was wrong |
| `chore/` — tooling, CI, dependencies | `check_doc_structure.py` if a checker changed; a failing test case for any new check |
| `docs/` — documentation only | `check_doc_links.py` and `check_doc_structure.py`; no code change, so `pytest` and `mypy` still run but are not the point |

A change that alters a data shape also updates `src/qnagym/contracts/` and its contract tests, per [`docs/testing.md`](testing.md).

### 7. Open a PR

**when** local checks pass → push the branch and open a PR against `main` → next: [`docs/adr/0006-pr-process.md`](adr/0006-pr-process.md)

### 8. Wait for PR checks

**when** a PR is open → wait for all required checks to pass → next: [`docs/adr/0006-pr-process.md`](adr/0006-pr-process.md)

Required checks: lint, type-check, tests, traceability, doc defaults, doc links, doc structure, security, dependencies.

| Check outcome | Action |
|---|---|
| passing | none |
| pending / running | await |
| failed | correct and push, if the attempt budget allows |
| cancelled, skipped, or infrastructure-failed | not a development failure — re-run or await; do not spend an attempt |
| externally blocked | report and await the user |

Correction attempts are capped per batch by `MAX_CORRECTION_ATTEMPTS_PER_BATCH`; an explicit retry comment starts a new batch and reopening the PR does not reset the counter. The full rules are in [ADR 0006 §2](adr/0006-pr-process.md).

### 9. Merge

**when** all checks pass → squash merge → next: [`docs/adr/0006-pr-process.md`](adr/0006-pr-process.md)

Never push directly to `main`. No workflow merges a PR automatically — rule D7 in [`docs/rules.md`](rules.md).

### 10. Delete the branch

**when** the PR is merged → delete the remote branch → next: [`docs/development.md`](development.md)

### 11. Sync locally

**when** the PR is merged → update local `main` → next: [`docs/development.md`](development.md)

```bash
git checkout main && git pull
```

## Related

- [`docs/development.md`](development.md) — environment setup, tooling and the development-only model list
- [`docs/spec/traceability.md`](spec/traceability.md) — how to map a spec section to code and tests
- [`docs/adr/0003-local-development-workflow.md`](adr/0003-local-development-workflow.md) — the decision record for this workflow
- [`docs/adr/0006-pr-process.md`](adr/0006-pr-process.md) — PR feedback evaluation, check monitoring and lifecycle
- [`docs/adr/0007-sdd-process.md`](adr/0007-sdd-process.md) — the SDD process this workflow executes

## Maintaining this workflow

Always-loaded context grows only with evidence of an observed failure: if an agent made a mistake that a line here would have prevented, add that line and record the failure. Rerun the task set when the agent tool or model changes.
