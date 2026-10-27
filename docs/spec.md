# qnagym Spec (v1)

Knowledge acquisition practice. Python CLI.

## In scope

- Topic-based learning: user provides material (text, topic, URL) to explore
- Iterative Q&A refinement: generate → comment/refine → confirm
- Practice drilling: hide answer, ask question, capture response
- Evaluation: score answer vs agreed answer, detailed feedback
- Progress tracking: track improvement across repeats, suggest breaks
- Local JSON session files under `data/sessions/` (override with `QNAGYM_DATA_DIR`)
- Hybrid models: local OpenAI-compatible by default; optional free-tier cloud

## Out of scope

Web UI, multi-user, accounts, network UI, paid APIs as default, live coding judge.

## User Scenario

```
1. qnagym generate --material "photosynthesis" --questions 5
   → Generates 5 Q&A pairs about photosynthesis

2. qnagym refine --session <id>
   → Shows Q&A; user comments on questions/answers to refine them
   → Repeat until satisfied

3. qnagym confirm --session <id>
   → Locks in the Q&A bank for practice

4. qnagym drill --session <id>
   → Hides answers, asks one question at a time, saves user answers

5. qnagym evaluate --session <id>
   → Scores answers vs agreed answers, gives feedback, suggests next steps

6. qnagym repeat --session <id>
   → Resets for another round, tracks improvement vs previous attempts
   → Suggests break if not improving
```

## Contracts

Detailed contracts live in `docs/spec/`. Each file has an explicit **Contract** section that code and tests must conform to.

| Contract | File | Covers |
|---|---|---|
| CLI | [`docs/spec/cli.md`](spec/cli.md) | Commands, flags, behavior rules, exit codes |
| Session JSON | [`docs/spec/session.md`](spec/session.md) | Session file schema, field contracts, display rules |
| Config | [`docs/spec/config.md`](spec/config.md) | Config keys, env, TOML, precedence |
| Flow | [`docs/spec/flow.md`](spec/flow.md) | State machine, guard rules |
| Prompts / Models | [`docs/spec/prompts.md`](spec/prompts.md) | JSON response contracts, standard-use models |
| Questions | [`docs/spec/questions.md`](spec/questions.md) | Question count, vague material threshold |
| Traceability | [`docs/spec/traceability.md`](spec/traceability.md) | Spec section → code → tests |

## Change workflow

Per [`docs/constitution.md`](constitution.md) principle 5 ("Spec before code"): write or update the spec contract that covers the task before implementation. See [`docs/spec/traceability.md`](spec/traceability.md) for how to map a spec change to code and tests.
