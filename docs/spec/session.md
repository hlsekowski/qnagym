# Session JSON Contract

Source: [`docs/spec.md`](spec.md#session-json)

## Contract

`<data_dir>/<id>.json` (default: see [`DEFAULT_DATA_DIR`](../src/qnagym/contracts/constants.py)):

```json
{
  "id": "uuid",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "status": "prepared|confirmed|drilling|evaluated",
  "material": "string",
  "question_count": 5,
  "context": {
    "duration_minutes": null,
    "difficulty": "medium",
    "language": "en"
```

> **Note:** The default session data directory is defined by [`DEFAULT_DATA_DIR`](../src/qnagym/contracts/constants.py) (default: `data/sessions`). Override with `QNAGYM_DATA_DIR` or `--data-dir`.
  },
  "questions": [
    {
      "id": "q1",
      "prompt": "string",
      "agreed_answer": "string",
      "user_answer": null,
      "evaluation": null,
      "refinement_history": []
    }
  ],
  "progress": {
    "attempts": 0,
    "best_score": 0.0,
    "last_score": 0.0,
    "improving": true,
    "break_suggested": false
  },
  "next_steps": []
}
```

### Field Contracts

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | UUID |
| `created_at` | string | yes | ISO-8601 UTC with timezone offset (e.g., `2024-01-15T10:30:00+00:00`) |
| `updated_at` | string | yes | ISO-8601 UTC with timezone offset, touched on every save |
| `status` | string | yes | `prepared\|confirmed\|drilling\|evaluated`; transitions per [`docs/spec/flow.md`](flow.md#state-machine) |
| `material` | string | yes | The source material/topic/URL provided by user |
| `question_count` | integer | yes | Must be >= 1. See [`docs/spec/questions.md`](questions.md#question-count-formula) |
| `context.duration_minutes` | integer\|null | no | Optional session duration hint |
| `context.difficulty` | string | no | `easy\|medium\|hard` (default: `medium`) |
| `context.language` | string | no | Language code (default: `en`) |
| `questions[].id` | string | yes | Unique question identifier (e.g., `q1`, `q2`) |
| `questions[].prompt` | string | yes | The question text |
| `questions[].agreed_answer` | string | yes | The refined/confirmed answer (model answer after refinement) |
| `questions[].user_answer` | string\|null | no | User's answer (set during `drill`) |
| `questions[].evaluation` | object\|null | no | Set during `evaluate` |
| `questions[].refinement_history` | array | yes | List of refinement comments and previous versions |
| `progress.attempts` | integer | yes | Number of practice attempts (drill+evaluate cycles) |
| `progress.best_score` | float | yes | Best average score across attempts (0.0-1.0) |
| `progress.last_score` | float | yes | Score from most recent attempt (0.0-1.0) |
| `progress.improving` | boolean | yes | Whether last attempt improved over previous |
| `progress.break_suggested` | boolean | yes | Whether a break was suggested after last evaluation |
| `next_steps` | string[] | yes | Practice suggestions (set during `evaluate`; default: `[]`) |

### Evaluation Object

```json
{
  "score": 0.0-1.0,
  "confidence": 0.0-1.0,
  "feedback": "string",
  "covered_points": ["string"],
  "missed_points": ["string"],
  "alternatives": [
    { "summary": "string", "score": 0.0-1.0 }
  ]
}
```

`evaluation` is `null` until `evaluate` runs. `alternatives` may be an empty array.

### Refinement History Entry

```json
{
  "timestamp": "ISO-8601",
  "question_id": "q1",
  "field": "prompt|agreed_answer",
  "comment": "string",
  "previous_value": "string",
  "new_value": "string"
}
```

### Status vs Progress Consistency

- `status == "prepared"` ⟺ Q&A generated, not yet confirmed for practice
- `status == "confirmed"` ⟺ Q&A locked, ready for drill
- `status == "drilling"` ⟺ User answering questions
- `status == "evaluated"` ⟺ Scored with feedback and next steps

### File Safety

- Session IDs used as filenames must be a single path component (no separators, `.`/`..`, or absolute paths).
- Session files are created with owner-only permissions (`0600`) because they may contain user's learning material and answers.
- Writes use a temporary file in the same directory followed by an atomic replace, so an interrupted write cannot leave a partially written session.

### Display Rules

- If top `confidence` < 0.95, show it.
- If another alternative score is within 0.05 of the top score, show that alternative.
- Self-reported, not calibrated.
- Show progress trend: improving 📈, stable ➡️, declining 📉
- If `break_suggested` is true, show break recommendation prominently
