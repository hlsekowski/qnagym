# AI Provider Policy

Standards for AI model usage, provider configuration, and privacy in qnagym.

## Provider Configuration

### Single Config Source
All model configuration comes from a single `Config` object (see `docs/spec/config.md`). No hardcoded endpoints or model names in application code.

### Precedence (Highest to Lowest)
1. CLI flags (`--base-url`, `--model`, `--api-key`)
2. Environment variables (`QNAGYM_BASE_URL`, `QNAGYM_MODEL`, `QNAGYM_API_KEY`)
3. TOML config file (`qnagym.toml`, `~/.config/qnagym/config.toml`)
4. Hard-coded defaults (local Ollama)

### Validation
- `base_url` must be valid HTTP/HTTPS URL
- `model` must be non-empty
- `temperature` in [0.0, 2.0] (default: see [`DEFAULT_TEMPERATURE`](../src/qnagym/contracts/constants.py))
- `max_tokens` positive integer (default: see [`DEFAULT_MAX_TOKENS`](../src/qnagym/contracts/constants.py))
- `timeout` positive integer (default: see [`DEFAULT_TIMEOUT`](../src/qnagym/contracts/constants.py))

## Standard-use vs Development-only Models

### Standard-use Models (End Users)
Listed in `docs/spec/prompts.md`. Local-first, optional free-tier cloud.

| Model | Notes |
|---|---|
| `gemma3:12b` | Default. Balanced for generation, refinement, evaluation. |
| `llama3.2` | General knowledge topics. |
| `nemotron-3.5-super-vl-120b-a12b` | Free-tier cloud via NVIDIA Build. |

### Development-only Models
Listed in `docs/development.md`. For docs/tooling only, not for running qnagym.

## Model Pinning & Reproducibility

- **Temperature default: 0.0** — deterministic outputs
- **Seed**: Not exposed (model-dependent); document if needed
- **Model version**: Pin specific tags (e.g., `gemma3:12b` not `gemma3:latest`)

## Structured Output

All model calls **MUST** use `response_format={"type": "json_object"}` (OpenAI-compatible).

Response schemas defined in `docs/spec/prompts.md`:
- Generate: `{"ok": bool, "questions": [...]}`
- Refine: `{"ok": bool, "questions": [...]}`
- Evaluate: `{"evaluations": [...], "next_steps": [...]}`

Client validates JSON parsing and schema compliance in-process.

## Timeouts & Retries

- **Default timeout**: 60 seconds (configurable)
- **Retries**: None by default (fail fast for debugging)
- **Circuit breaker**: Not implemented (simple CLI)

## Prompt Management

- Prompts live in `src/qnagym/contracts/constants.py` as constants
- System prompts versioned with code (git history)
- Prompts reviewed like code (PR review)
- No external prompt files or templates

## Privacy & Data Handling

### What Leaves Local Machine
- **Local models (Ollama/LM Studio)**: Nothing leaves machine
- **Free-tier cloud (NVIDIA Build)**: Only the prompt + material + Q&A sent
- **Paid APIs**: Not default; only if explicitly configured

### Data Minimization
- Only send material, questions, and answers needed for the task
- No user identifiers, session IDs, or metadata sent to model
- No telemetry/analytics sent to model providers

### Session Storage
- Sessions stored locally as JSON (see [`DEFAULT_DATA_DIR`](../src/qnagym/contracts/constants.py))
- Owner-only permissions (0600)
- No automatic cloud sync

## Model Drift Monitoring

- Track evaluation score consistency over time
- Alert if average score drops > 10% over 10 sessions
- Log model version with each session for correlation

## Prompt Injection Mitigations

- System prompts are fixed constants (not user-controllable)
- User input (material, comments) goes in user messages only
- JSON response format limits injection surface
- Validate all model responses against expected schema

## No-Cost AI Rules (Enforced)

| Rule | Enforcement |
|---|---|
| Default model is local | Config default points to Ollama |
| No paid APIs in defaults | Only local/free-tier in `STANDARD_USE_MODELS` |
| No vendor SDKs | Only `openai` SDK in dependencies |
| Structured JSON output | All calls use `response_format=json_object` |
| Temperature=0 default | Config default; documented in spec |
| Prompts versioned | In `constants.py` with git history |
| No PII to cloud | Local-first; anonymized if cloud used |
| Drift monitoring | Track evaluation consistency |

---

## Related Files

- `docs/spec/config.md` — Config contract
- `docs/spec/prompts.md` — Prompt contracts
- `docs/constitution.md` — Principles C3, C4
- `docs/rules.md` — Rules NC1–NC8
- `src/qnagym/adapters/config.py` — Config loading
- `src/qnagym/adapters/client.py` — Model client
- `src/qnagym/contracts/constants.py` — Model constants
