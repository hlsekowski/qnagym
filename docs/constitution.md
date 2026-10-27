# Constitution

Non-negotiable principles for qnagym. Product spec lives in `docs/spec.md`.

| ID | Principle | Description | Severity | Enforcement |
|----|-----------|-------------|----------|-------------|
| C1 | **Stop when unclear.** | If the task is underspecified, stop and ask. Do not speculate or implement guessed behavior. | MUST | Review gate: PR template "clarity confirmed" checkbox |
| C2 | **Token budget.** | Keep product prompts, repo docs, and agent context short. Prefer pointers over duplicated text. | SHOULD | Lint: `AGENTS.md ≤ 100 lines`, `README.md ≤ 80 lines`, PR diff ≤ 400 lines |
| C3 | **Cheap AI.** | Default to local OpenAI-compatible models (Ollama, LM Studio). Optional free-tier cloud allowed. Paid APIs not default. | MUST | Config check: default model is local in `src/` config |
| C4 | **Thin providers.** | Talk to models via OpenAI-compatible `base_url` + `model` + optional `api_key`. Vendor extra only if saves days. | MUST | Code review: no vendor SDKs unless justified in ADR |
| C5 | **Spec before code.** | Write/update spec before implementation. No app code until spec exists. | MUST | Traceability check: every spec section has code symbol + test (`scripts/check_traceability.py`) |
| C6 | **Testing.** | All changes require passing tests. Run `pytest` before committing. | MUST | `pytest` passes (mocked HTTP); coverage ≥ 80% |
| C7 | **CI.** | All changes must pass CI pipeline (lint, type-check, tests) before merge. No exceptions. | MUST | GitHub Actions: lint, type-check, tests, security, traceability |
| C8 | **Security.** | No secrets in code or logs. Validate all external input. Least-privilege for external calls. | MUST | `gitleaks` + `bandit`; secret scan; input validation |
| C9 | **Dependencies.** | Minimize external dependencies. Pin versions. Audit for vulnerabilities before adding. | MUST | Lockfile exists; `pip-audit` clean; license check |
| C10 | **Observability.** | Structured logging for all I/O boundaries. Trace IDs for request flows. Metrics for latency and errors. | SHOULD | Log schema defined; trace IDs propagated; PII redacted |

> **Agent & development rules:** See [`docs/rules.md`](rules.md) for A1–A4 (agent) and D1–D5 (development).
> **Exception process:** See `docs/rules.md`.
