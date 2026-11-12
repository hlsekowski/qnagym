# ADR 0008: Workflow runtime candidates

> **Purpose:** Records the workflow runtime candidates under consideration, by layer, without selecting any of them.
> **Read when:** choosing a runtime for the worker/task execution model, or asking which runtimes were considered.
> **Owns:** the candidate list for the orchestration, coding-agent and deployment layers. Each layer's selection is owned by its own decision ADR.

## Status

Proposed

## Context

ADR 0004 defines the worker/task execution model and selects no framework, queue implementation, container runtime, workflow engine, model, or polling mechanism. Its §9 (Deployment neutrality) states that each runtime technology is decided in its own ADR when introduced.

No such ADR exists yet, and the candidate set was recorded only in an issue comment — invisible to anyone reading the repository. This ADR makes that set visible and attributable, so the per-layer decision ADRs have a stated starting point rather than an implicit one.

### Origin

The candidate set comes from the #55 audit, question 1, answered by the repository owner:

> `there will be automation - initial plan is to use langgraph , opencode , k8s , but this is not written in stone`

The qualifier is part of the record: these are candidates, not commitments.

## Decision

### 1. No runtime is selected

This ADR selects nothing. It is a precursor to the per-layer decision ADRs that ADR 0004 §9 requires, and it does not authorize implementation against any candidate.

### 2. Candidates by layer

| Layer | Candidate | Status |
|---|---|---|
| Orchestration | LangGraph | under consideration |
| Coding agent | opencode | under consideration |
| Deployment | k8s | tracked separately in [#9](https://github.com/hlsekowski/qnagym/issues/9) |

The deployment layer is cross-referenced rather than restated: #9 owns that decision, and duplicating it here would create a second owner for the same fact.

### 3. What each layer decides

- **Orchestration** — how tasks are scheduled, claimed and retried; the ADR 0004 execution model's runtime.
- **Coding agent** — what performs an SDD cycle; the executor behind a task's development step.
- **Deployment** — where workers run; one machine or several.

The layers are separable. A decision on one does not commit the others, and a candidate may be adopted in one layer while another layer stays on the local environment of ADR 0003.

## Consequences

### Positive

- The candidate set is visible in the repository rather than living in an issue comment.
- Each layer's eventual decision ADR has a stated starting point, so "why this runtime" can be answered against a recorded alternative set.
- Separating the layers lets a runtime be adopted where it earns its place without committing the whole stack.

### Negative and limitations

- Candidacy is not evaluation. No candidate here has been measured against the ADR 0004 invariants — exclusive claims with expiry, durable execution state, isolated workspaces, deduplicated effects.
- A candidate may be superseded before any decision ADR is written; this list would then need amending.

### Cost

Listing a candidate implies no cost commitment. LangGraph and opencode are open-source, and constitution C3 (zero-cost AI) continues to apply unchanged: any choice that implied paid infrastructure or hardware would require a separate decision amending ADR 0003, as ADR 0004 §9 already requires.

## Related

- [ADR 0004: Worker and Task Execution Model](0004-worker-task-model.md) — the execution model these runtimes would implement; §9 requires a per-runtime decision ADR
- [ADR 0003: Local AI-Driven Development Workflow](0003-local-development-workflow.md) — the current local environment
- [#9: Introduce k8s as worker runtime](https://github.com/hlsekowski/qnagym/issues/9) — owns the deployment-layer decision
- [#55: applicability audit](https://github.com/hlsekowski/qnagym/issues/55) — origin of the candidate set (question 1)
