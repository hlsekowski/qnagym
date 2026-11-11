# Agent instructions

qnagym is a Python CLI for knowledge-acquisition practice; the product spec lives in `docs/spec.md`.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"     # setup
pytest                      # tests (mocked HTTP, no live model)
ruff check . && ruff format --check .   # lint
python3 -m mypy src/qnagym              # type-check
python3 scripts/check_traceability.py   # doc checks
python3 scripts/check_doc_defaults.py
python3 scripts/check_doc_links.py
```

## Routing

| When | Read |
|---|---|
| changing product behaviour or a data shape | [`docs/spec.md`](docs/spec.md), then the contract in `docs/spec/` |
| adding or changing a rule, default or threshold | [`docs/rules.md`](docs/rules.md) |
| starting any change (branch, spec-first order, PR) | [`docs/development.md`](docs/development.md) |
| mapping a spec section to code and tests | [`docs/spec/traceability.md`](docs/spec/traceability.md) |
| writing or reviewing tests | [`docs/testing.md`](docs/testing.md) |
| choosing or configuring a model | [`docs/spec/prompts.md`](docs/spec/prompts.md), [`docs/ai_provider_policy.md`](docs/ai_provider_policy.md) |
| asking why a decision was made | the ADR in [`docs/adr/`](docs/adr/) |
| recording a rule exception | [`docs/exceptions.md`](docs/exceptions.md) |

Principles C1–C10 live in [`docs/constitution.md`](docs/constitution.md); agent and development rules A1–A4, D1–D6 live in [`docs/rules.md`](docs/rules.md).
