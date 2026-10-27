# Config Contract

Source: [`docs/spec.md`](spec.md#config)

## Contract

### Config Keys

| Key | Type | Description | Default |
|---|---|---|---|
| `base_url` | string | OpenAI-compatible API base URL | See [`DEFAULT_BASE_URL`](../src/qnagym/contracts/constants.py) |
| `model` | string | Model name | See [`DEFAULT_MODEL`](../src/qnagym/contracts/constants.py) |
| `api_key` | string | API key (optional for local) | See [`DEFAULT_API_KEY`](../src/qnagym/contracts/constants.py) |
| `data_dir` | string | Session data directory | See [`DEFAULT_DATA_DIR`](../src/qnagym/contracts/constants.py) |
| `temperature` | float | Model temperature (0.0-2.0) | See [`DEFAULT_TEMPERATURE`](../src/qnagym/contracts/constants.py) |
| `max_tokens` | integer | Max tokens per response | See [`DEFAULT_MAX_TOKENS`](../src/qnagym/contracts/constants.py) |
| `timeout` | integer | Request timeout in seconds | See [`DEFAULT_TIMEOUT`](../src/qnagym/contracts/constants.py) |

> All default values are defined in [`src/qnagym/contracts/constants.py`](../src/qnagym/contracts/constants.py).

### Precedence (Highest to Lowest)

1. **CLI flag** (e.g., `--model`, `--base-url`)
2. **Environment variable** (e.g., `QNAGYM_MODEL`, `QNAGYM_BASE_URL`)
3. **TOML config file** (explicit via `--config` or auto-discovered)
4. **Hard-coded default** (see table above)

### Environment Variables

| Variable | Config Key |
|---|---|
| `QNAGYM_BASE_URL` | `base_url` |
| `QNAGYM_MODEL` | `model` |
| `QNAGYM_API_KEY` | `api_key` |
| `QNAGYM_DATA_DIR` | `data_dir` |
| `QNAGYM_TEMPERATURE` | `temperature` |
| `QNAGYM_MAX_TOKENS` | `max_tokens` |
| `QNAGYM_TIMEOUT` | `timeout` |
| `QNAGYM_CONFIG` | Explicit config file path |

### TOML Config File Locations (Auto-discovery Order)

1. `./qnagym.toml` (project local)
2. `$XDG_CONFIG_HOME/qnagym/config.toml` (e.g., `~/.config/qnagym/config.toml`)
3. `~/.config/qnagym/config.toml` (fallback)

### TOML Format Example

```toml
# Example config - actual defaults defined in src/qnagym/contracts/constants.py
base_url = "http://127.0.0.1:11434/v1"  # DEFAULT_BASE_URL
model = "gemma3:12b"                    # DEFAULT_MODEL
api_key = "ollama"                      # DEFAULT_API_KEY
data_dir = "./data/sessions"            # DEFAULT_DATA_DIR
temperature = 0.0                       # DEFAULT_TEMPERATURE
max_tokens = 4096                       # DEFAULT_MAX_TOKENS
timeout = 60                            # DEFAULT_TIMEOUT
```

> **Note:** The TOML example above shows literal values for illustration with constant references as comments. Actual defaults are defined in [`src/qnagym/contracts/constants.py`](../src/qnagym/contracts/constants.py).

### No-Cost AI Config Rules

- **Default model MUST be local** (Ollama/LM Studio compatible)
- **Paid APIs MUST NOT be defaults** — only allowed via explicit env/TOML override
- **Free-tier cloud endpoints** (e.g., NVIDIA Build) allowed as optional override
- **Temperature default 0.0** for reproducibility
- **Structured output required** — all model calls use `response_format=json_object`

### Validation Rules

- `base_url` must be valid HTTP/HTTPS URL
- `model` must be non-empty string
- `temperature` must be in range [0, 2.0] (see [`DEFAULT_TEMPERATURE`](../src/qnagym/contracts/constants.py) for default)
- `max_tokens` must be positive integer (see [`DEFAULT_MAX_TOKENS`](../src/qnagym/contracts/constants.py) for default)
- `timeout` must be positive integer (see [`DEFAULT_TIMEOUT`](../src/qnagym/contracts/constants.py) for default)
- `data_dir` must be valid path (created if not exists)
