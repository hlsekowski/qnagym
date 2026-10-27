# ADR 0001: Spec-driven development

## Status

Accepted

## Context

qnagym is a Python CLI for knowledge acquisition practice. The product spec lives in `docs/spec.md` and the non-negotiable principles live in `docs/constitution.md`. Principle 5 states: "Spec before code. Write or update the spec that covers the task before implementation."

This project adopts spec-driven development (SDD) from the start, following the proven architecture from interview-gym.

## Decision

Adopt spec-driven development (SDD) as the project's architectural decision:

1. **Decompose the spec into domain contracts** under `docs/spec/` (cli, session, config, flow, prompts, traceability). Each contract file has an explicit **Contract** section that code and tests must conform to. `docs/spec.md` becomes an index linking to these contracts.

2. **Add a contracts layer in code** under `src/qnagym/contracts/`. Each module mirrors a `docs/spec/*.md` contract and defines the canonical data shapes and validation rules that application code must conform to.

3. **Organize tests by spec traceability** under `tests/unit/`, `tests/contracts/`, and `tests/integration/`. Each test file header cites the spec section it verifies. Every contract file in `docs/spec/` has at least one corresponding test in `tests/contracts/`.

4. **Maintain a traceability matrix** in `docs/spec/traceability.md` mapping spec section → code symbol → test file.

5. **Follow a spec-first change workflow** (documented in `docs/development.md`):
   - Update the spec contract.
   - Update the code contract if the data shape changed.
   - Update tests to verify the new contract.
   - Implement application code to satisfy the contract and tests.
   - Run `pytest` (mocked HTTP, no live model).

## Consequences

### Positive

- Every code change starts from a spec contract (constitution principle 5).
- Traceability from spec section → code → test makes impact of spec changes obvious.
- Contracts layer centralizes data shape definitions, reducing drift between spec and implementation.
- Contract tests catch spec violations early.

### Negative

- More files and indirection (contracts layer between domain models and spec).
- Requires discipline to keep the traceability matrix in sync.

## Related

- [`docs/constitution.md`](constitution.md) — principle 5: "Spec before code"
- [`docs/spec.md`](spec.md) — v1 product spec (index to contracts)
- [`docs/spec/traceability.md`](spec/traceability.md) — spec → code → test mapping
- [`docs/development.md`](development.md) — spec-first change workflow
