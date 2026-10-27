# Prompt Contract

Source: [`docs/spec.md`](spec.md#models)

## Contract

Chat completions + JSON object responses. Fields: questions, answers, scores, `confidence`, `alternatives`, `covered_points`, `missed_points`.

Prompts stay short (token budget). No coding judge.

## Model Contracts

### Standard-use Models (End Users)

For end users running the CLI. Local first, optional free-tier cloud.

| Model | Notes |
|---|---|
| `gemma3:12b` | Default. Balanced for question generation, refinement, and evaluation. |
| `llama3.2` | General knowledge topics (science, history, literature). |
| `nemotron-3.5-super-vl-120b-a12b` | Free-tier cloud alternative via NVIDIA Build. |

Avoid `gemma4:12b` and `gemma4:12b-mlx`: structured output is unavailable.

### Development-only Models

Not for end users. Used to write and review these docs and for local agent tooling. Listed in [`docs/development.md`](development.md#models-used-for-development).

## JSON Response Contracts

### Generate Response

```json
{
  "ok": true,
  "questions": [
    { "prompt": "string", "model_answer": "string" }
  ]
}
```

If the material is too vague:

```json
{
  "ok": false,
  "questions": ["clarifying question", "..."]
}
```

### Refine Response

```json
{
  "ok": true,
  "questions": [
    { "id": "q1", "prompt": "string", "model_answer": "string" }
  ]
}
```

### Evaluate Response

```json
{
  "evaluations": [
    {
      "id": "q1",
      "score": 0.0-1.0,
      "confidence": 0.0-1.0,
      "feedback": "string",
      "covered_points": ["string"],
      "missed_points": ["string"],
      "alternatives": [
        { "summary": "string", "score": 0.0-1.0 }
      ]
    }
  ],
  "next_steps": ["string"]
}
```

### Error Response (Model Failures)

When the model returns an error (HTTP 5xx, timeout, malformed JSON, invalid schema), the client wraps it as:

```json
{
  "error": {
    "type": "model_error|timeout|invalid_response|schema_error",
    "message": "string",
    "details": {}
  }
}
```

The CLI maps this to exit code 1 (`EXIT_CODE_MODEL_ERROR`).

## System Prompts

### Generate System Prompt

```
Return JSON only. Knowledge coach.
If material is too vague (no clear topic or scope),
{"ok":false,"questions":["clarifying question",...]}.
Never invent a topic.
Else {"ok":true,"questions":[{"prompt":"...","model_answer":"..."}]}.
```

### Refine System Prompt

```
Return JSON only. Refine Q&A based on user comments.
{"ok":true,"questions":[{"id":"q1","prompt":"...","model_answer":"..."}]}.
```

### Evaluate System Prompt

```
Return JSON only. Score each user answer 0-1 vs agreed answer and material.
Self-reported confidence 0-1. Include covered/missed points and close alternatives.
{"evaluations":[{"id":"q1","score":0,"confidence":0,"feedback":"...","covered_points":[],"missed_points":[],"alternatives":[{"summary":"...","score":0}]}],"next_steps":["..."]}.
```

## Model Parameters

| Parameter | Value | Source |
|---|---|---|
| `temperature` | See [`DEFAULT_TEMPERATURE`](../src/qnagym/contracts/constants.py) | [`docs/spec/config.md`](config.md) |
| `response_format` | `json_object` | Required for structured output |
| `max_tokens` | See [`DEFAULT_MAX_TOKENS`](../src/qnagym/contracts/constants.py) | [`docs/spec/config.md`](config.md) |
| `timeout` | See [`DEFAULT_TIMEOUT`](../src/qnagym/contracts/constants.py) | [`docs/spec/config.md`](config.md) |
