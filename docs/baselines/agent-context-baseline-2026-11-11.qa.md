### Q1: Confirm the always-loaded file set
- Context: `AGENTS.md` is the only agent instruction file (no copilot-instructions.md, CLAUDE.md, .cursor/rules, nested AGENTS.md); it names 5 other files unconditionally or as governing reference, while `README.md` and `.github/pull_request_template.md` are candidates I currently exclude.
- Options presented: A) 6 files as listed (AGENTS.md + the 5 it names); exclude README.md and the PR template — matches #55's audit, which treats the PR template as "PR creation only, not agent context" · B) 8 files — also include `README.md` and `.github/pull_request_template.md`; adds 108 lines / 1128 tokens to the baseline · C) Defer — needs a decision on whether the PR template counts as agent context
- User answer: `A`
- Action taken: always-loaded set fixed to 6 files; README.md and the PR template excluded from the baseline table.

### Q2: Confirm the representative task set
- Context: Open issues #57–#66 are the natural source; I drafted 8 tasks (#57, #58, #59, #60, #61, #63, #64, #66), all open, so "include closed issues" does not arise.
- Options presented: A) All 8 open issues #57–#66 (excluding #62, which overlaps #66's workflow scope) — widest coverage, 8 rows · B) 5 tasks only: #57, #58, #60, #61, #66 — the doc-heavy core; shorter table · C) Defer — needs a decision on whether #62 belongs in the set
- User answer: `A`
- Action taken: task set fixed to 8 tasks: #57, #58, #59, #60, #61, #63, #64, #66.

### Q3: Confirm the report path
- Context: No `docs/baselines/` directory exists yet; the repo has no precedent for baseline artifacts.
- Options presented: A) `docs/baselines/agent-context-baseline-2026-11-11.md` (+ `.qa.md` companion) — new directory, dated, matches the issue's naming · B) `docs/agent-context-baseline-2026-11-11.md` — flat under `docs/`, no new directory · C) Defer — needs owner preference on directory layout
- User answer: `A`
- Action taken: report written to `docs/baselines/agent-context-baseline-2026-11-11.md`, Q&A log to `docs/baselines/agent-context-baseline-2026-11-11.qa.md`.

### Q4: Confirm PR vs push
- Context: Rule D6 requires a dedicated branch and no direct commits to `main`; branch protection requires a PR.
- Options presented: A) Open a PR from a dedicated branch referencing #56 — satisfies D6 and branch protection · B) Push the branch only, no PR — leaves the work unmerged and untracked · C) Defer — needs owner decision on merge timing
- User answer: `A`
- Action taken: work committed on branch `docs/agent-context-baseline-issue-56` and delivered as a PR referencing #56.
