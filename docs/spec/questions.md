# Questions Contract

Source: [`docs/spec.md`](spec.md#inputs)

## Contract

### Question Count Formula

When `duration_minutes` is provided:

```
question_count = max(3, min(15, round(duration_minutes / 6)))
```

When `duration_minutes` is not provided, default to 5 questions.

**Note:** Python's `round()` uses banker's rounding (round to even).

| Duration (min) | Questions |
|---|---|
| 0–20 | 3 |
| 21–27 | 4 |
| 28–33 | 5 |
| 34–39 | 6 |
| 40–45 | 7 |
| 46–51 | 8 |
| 52–57 | 9 |
| 58–63 | 10 |
| 64–69 | 11 |
| 70–75 | 12 |
| 76–81 | 13 |
| 82–87 | 14 |
| ≥ 88 | 15 |

### Vague Material Threshold

Material is considered too vague if it contains fewer than **20 characters** (after trimming whitespace).

```python
MIN_MATERIAL_CHARS = 20  # See [`MIN_MATERIAL_CHARS`](../src/qnagym/contracts/constants.py) - example default
```

> **Note:** The threshold value is defined by [`MIN_MATERIAL_CHARS`](../src/qnagym/contracts/constants.py).

If the material is too vague, `generate` stops and prints clarifying questions. It does not invent a topic.

### Clarifying Questions (Default)

When the material is too vague, the model returns (or the CLI falls back to):

1. "What specific topic or subject do you want to learn about?"
2. "What is the scope or focus area (e.g., basics, advanced, specific aspect)?"
3. "What is your current knowledge level (beginner, intermediate, advanced)?"

### Question ID Format

Question IDs are strings, unique within a session, non-empty. The code generates `q1`, `q2`, ... if the model doesn't provide IDs.

### Difficulty Levels

| Level | Description |
|---|---|
| `easy` | Basic recall and understanding |
| `medium` | Application and analysis (default) |
| `hard` | Synthesis and evaluation |

Difficulty affects prompt instructions to the model.
