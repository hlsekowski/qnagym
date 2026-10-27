"""CLI contract module.

Mirrors docs/spec/cli.md.
"""

from __future__ import annotations

COMMANDS = {
    "generate": "Generate Q&A from material",
    "refine": "Refine Q&A via comments",
    "confirm": "Confirm Q&A bank for practice",
    "drill": "Practice: hide answers, ask questions",
    "evaluate": "Score answers vs agreed answers",
    "repeat": "Repeat practice session",
    "reset": "Reset to prepared state for refinement",
    "list": "List saved sessions",
    "show": "Show session details",
}

GLOBAL_FLAGS = {
    "base_url": "OpenAI-compatible base URL",
    "model": "Model name",
    "api_key": "API key",
    "data_dir": "Session data directory",
    "config": "Explicit TOML config file",
    "json": "Output JSON instead of human-readable",
}

EXIT_CODES = {
    "success": 0,
    "model_error": 1,
    "flow_error": 2,
    "config_error": 3,
    "input_error": 4,
}

BEHAVIOR_RULES = [
    "generate: Creates session in 'prepared' state. If material too vague, "
    "stops with clarifying questions (exit 4).",
    "refine: Requires session in 'prepared' state. Shows Q&A, accepts comments "
    "to refine specific questions. Stays in 'prepared' state.",
    "confirm: Requires session in 'prepared' state. Transitions to 'confirmed' "
    "state. Locks Q&A for practice.",
    "drill: Requires session in 'confirmed' state. Transitions to 'drilling' "
    "state. Hides answers, asks one question at a time, records user answers.",
    "evaluate: Requires session in 'drilling' state with all questions "
    "answered. Transitions to 'evaluated' state. Scores answers, gives "
    "feedback, suggests next steps.",
    "repeat: Requires session in 'evaluated' state. Transitions to 'confirmed' "
    "state. Clears user answers and evaluations, preserves progress history. "
    "Suggests break if not improving.",
    "reset: Requires session in 'drilling' or 'evaluated' state. Transitions "
    "to 'prepared' state. Clears user answers, evaluations, next_steps.",
    "list: Shows recent sessions with status, question count, material preview.",
    "show: Displays full session details (questions, answers, evaluations, progress).",
]
