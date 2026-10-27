# Testing Standards

This document defines the testing standards for qnagym. All tests must follow these conventions.

## Test Organization

```
tests/
├── unit/                    # Unit tests (fast, isolated, mocked)
│   ├── adapters/            # Adapter tests (CLI, config, client, display, session_store)
│   ├── domain/              # Domain logic tests (flow, scoring, session, questions)
│   ├── services/            # Service tests (generate, refine, confirm, drill, evaluate, progress)
│   ├── test_*.py            # Cross-cutting unit tests
│   └── conftest.py          # Shared fixtures
├── contracts/               # Contract tests (spec → code validation)
│   ├── test_*_contract.py   # Contract compliance tests
│   └── test_*_schema.py     # Schema validation tests
├── integration/             # Integration tests (E2E flows)
│   └── test_e2e_flow.py     # Full generate→refine→confirm→drill→evaluate→repeat flow
├── http.py                  # HTTP mocking utilities
└── conftest.py              # Root fixtures
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions/classes in isolation
- **Dependencies**: Fully mocked (no network, no filesystem, no real models)
- **Speed**: Fast (< 100ms per test)
- **Naming**: `test_<module>_<function>_<scenario>`
- **Coverage target**: ≥ 80% line coverage

### 2. Contract Tests (`tests/contracts/`)
- **Purpose**: Verify code conforms to spec contracts
- **Scope**:
  - Schema validation (session JSON, config, CLI signatures)
  - Business rule validation (question count, vague material, flow transitions)
  - Prompt/response format compliance
- **Dependencies**: Mocked HTTP only
- **Naming**: `test_<contract>_contract.py` or `test_<contract>_schema.py`

### 3. Integration Tests (`tests/integration/`)
- **Purpose**: Test full user flows end-to-end
- **Dependencies**: Mocked HTTP, real filesystem (tmp_path)
- **Speed**: Slower (100-500ms per test)
- **Naming**: `test_e2e_<flow>_<variant>`

## Mocking Standards

### HTTP Mocking
All external HTTP calls must be mocked using `tests/http.py` utilities:

```python
from tests.http import model_client

# In test:
client = model_client({"ok": True, "questions": [...]})
```

### Filesystem
Use `tmp_path` fixture for all filesystem operations:

```python
def test_something(tmp_path):
    jd_path = tmp_path / "jd.txt"
    jd_path.write_text("Job description...")
```

### Time
Use `freezegun` or mock `datetime` for time-dependent tests.

## Test Data

### Fixtures
- Define reusable fixtures in `conftest.py`
- Use factory functions for complex test objects
- Keep fixtures minimal and focused

### Test Data Files
- Store test data in `tests/fixtures/` (create if needed)
- Use JSON/YAML for structured test data
- Never commit real API keys or secrets

## Coverage Requirements

| Metric | Target |
|--------|--------|
| Line coverage | ≥ 80% |
| Branch coverage | ≥ 70% |
| Critical paths (flow, scoring, config) | 100% |

Run coverage:
```bash
pytest --cov=qnagym --cov-report=term-missing --cov-fail-under=80
```

## Failure Path Testing

Every service must test these failure paths:

| Failure Type | Test Required |
|--------------|---------------|
| Model HTTP error (5xx) | ✅ |
| Model timeout | ✅ |
| Malformed JSON response | ✅ |
| Invalid response schema | ✅ |
| Empty response | ✅ |
| Vague material (clarifying questions) | ✅ |
| Flow guard violations | ✅ |
| Config validation errors | ✅ |

## Live Model Tests (Opt-in)

For manual validation only — **never in CI**:

```bash
# Mark with @pytest.mark.live
@pytest.mark.live
def test_with_real_model():
    ...

# Run manually:
pytest -m live
```

Requirements:
- Marked with `@pytest.mark.live`
- Skipped by default in CI
- Require local model running (Ollama/LM Studio)
- Documented in `docs/development.md`

## Test Naming Conventions

| Pattern | Example |
|---------|---------|
| Unit: `test_<module>_<function>_<scenario>` | `test_prepare_service_vague_material` |
| Contract: `test_<contract>_<rule>` | `test_session_schema_status_confirmed_sync` |
| Integration: `test_e2e_<flow>_<variant>` | `test_e2e_full_flow_happy_path` |

## Assertions

- Use `pytest` assertions (native `assert`)
- Use `pytest.raises` for exceptions
- Check exit codes for CLI errors
- Verify side effects (mock calls, file writes)

## CI Integration

Tests run in CI on every PR:
- `pytest` with coverage gate (≥ 80%)
- All test categories run
- Mocked HTTP only (no live model)
- Flaky tests: quarantine with `@pytest.mark.flaky` and fix within 1 week

## Adding New Tests

1. **Identify category**: unit / contract / integration
2. **Find/create test file**: Follow organization above
3. **Add spec reference**: Header comment `# Verifies docs/spec/<file>.md#<section>`
4. **Write test**: Follow naming, mocking, assertion standards
5. **Run locally**: `pytest tests/<path>/test_<name>.py -v`
6. **Verify coverage**: `pytest --cov=qnagym --cov-report=term-missing`

## Example: Adding a Unit Test for `questions.py`

```python
# tests/unit/domain/test_questions.py
# Verifies docs/spec/questions.md#question-count-formula

import pytest
from qnagym.domain.questions import calculate_question_count


class TestQuestionCount:
    def test_question_count_with_duration(self):
        assert calculate_question_count(45) == 8
        assert calculate_question_count(30) == 5
        assert calculate_question_count(90) == 15

    def test_question_count_min_max_bounds(self):
        assert calculate_question_count(0) == 3  # min
        assert calculate_question_count(1000) == 15  # max

    def test_question_count_fallback(self):
        assert calculate_question_count(None) == 5  # fallback
```

---

## Related Files

- `docs/development.md` — Developer setup and workflow
- `docs/spec/traceability.md` — Spec → code → test mapping
- `tests/http.py` — HTTP mocking utilities
- `pyproject.toml` — pytest configuration
