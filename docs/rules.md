# Rule Catalog & Enforcement Matrix

**Constitution principles (C1–C10) live in [`docs/constitution.md`](constitution.md)** — this file covers agent rules (A) and development rules (D) only.

## Agent Rules (A1–A4)

| ID | Rule | Severity | Enforcement Method | CI Job / Check |
|----|------|----------|-------------------|----------------|
| A1 | References over duplication | MUST | Lint: no hardcoded constants that exist in `docs/` or `src/` config | Custom script |
| A2 | Verify before writing | MUST | Review gate: PR must reference source for new values | Manual (PR review) |
| A3 | DRY across docs and code | MUST | Script: documented defaults match `src/` config | `scripts/check_doc_defaults.py` (pre-commit, CI) |
| A4 | Honesty about confidence | MUST | Thresholds defined in `docs/spec.md` (not hardcoded) | Unit test |

## Development Rules (D1–D6)

| ID | Rule | Severity | Enforcement Method | CI Job / Check |
|----|------|----------|-------------------|----------------|
| D1 | Definition of Done | MUST | PR checklist: spec, contract, tests, CI, security, docs, traceability, changelog | `.github/pull_request_template.md` |
| D2 | Git conventions | MUST | Conventional Commits enforced, PR template with checklist | `commitlint` + PR template |
| D3 | Versioning & changelog | SHOULD | SemVer tags, `CHANGELOG.md` (Keep a Changelog) | Release workflow |
| D4 | Code style | MUST | `ruff` + `mypy strict` in `pyproject.toml` as single source | `ruff` + `mypy` (pre-commit, CI) |
| D5 | Error handling & CLI | SHOULD | Stable exit codes, stderr for errors, `--json` output | Unit tests |
| D6 | Dedicated branches | MUST | Every modification done in a dedicated branch; no direct commits to `main` | CI: reject direct pushes to `main`; PR required |

## No-Cost AI Rules (NC1–NC8)

| ID | Rule | Severity | Enforcement Method | CI Job / Check |
|----|------|----------|-------------------|----------------|
| NC1 | Default model is local | MUST | Config default points to local Ollama/LM Studio | Config check in CI |
| NC2 | Optional free-tier cloud only | MUST | No paid API keys in defaults; env var override only | Config check in CI |
| NC3 | No vendor SDKs | MUST | Only `openai` SDK in dependencies | `pip-audit` + dependency review |
| NC4 | Structured JSON output | MUST | All model calls use `response_format=json_object` | Code review + unit tests |
| NC5 | Temperature=0 default | SHOULD | Config default; documented in spec | Config check |
| NC6 | Prompts versioned | SHOULD | Prompts in contracts with version constants | Code review |
| NC7 | No PII to cloud | MUST | Local-first; anonymized if cloud used | Privacy review |
| NC8 | Model drift monitoring | SHOULD | Track evaluation consistency over time | Integration test |

## CI Jobs (from `.github/workflows/ci.yml`)

| Job | Rules Covered | Description |
|-----|---------------|-------------|
| `lint` | C2, C7, D4 | `ruff` check + format |
| `typecheck` | C7, D4 | `mypy` strict |
| `test` | C6, C7 | `pytest` with coverage ≥ 80% |
| `security` | C8, C9 | `gitleaks` (secrets) + `bandit` (SAST) |
| `dependencies` | C9 | `pip-audit` (vulns) + `pip-licenses` |
| `traceability` | C5 | `scripts/check_traceability.py` |
| `doc-defaults` | A3 | `scripts/check_doc_defaults.py` |
| `pre-commit` | C6, C7, C8, C9, D4 | All pre-commit hooks |

## Severity Legend

- **MUST** — Blocking: CI fails, PR cannot merge without exception.
- **SHOULD** — Strongly recommended: CI warns, merge allowed with justification.
- **MAY** — Optional: no enforcement, best practice.

## Exception Process

For **MUST** rules only:
1. Open issue with `exception` label.
2. Document: rule ID, justification, owner, expiry date.
3. Approval from maintainer required.
4. Record in `docs/exceptions.md`.

## Hotfix Path

For urgent production fixes that bypass CI:
1. Create `hotfix/` branch from `main`.
2. Apply minimal fix with tests.
3. Get maintainer approval (documented in PR).
4. Merge with `--no-ff` to preserve history.
5. Run full CI post-merge; if failures, revert immediately.
6. Document exception in `docs/exceptions.md`.

## Related Files

- `docs/constitution.md` — Canonical principles (C1–C10) with enforcement
- `docs/adr/0001-spec-driven-development.md` — SDD architecture decision
- `docs/adr/0002-architecture-dependency-model.md` — Dependency model
- `AGENTS.md` — Agent instructions (references C1–C10, A1–A4)
- `docs/development.md` — Developer workflow
- `docs/testing.md` — Testing standards
- `docs/ai_provider_policy.md` — AI model usage, provider config, privacy
- `docs/spec/traceability.md` — Spec → code → test mapping
- `.pre-commit-config.yaml` — Pre-commit hooks (C6, C7, C8, C9, D4)
- `.github/workflows/ci.yml` — CI pipeline
- `pyproject.toml` — Tool config (ruff, mypy, pytest)
