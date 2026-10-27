# Traceability Matrix

Maps spec sections → code symbols → tests.

| Spec section | Code | Tests |
|---|---|---|
| `spec.md#cli` | `src/qnagym/adapters/cli.py`, `src/qnagym/services/generate.py`, `src/qnagym/services/refine.py`, `src/qnagym/services/confirm.py`, `src/qnagym/services/drill.py`, `src/qnagym/services/evaluate.py`, `src/qnagym/services/progress.py` | `tests/unit/adapters/test_cli.py`, `tests/unit/services/test_generate.py`, `tests/unit/services/test_refine.py`, `tests/unit/services/test_confirm.py`, `tests/unit/services/test_drill.py`, `tests/unit/services/test_evaluate.py`, `tests/unit/services/test_progress.py` |
| `spec.md#cli` (drill --interactive) | `src/qnagym/services/drill.py:_drill_interactive`, `src/qnagym/adapters/cli.py` | `tests/unit/services/test_drill.py::test_drill_interactive_*` |
| `spec.md#session-json` | `src/qnagym/contracts/types.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/session.py` | `tests/contracts/test_types.py`, `tests/contracts/test_validation.py`, `tests/contracts/test_session_schema.py` |
| `spec.md#config` | `src/qnagym/adapters/config.py`, `src/qnagym/contracts/constants.py`, `src/qnagym/contracts/config.py` | `tests/unit/adapters/test_config.py`, `tests/contracts/test_constants.py`, `tests/contracts/test_config_contract.py` |
| `spec.md#flow` | `src/qnagym/domain/flow.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/flow.py` | `tests/unit/domain/test_flow.py`, `tests/contracts/test_validation.py`, `tests/contracts/test_flow_contract.py` |
| `spec.md#models` (prompts) | `src/qnagym/domain/scoring.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/prompts.py` | `tests/unit/domain/test_scoring.py`, `tests/contracts/test_validation.py`, `tests/contracts/test_prompts_contract.py` |
| `spec.md#questions` | `src/qnagym/domain/questions.py`, `src/qnagym/contracts/validation.py`, `src/qnagym/contracts/questions.py` | `tests/contracts/test_validation.py`, `tests/contracts/test_questions_contract.py` |
| `spec.md#questions` (vague material) | `src/qnagym/domain/questions.py` | `tests/unit/domain/test_questions.py` |
| `spec.md#flow` (full E2E) | `src/qnagym/domain/flow.py`, `src/qnagym/adapters/cli.py` | `tests/integration/test_e2e_flow.py` |

## Contract Tests (spec → contracts)

| Spec section | Contract module | Contract tests |
|---|---|---|
| `spec.md#cli` | `src/qnagym/contracts/cli.py` | `tests/contracts/test_cli_contract.py` |
| `spec.md#config` | `src/qnagym/contracts/config.py` | `tests/contracts/test_config_contract.py` |
| `spec.md#flow` | `src/qnagym/contracts/flow.py` | `tests/contracts/test_flow_contract.py` |
| `spec.md#models` (prompts) | `src/qnagym/contracts/prompts.py` | `tests/contracts/test_prompts_contract.py` |
| `spec.md#questions` | `src/qnagym/contracts/questions.py` | `tests/contracts/test_questions_contract.py` |
| `spec.md#session-json` | `src/qnagym/contracts/session.py` | `tests/contracts/test_session_schema.py` |
| `spec.md#constants` | `src/qnagym/contracts/constants.py` | `tests/contracts/test_constants.py` |

## How to use

When a spec section changes:
1. Find the row for that section.
2. Update the code and tests in the same row.
3. Run `pytest` to verify.

## Maintenance

Keep this matrix in sync with `docs/spec/*.md` and `src/qnagym/`. No orphaned spec sections; every contract file in `docs/spec/` has at least one corresponding test in `tests/contracts/`.
