# Traceability Matrix

> **Purpose:** Maps each spec section to the code symbols and tests that implement it.
> **Read when:** changing a spec section, or checking which code and tests a spec change affects.
> **Owns:** the spec-section → code → test mapping and the ADR traceability table.

Maps spec sections → code symbols → tests.

| Contract | Spec section | Code | Tests |
|---|---|---|
| `docs/spec/cli.md` | `spec.md#cli` | `src/qnagym/adapters/cli.py`, `src/qnagym/services/generate.py`, `src/qnagym/services/refine.py`, `src/qnagym/services/confirm.py`, `src/qnagym/services/drill.py`, `src/qnagym/services/evaluate.py`, `src/qnagym/services/progress.py` | `tests/unit/adapters/test_cli.py`, `tests/unit/services/test_generate.py`, `tests/unit/services/test_refine.py`, `tests/unit/services/test_confirm.py`, `tests/unit/services/test_drill.py`, `tests/unit/services/test_evaluate.py`, `tests/unit/services/test_progress.py` |
| `docs/spec/cli.md` | `spec.md#cli` (drill --interactive) | `src/qnagym/services/drill.py:_drill_interactive`, `src/qnagym/adapters/cli.py` | `tests/unit/services/test_drill.py::test_drill_interactive_*` |
| `docs/spec/session.md` | `spec.md#session-json` | `src/qnagym/contracts/types.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/session.py` | `tests/contracts/test_types.py`, `tests/contracts/test_validation.py`, `tests/contracts/test_session_schema.py` |
| `docs/spec/config.md` | `spec.md#config` | `src/qnagym/adapters/config.py`, `src/qnagym/contracts/constants.py`, `src/qnagym/contracts/config.py` | `tests/unit/adapters/test_config.py`, `tests/contracts/test_constants.py`, `tests/contracts/test_config_contract.py` |
| `docs/spec/flow.md` | `spec.md#flow` | `src/qnagym/domain/flow.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/flow.py` | `tests/unit/domain/test_flow.py`, `tests/contracts/test_validation.py`, `tests/contracts/test_flow_contract.py` |
| `docs/spec/prompts.md` | `spec.md#models` (prompts) | `src/qnagym/domain/scoring.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/prompts.py` | `tests/unit/domain/test_scoring.py`, `tests/contracts/test_validation.py`, `tests/contracts/test_prompts_contract.py` |
| `docs/spec/questions.md` | `spec.md#questions` | `src/qnagym/domain/questions.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/questions.py` | `tests/contracts/test_validation.py`, `tests/contracts/test_questions_contract.py` |
| `docs/spec/questions.md` | `spec.md#questions` (vague material) | `src/qnagym/domain/questions.py` | `tests/unit/domain/test_questions.py` |
| `docs/spec/flow.md` | `spec.md#flow` (full E2E) | `src/qnagym/domain/flow.py`, `src/qnagym/adapters/cli.py` | `tests/integration/test_e2e_flow.py` |

## Contract Tests (spec → contracts)

| Spec section | Contract module | Contract tests |
|---|---|---|
| `docs/spec/cli.md` | `spec.md#cli` | `src/qnagym/contracts/cli.py` | `tests/contracts/test_cli_contract.py` |
| `docs/spec/config.md` | `spec.md#config` | `src/qnagym/contracts/config.py` | `tests/contracts/test_config_contract.py` |
| `docs/spec/flow.md` | `spec.md#flow` | `src/qnagym/contracts/flow.py` | `tests/contracts/test_flow_contract.py` |
| `docs/spec/prompts.md` | `spec.md#models` (prompts) | `src/qnagym/contracts/prompts.py` | `tests/contracts/test_prompts_contract.py` |
| `docs/spec/questions.md` | `spec.md#questions` | `src/qnagym/contracts/questions.py` | `tests/contracts/test_questions_contract.py` |
| `docs/spec/session.md` | `spec.md#session-json` | `src/qnagym/contracts/session.py` | `tests/contracts/test_session_schema.py` |
| `spec.md#constants` | `src/qnagym/contracts/constants.py` | `tests/contracts/test_constants.py` |

## How to use

When a spec section changes:
1. Find the row for that section.
2. Update the code and tests in the same row.
3. Run `pytest` to verify.

## Maintenance

Keep this matrix in sync with `docs/spec/*.md` and `src/qnagym/`. No orphaned spec sections; every contract file in `docs/spec/` has at least one corresponding test in `tests/contracts/`.

## ADR Traceability

Rows below are **future work**, not implemented contracts. Their `Code (future)` and `Tests (future)` cells are `—` until the ADR is implemented, and `scripts/check_traceability.py` does not validate them: it reads only the `Contract | Spec section | Code | Tests` table above.

| ADR | Spec sections | Code (future) | Tests (future) |
|---|---|---|---|
| ADR 0001 | `spec.md` (SDD principles) | — | — |
| ADR 0002 | `spec.md` (architecture) | — | — |
| ADR 0003 | `spec.md` (workflow model) | `src/qnagym/contracts/issue_process.py`, `src/qnagym/contracts/event_process.py`, `src/qnagym/contracts/local_sync.py`, `src/qnagym/contracts/retry_authorization.py`, `src/qnagym/domain/issue_process.py`, `src/qnagym/domain/event_process.py`, `src/qnagym/domain/local_sync.py`, `src/qnagym/domain/retry_authorization.py`, `src/qnagym/services/issue_process.py`, `src/qnagym/services/event_process.py`, `src/qnagym/services/local_sync.py`, `src/qnagym/services/retry_authorization.py` | `tests/unit/contracts/test_issue_process.py`, `tests/unit/contracts/test_event_process.py`, `tests/unit/contracts/test_local_sync.py`, `tests/unit/contracts/test_retry_authorization.py`, `tests/unit/domain/test_issue_process_domain.py`, `tests/unit/domain/test_event_process_domain.py`, `tests/unit/domain/test_local_sync_domain.py`, `tests/unit/domain/test_retry_authorization_domain.py`, `tests/unit/services/test_issue_process_service.py`, `tests/unit/services/test_event_process_service.py`, `tests/unit/services/test_retry_authorization_service.py` |
| ADR 0004 | `spec.md` (worker/task model) | `src/qnagym/contracts/task_model.py`, `src/qnagym/domain/task_queue.py`, `src/qnagym/services/task_queue.py` | `tests/unit/contracts/test_task_model.py`, `tests/unit/domain/test_task_queue.py`, `tests/unit/services/test_task_queue_service.py` |
| ADR 0005 | `spec.md` (issue process) | `src/qnagym/contracts/issue_process.py`, `src/qnagym/domain/issue_process.py`, `src/qnagym/services/issue_process.py` | `tests/unit/contracts/test_issue_process.py`, `tests/unit/domain/test_issue_process_domain.py`, `tests/unit/services/test_issue_process_service.py` |
| ADR 0006 | `spec.md` (PR process) | `src/qnagym/contracts/pr_process.py`, `src/qnagym/domain/pr_feedback.py`, `src/qnagym/domain/pr_checks.py`, `src/qnagym/domain/pr_lifecycle.py`, `src/qnagym/domain/pr_notifications.py`, `src/qnagym/domain/pr_trust.py`, `src/qnagym/services/pr_feedback.py`, `src/qnagym/services/pr_checks.py`, `src/qnagym/services/pr_lifecycle.py`, `src/qnagym/services/pr_notifications.py`, `src/qnagym/services/pr_trust.py` | `tests/contracts/test_pr_process_contract.py`, `tests/unit/services/test_pr_feedback.py`, `tests/unit/services/test_pr_checks.py`, `tests/unit/services/test_pr_lifecycle.py`, `tests/unit/services/test_pr_notifications.py`, `tests/unit/services/test_pr_trust.py` |
| ADR 0007 | `spec.md` (SDD process) | `src/qnagym/contracts/sdd_process.py`, `src/qnagym/domain/sdd_process.py`, `src/qnagym/services/sdd_process.py` | `tests/unit/contracts/test_sdd_process.py`, `tests/unit/domain/test_sdd_process_domain.py`, `tests/unit/services/test_sdd_process_service.py` |
