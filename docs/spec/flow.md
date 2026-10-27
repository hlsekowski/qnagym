# Flow Contract

Source: [`docs/spec.md`](spec.md#flow)

## Contract

```mermaid
flowchart TD
  ingestMaterial[Ingest material and optional context]
  generateQA[Generate question bank with model answers]
  userRefines[User refines Q&A via comments]
  userConfirms[User confirms Q&A bank]
  hideShow[Hide answers; show one question]
  userAnswers[User answers]
  moreQuestions{More questions?}
  evaluate[Evaluate vs agreed answers; track progress; suggest practice]
  repeat{Repeat?}
  ingestMaterial --> generateQA
  generateQA --> userRefines
  userRefines -->|more comments| userRefines
  userRefines -->|confirm| userConfirms
  userConfirms --> hideShow
  hideShow --> userAnswers
  userAnswers --> moreQuestions
  moreQuestions -->|yes| hideShow
  moreQuestions -->|no| evaluate
  evaluate --> repeat
  repeat -->|yes| hideShow
  repeat -->|no| end
```

## State Machine

| Status | Meaning | Allowed Transitions |
|---|---|---|
| `prepared` | Q&A generated, being refined | `prepared` (refine), `confirmed` (confirm) |
| `confirmed` | Q&A locked, ready for practice | `drilling` (drill) |
| `drilling` | Answers being captured | `evaluated` (evaluate, when all answered), `confirmed` (reset) |
| `evaluated` | Scored with feedback and progress | `confirmed` (repeat), `prepared` (reset to refine) |

## Guard Rules

- **generate**: Creates session in `prepared` state. If material too vague (see [`docs/spec/questions.md`](questions.md#vague-material-threshold)), stops with clarifying questions; raises `VagueMaterialError` with list; does not invent content.
- **refine**: Requires `status == "prepared"`. Accepts comments on specific questions. Updates `agreed_answer` and/or `prompt`, records in `refinement_history`. Stays in `prepared` state.
- **confirm**: Requires `status == "prepared"`. Transitions to `confirmed`. Sets `confirmed_at` timestamp.
- **drill** (record_answer): Requires `status == "confirmed"` (first answer transitions to `drilling`). Records `user_answer` for specific question. Validates question exists.
- **drill --interactive**: Requires `status == "confirmed"` or `drilling`. Runs interactive loop: shows next unanswered question, reads answer from stdin, records it, repeats until all answered or user types `quit`. Typing `skip` marks question as answered with `[skipped]` marker. Ctrl+C exits gracefully.
- **evaluate**: Requires `status == "drilling"` AND no unanswered questions. Transitions to `evaluated`. Scores all answers, updates `progress`, sets `next_steps`, suggests break if not improving.
- **repeat**: Requires `status == "evaluated"`. Transitions to `confirmed`. Clears `user_answer` and `evaluation` for all questions. Increments `progress.attempts`. Preserves `progress.best_score`, `progress.last_score`, `progress.improving`.
- **reset** (to prepared): Requires `status in {"drilling", "evaluated"}`. Transitions to `prepared`. Clears user answers, evaluations, next_steps. Resets progress for new refinement cycle.

## Progress Tracking Rules

- `progress.attempts`: Incremented on each `repeat` (drill+evaluate cycle)
- `progress.last_score`: Average score from most recent `evaluate`
- `progress.best_score`: Max of all `last_score` values
- `progress.improving`: `last_score > previous_last_score` (for attempts > 1)
- `progress.break_suggested`: Set to `true` if `not improving` for 2+ consecutive attempts OR `last_score < 0.3`

## Break Suggestion Logic

```
IF attempts >= 2 AND NOT improving:
    suggest_break = true
    next_steps.append("Take a 10-15 minute break before continuing")
ELIF last_score < 0.3:
    suggest_break = true
    next_steps.append("Consider reviewing the material before practicing again")
ELSE:
    suggest_break = false
```
