# CLI Contract

Source: [`docs/spec.md`](spec.md#cli)

## Contract

### Commands

| Command | Description | Key Flags |
|---|---|---|
| `qnagym generate` | Generate Q&A from material | `--material`, `--questions`, `--duration`, `--output` |
| `qnagym refine` | Iteratively refine Q&A via comments | `--session`, `--comment`, `--question-id` |
| `qnagym confirm` | Confirm/lock Q&A bank for practice | `--session` |
| `qnagym drill` | Practice: hide answers, ask questions | `--session`, `--question-id`, `--answer`, `--interactive` |
| `qnagym evaluate` | Score answers vs agreed answers | `--session` |
| `qnagym repeat` | Reset for another round, track progress | `--session` |
| `qnagym list` | List saved sessions | `--limit` |
| `qnagym show` | Show session details | `--session` |

### Global Flags

| Flag | Description | Default |
|---|---|---|
| `--base-url` | OpenAI-compatible base URL | See [`DEFAULT_BASE_URL`](../src/qnagym/contracts/constants.py) |
| `--model` | Model name | See [`DEFAULT_MODEL`](../src/qnagym/contracts/constants.py) |
| `--api-key` | API key (optional) | See [`DEFAULT_API_KEY`](../src/qnagym/contracts/constants.py) |
| `--data-dir` | Session data directory | See [`DEFAULT_DATA_DIR`](../src/qnagym/contracts/constants.py) |
| `--config` | Explicit TOML config file | Auto-discover |
| `--json` | Output JSON instead of human-readable | `false` |
| `--interactive` | Run interactive drill session (drill command) | `false` |
| `--help` | Show help | - |

> Default values are defined in [`src/qnagym/contracts/constants.py`](../src/qnagym/contracts/constants.py) and [`docs/spec/config.md`](config.md).

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Model error (HTTP 5xx, timeout, malformed JSON, invalid schema) |
| 2 | Flow error (invalid transition, guard violation) |
| 3 | Config error (invalid config, missing required) |
| 4 | Input error (vague material, invalid args) |

### Behavior Rules

1. **generate**: Reads material, generates Q&A bank, saves session in `prepared` state. If material too vague, stops with clarifying questions (exit 4).
2. **refine**: Requires session in `prepared` state. Shows Q&A, accepts comments to refine specific questions. Can be run multiple times. Stays in `prepared` state.
3. **confirm**: Requires session in `prepared` state. Transitions to `confirmed` state. Locks Q&A for practice.
4. **drill**: Requires session in `confirmed` state. Transitions to `drilling` state. Hides answers, asks one question at a time, records user answers.
5. **evaluate**: Requires session in `drilling` state with all questions answered. Transitions to `evaluated` state. Scores answers, gives feedback, suggests next steps.
6. **repeat**: Requires session in `evaluated` state. Transitions to `confirmed` state. Clears user answers and evaluations, preserves progress history. Suggests break if not improving.
7. **list**: Shows recent sessions with status, question count, material preview.
8. **show**: Displays full session details (questions, answers, evaluations, progress).

### Output Format

- Human-readable by default (colors, progress indicators)
- `--json` flag outputs structured JSON for scripting
- Errors to stderr, success to stdout
