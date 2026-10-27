"""Constants & Config Keys (immutable values, error codes).

Mirrors docs/spec/cli.md, docs/spec/config.md, docs/spec/questions.md,
docs/spec/prompts.md, docs/spec/flow.md.
"""

from __future__ import annotations

from pathlib import Path

# --- CLI constants (from docs/spec/cli.md) ---

VALID_STATUSES = {"prepared", "confirmed", "drilling", "evaluated"}

EXIT_CODE_SUCCESS = 0
EXIT_CODE_MODEL_ERROR = 1
EXIT_CODE_FLOW_ERROR = 2
EXIT_CODE_CONFIG_ERROR = 3
EXIT_CODE_INPUT_ERROR = 4

# Question count formula: max(3, min(15, round(duration_minutes / 6)))
# Fallback (no duration): 5 questions
# See docs/spec/questions.md for full contract
FALLBACK_COUNT = 5
QUESTION_COUNT_MIN = 3
QUESTION_COUNT_MAX = 15
MINUTES_PER_QUESTION = 6

# Vague material threshold: 20 chars (see docs/spec/questions.md)
MIN_MATERIAL_CHARS = 20

# Clarifying questions (see docs/spec/questions.md)
CLARIFYING_QUESTIONS = [
    "What specific topic or subject do you want to learn about?",
    "What is the scope or focus area (e.g., basics, advanced, specific aspect)?",
    "What is your current knowledge level (beginner, intermediate, advanced)?",
]

# Display rules (see docs/spec/session.md)
CONFIDENCE_SHOW_BELOW = 0.95
ALTERNATIVE_DELTA = 0.05

# Progress tracking (see docs/spec/flow.md)
BREAK_SUGGEST_THRESHOLD_ATTEMPTS = 2
BREAK_SUGGEST_THRESHOLD_SCORE = 0.3


# --- Config constants (from docs/spec/config.md) ---

DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL = "gemma3:12b"
DEFAULT_API_KEY = "ollama"
DEFAULT_DATA_DIR = Path("data/sessions")
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TIMEOUT = 60

# Precedence (highest to lowest):
# 1. CLI flag
# 2. Environment variable
# 3. TOML file
# 4. Hard-coded default

ENV_BASE_URL = "QNAGYM_BASE_URL"
ENV_MODEL = "QNAGYM_MODEL"
ENV_API_KEY = "QNAGYM_API_KEY"
ENV_DATA_DIR = "QNAGYM_DATA_DIR"
ENV_TEMPERATURE = "QNAGYM_TEMPERATURE"
ENV_MAX_TOKENS = "QNAGYM_MAX_TOKENS"
ENV_TIMEOUT = "QNAGYM_TIMEOUT"
ENV_CONFIG = "QNAGYM_CONFIG"

TOML_LOCAL = Path("qnagym.toml")
XDG_CONFIG_HOME = "XDG_CONFIG_HOME"
TOML_XDG = Path("qnagym") / "config.toml"
TOML_HOME = Path.home() / ".config" / "qnagym" / "config.toml"

CONFIG_KEYS = ["base_url", "model", "api_key", "data_dir", "temperature", "max_tokens", "timeout"]

DEFAULTS = {
    "base_url": DEFAULT_BASE_URL,
    "model": DEFAULT_MODEL,
    "api_key": DEFAULT_API_KEY,
    "data_dir": DEFAULT_DATA_DIR,
    "temperature": DEFAULT_TEMPERATURE,
    "max_tokens": DEFAULT_MAX_TOKENS,
    "timeout": DEFAULT_TIMEOUT,
}

ENV_MAP = {
    "base_url": ENV_BASE_URL,
    "model": ENV_MODEL,
    "api_key": ENV_API_KEY,
    "data_dir": ENV_DATA_DIR,
    "temperature": ENV_TEMPERATURE,
    "max_tokens": ENV_MAX_TOKENS,
    "timeout": ENV_TIMEOUT,
}


# --- Prompt constants (from docs/spec/prompts.md) ---

# Standard-use models (end users) - see docs/spec/prompts.md
STANDARD_USE_MODELS = {
    "gemma3:12b": "Default. Balanced for question generation, refinement, and evaluation.",
    "llama3.2": "General knowledge topics (science, history, literature).",
    "nemotron-3.5-super-vl-120b-a12b": "Free-tier cloud alternative via NVIDIA Build.",
}

# Models to avoid
AVOID_MODELS = {
    "gemma4:12b": "Structured output is unavailable.",
    "gemma4:12b-mlx": "Structured output is unavailable.",
}

# System prompts (see docs/spec/prompts.md)
GENERATE_SYSTEM = (
    "Return JSON only. Knowledge coach. "
    "If material is too vague (no clear topic or scope), "
    '{"ok":false,"questions":["clarifying question",...]}. '
    "Never invent a topic. "
    'Else {"ok":true,"questions":[{"prompt":"...","model_answer":"..."}]}.'
)

REFINE_SYSTEM = (
    "Return JSON only. Refine Q&A based on user comments. "
    '{"ok":true,"questions":[{"id":"q1","prompt":"...","model_answer":"..."}]}.'
)

EVALUATE_SYSTEM = (
    "Return JSON only. Score each user answer 0-1 vs agreed answer and material. "
    "Self-reported confidence 0-1. Include covered/missed points and close alternatives. "
    '{"evaluations":[{"id":"q1","score":0,"confidence":0,"feedback":"...","covered_points":[],"missed_points":[],"alternatives":[{"summary":"...","score":0}]}],"next_steps":["..."]}.'
)

# Vague material threshold (see docs/spec/questions.md)
# MIN_MATERIAL_CHARS = 20  # defined above

# Clarifying questions (see docs/spec/questions.md)
# CLARIFYING_QUESTIONS = [...]  # defined above


# --- Flow constants (from docs/spec/flow.md) ---

# State machine (see docs/spec/flow.md)
# VALID_STATUSES = {...}  # defined above

ALLOWED_TRANSITIONS = {
    "prepared": {"prepared", "confirmed"},
    "confirmed": {"drilling"},
    "drilling": {"evaluated", "confirmed", "prepared"},
    "evaluated": {"confirmed", "prepared"},
}
