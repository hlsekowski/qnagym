# Implement an issue

> **Purpose:** The invocable procedure for implementing one issue of this repository, end to end.
> **Read when:** invoked to implement an issue. Not loaded otherwise.
> **Owns:** nothing — every step links to its owner doc. The workflow itself is owned by [`docs/workflow.md`](../workflow.md).

Implement issue **#N** of this repository. Follow these steps in order. Where a step links to a document, read that document for the details; do not restate them here.

1. **Read the issue and its parent.** Open #N and its parent tracking issue. Note the issue's Tasks, Acceptance criteria and Out of scope sections — they define the scope.
2. **Check blockers.** Every issue listed under "Blocked by" must be closed. If any is open, comment on #N saying which one blocks it and stop.
3. **Apply the applicability gate.** Find #N's verdict in the #55 audit comment. `APPLICABLE` → continue. `AMEND` → continue using the issue body as edited by the review. `NOT APPLICABLE` → stop and comment. No verdict → stop and comment; do not guess.
4. **Create the branch.** Per rule D6 in [`docs/rules.md`](../rules.md) and the naming convention in [`docs/workflow.md`](../workflow.md): `git checkout -b <type>/<short-description>` from `main`.
5. **Follow the spec-first cycle.** Execute the steps in [`docs/workflow.md`](../workflow.md) in order. If the change alters product behaviour or a data shape, update the spec contract before code.
6. **Implement only the issue's scope.** Do not fix unrelated problems, even ones you notice. If anything is ambiguous, comment on #N with the specific question and stop — do not guess. Record every question and answer verbatim.
7. **Run all checks.** Every command in [`AGENTS.md`](../AGENTS.md)'s Commands block, including the doc checks. All must pass before opening a PR.
8. **Open the PR.** Reference the issue with "Closes #N". Follow the repository PR template. Then tick #N's box in the parent tracking issue and add a Decision-log line there for any deviation from the issue's stated scope.

Stop conditions: a blocker is open, no verdict exists, the scope is ambiguous, or a check fails. In every case, comment on the issue and leave it open — never mark it blocked unilaterally.
