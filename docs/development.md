# Development

> **Purpose:** Developer-only notes: environment setup, the commands to run, and the development-only model list.
> **Read when:** setting up the repo, running checks, or choosing a development model.
> **Owns:** the local setup commands, the development-only model list, and the pointer to the AI provider policy. The workflow sequence is owned by [`docs/workflow.md`](workflow.md).

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

The spec-first workflow sequence is owned by the workflow hub: [`docs/workflow.md`](workflow.md).

The AI workflow's PR Process (feedback evaluation, check monitoring, corrections, lifecycle) is defined in [ADR 0006](adr/0006-pr-process.md).

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
