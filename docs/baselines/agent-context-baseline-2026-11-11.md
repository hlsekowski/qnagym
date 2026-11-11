# Agent Context Baseline — 2026-11-11

## Methodology

Always-loaded agent context = `AGENTS.md` plus every file it names unconditionally or as the governing reference. Measured at repo SHA `72a5c3273e2d658ba4202d875a58fba8c5beaa47` on branch `main`. Tokenizer: `tiktoken 0.14.0`, encoding `cl100k_base` (`pip install tiktoken`). Lines counted as newline bytes; bytes as file size. Task-set files are the files a competent agent would open for each issue, taken from the issue body's own scope statement.

## Always-loaded context

| Path | Lines | Bytes | Tokens |
|---|---|---|---|
| `AGENTS.md` | 25 | 2220 | 524 |
| `docs/constitution.md` | 19 | 2268 | 563 |
| `docs/spec.md` | 59 | 2548 | 615 |
| `docs/rules.md` | 88 | 4959 | 1325 |
| `docs/development.md` | 66 | 3215 | 815 |
| `docs/spec/traceability.md` | 50 | 3917 | 1167 |
| **Total** | **307** | **19127** | **5009** |

## Representative task set

| Issue | Task | Files opened | Tokens |
|---|---|---|---|
| #57 | fix broken links and path references | 28 | 39422 |
| #58 | slim AGENTS.md to routing file | 8 | 7637 |
| #59 | add doc link/path checker | 7 | 6865 |
| #60 | single source of truth | 29 | 40769 |
| #61 | purpose/read-when headers | 26 | 37996 |
| #63 | rules.md as lookup, ADR roles | 9 | 24630 |
| #64 | CI doc-structure checks | 6 | 6050 |
| #66 | issue-to-PR agent procedure | 7 | 12005 |

Per-task file lists:

- **#57** — `AGENTS.md`, `README.md`, all 26 tracked `*.md`.
- **#58** — `AGENTS.md`, `docs/constitution.md`, `docs/spec.md`, `docs/rules.md`, `docs/development.md`, `docs/spec/traceability.md`, `docs/testing.md`, `docs/ai_provider_policy.md`.
- **#59** — `scripts/check_traceability.py`, `scripts/check_doc_defaults.py`, `.github/workflows/ci.yml`, `docs/development.md`, `docs/rules.md`, `AGENTS.md`, `docs/constitution.md`.
- **#60** — `README.md`, `AGENTS.md`, all 26 tracked `*.md`, `src/qnagym/contracts/constants.py`.
- **#61** — all 26 tracked `*.md`.
- **#63** — `docs/rules.md`, `docs/constitution.md`, all 7 ADRs.
- **#64** — `scripts/check_traceability.py`, `scripts/check_doc_defaults.py`, `.github/workflows/ci.yml`, `docs/rules.md`, `docs/constitution.md`, `AGENTS.md`.
- **#66** — `docs/development.md`, `docs/adr/0005-issue-process.md`, `docs/adr/0006-pr-process.md`, `docs/adr/0007-sdd-process.md`, `AGENTS.md`, `docs/rules.md`, `docs/constitution.md`.

Derived: always-loaded share of the cheapest task (#58) = 5009 / 7637 = 65.6%; of the most expensive (#60) = 5009 / 40769 = 12.3%; mean task cost = 175374 / 8 = 21922 tokens. `docs/rules.md` is the largest always-loaded file (1325 tokens, 26.5% of the total) and is a lookup table per #63.

## Reproduction

```bash
git checkout 72a5c3273e2d658ba4202d875a58fba8c5beaa47
pip install tiktoken==0.14.0

# lines + bytes for the always-loaded set
wc -lc AGENTS.md docs/constitution.md docs/spec.md docs/rules.md docs/development.md docs/spec/traceability.md

# tokens for the always-loaded set
python3 -c "
import tiktoken, pathlib
enc = tiktoken.get_encoding('cl100k_base')
for f in ['AGENTS.md','docs/constitution.md','docs/spec.md','docs/rules.md','docs/development.md','docs/spec/traceability.md']:
    b = pathlib.Path(f).read_bytes()
    print(f, b.count(b'\n'), len(b), len(enc.encode(b.decode('utf-8'))))
"

# tokens for the task set (files per task as listed above)
python3 -c "
import subprocess, pathlib, tiktoken
enc = tiktoken.get_encoding('cl100k_base')
md = subprocess.run(['git','ls-files','*.md'],capture_output=True,text=True).stdout.split()
tasks = {
 '#57': ['AGENTS.md','README.md']+md,
 '#58': ['AGENTS.md','docs/constitution.md','docs/spec.md','docs/rules.md','docs/development.md','docs/spec/traceability.md','docs/testing.md','docs/ai_provider_policy.md'],
 '#59': ['scripts/check_traceability.py','scripts/check_doc_defaults.py','.github/workflows/ci.yml','docs/development.md','docs/rules.md','AGENTS.md','docs/constitution.md'],
 '#60': ['README.md','AGENTS.md']+md+['src/qnagym/contracts/constants.py'],
 '#61': md,
 '#63': ['docs/rules.md','docs/constitution.md']+[m for m in md if m.startswith('docs/adr/')],
 '#64': ['scripts/check_traceability.py','scripts/check_doc_defaults.py','.github/workflows/ci.yml','docs/rules.md','docs/constitution.md','AGENTS.md'],
 '#66': ['docs/development.md','docs/adr/0005-issue-process.md','docs/adr/0006-pr-process.md','docs/adr/0007-sdd-process.md','AGENTS.md','docs/rules.md','docs/constitution.md'],
}
for k, files in tasks.items():
    print(k, len(files), sum(pathlib.Path(f).read_bytes().count(b'\n') for f in files), sum(len(pathlib.Path(f).read_bytes()) for f in files), sum(len(enc.encode(pathlib.Path(f).read_bytes().decode('utf-8'))) for f in files))
"
```

## Out-of-scope notes

- `AGENTS.md:6` references `docs/plan.md`, which does not exist in the repository (`git ls-files` confirms). Belongs to #57; not fixed here.
- `.specstory/` holds local session transcripts and is git-ignored (`.gitignore:11`), so it is excluded from the baseline; #55 flagged it as a duplication hazard for a separate follow-up.
- No agent runner was executed: #56's amended body records the runner as TBD (LangGraph / opencode / k8s per #55 Q1). This baseline is therefore a static context-cost measurement, not a task pass/fail run; #67 should repeat it on the chosen runner.
- `README.md` (87 lines, 902 tokens) and `.github/pull_request_template.md` (21 lines, 205 tokens) are excluded from the always-loaded set per decision Q1.
