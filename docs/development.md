# Development

Developer-only notes. End users start at [`README.md`](../README.md).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Development and testing was done on a Mac Air M4 with 16GB RAM.

## Tests

```bash
pytest   # mocked HTTP; no live model
```

See [`docs/testing.md`](testing.md) for complete testing standards (organization, mocking, coverage, naming, failure paths).

## Spec-first change workflow

Per [`docs/constitution.md`](constitution.md) principle 5 ("Spec before code"): write or update the spec contract that covers the task before implementation.

Per rule **D6** (dedicated branches): every modification must be done in a dedicated branch; no direct commits to `main`.

1. **Create a dedicated branch** — `git checkout -b <type>/<short-description>` from `main` (e.g. `feat/...`, `fix/...`, `chore/...`, `docs/...`).
2. **Update the spec** — modify the relevant `docs/spec/*.md` contract section.
3. **Update the contract** — modify `src/qnagym/contracts/*.py` if the data shape changed.
4. **Update tests** — add/modify `tests/contracts/` and `tests/unit/` to verify the new contract.
5. **Implement** — change application code (`cli.py`, `flow.py`, etc.) to satisfy the contract and tests.
6. **Run tests** — `pytest` (mocked HTTP, no live model).
7. **Open a PR** — merge via pull request, never push directly to `main`.

See [`docs/spec/traceability.md`](spec/traceability.md) for how to map a spec section to code and tests.

## Models used for development

Not for end users. Used to write and review these docs and for local agent tooling.

| Model | Endpoint | Use |
|---|---|---|
| `qwen3.5:4b` | See [`DEFAULT_BASE_URL`](../src/qnagym/contracts/constants.py) (Ollama) | Local model for VS Code Copilot integration; fast, low resource. Used for development only; **not used to run qnagym**. |
| `nemotron-3.5-super-vl-120b-a12b` | `https://build.nvidia.com/nvidia/nemotron-3.5-super-vl-120b-a12b` | **Recommended** for documentation review: handles larger codebases reliably. Free-tier cloud alternative for development. |

Standard-use models are listed in [`docs/spec/prompts.md`](spec/prompts.md).

## AI / Provider Policy

See [`docs/ai_provider_policy.md`](ai_provider_policy.md) for complete standards on:
- Provider configuration (single config source, precedence, validation)
- Standard-use vs development-only models
- Model pinning, reproducibility (temperature, seed)
- Timeouts, retries, structured output validation
- Prompt management (versioned, reviewed like code)
- Privacy & data handling (what leaves local machine)
- Model drift monitoring
- Prompt injection mitigations
