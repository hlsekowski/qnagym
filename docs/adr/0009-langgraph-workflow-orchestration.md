# ADR 0009: LangGraph workflow graph orchestration

> **Purpose:** Records the decision to use LangGraph as the workflow graph orchestration technology.
> **Read when:** implementing or changing the workflow graph orchestration layer.
> **Owns:** the LangGraph selection and its boundaries; ADR 0004 continues to own worker/task invariants.

## Status

Proposed

## Context

ADR 0004 defines the worker/task execution model but deliberately selects no runtime technology. Its §9 requires a separate decision for each runtime technology when introduced.

The project owner identified LangGraph as part of the initial plan in the [#55 decision log](https://github.com/hlsekowski/qnagym/issues/55), with the qualifier that the plan "is not written in stone." LangGraph was recorded as a candidate workflow runtime under consideration in [#98](https://github.com/hlsekowski/qnagym/issues/98); #98 selected no runtime.

ADR 0008 previously bundled LangGraph, OpenCode, Kubernetes, and LiteLLM into a single decision record. This ADR separates the LangGraph decision as required by ADR 0004 §9.

## Decision

Use [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) as the workflow graph orchestration technology.

LangGraph defines and runs stateful agent/workflow graphs. Its checkpointer can persist graph state and support resumption. It is chosen for graph-level orchestration, not as a substitute for ADR 0004's separate task-claim and effect-safety mechanisms. LangGraph graph state persistence is not by itself proof of cross-worker claims, fencing, shared execution state, workspace isolation, or safe effect recovery.

### Dependency gate (C9 erratum)

LangGraph is proposed as the workflow graph technology, but acceptance is not a C9 waiver. No `langgraph` Python dependency may be added to `pyproject.toml` until all of the following are complete:

1. A measured need for the `langgraph` dependency is documented (what graph capability it provides that the current implementation cannot).
2. The exact `langgraph` release is checked against current security advisories, its provenance verified, and an immutable version pin recorded in `pyproject.toml`.
3. Its dependencies are audited (rule NC3 / constitution C9) and the audit result is recorded.

Until the gate is passed, LangGraph graph logic may be prototyped in application code but no `langgraph` dependency is introduced.

## Consequences

### Positive

- Provides a Python graph model for stateful agent workflows and persistence for resuming graph state.
- Fits the project's multi-step agent workflow; graph logic can live with the Python application.
- Separate ADR per technology as ADR 0004 §9 requires.

### Limitations

- LangGraph's graph persistence does not replace the task coordination and effect-safety mechanisms required by ADR 0004.
- No `langgraph` dependency may be added until the C9 gate is passed.

## Related

- [ADR 0003: Local AI-Driven Development Workflow](0003-local-development-workflow.md) — local-first and zero-cost constraints
- [ADR 0004: Worker and Task Execution Model](0004-worker-task-model.md) — worker/task invariants and runtime neutrality
- [ADR 0008: Workflow runtime and model-routing selection](0008-workflow-runtime-and-model-routing.md) — umbrella decision record
- [#55: Applicability audit](https://github.com/hlsekowski/qnagym/issues/55) — records the owner's initial plan
- [#98: Introduce LangGraph as the first workflow runtime](https://github.com/hlsekowski/qnagym/issues/98) — prior decision to start with LangGraph
- [Project constitution](../constitution.md) and [rule catalog](../rules.md) — constraints for technology selection
