# ADR 0010: OpenCode coding-agent execution

> **Purpose:** Records the decision to use OpenCode as the coding-agent execution technology for the SDD process.
> **Read when:** implementing or changing the coding-agent execution layer.
> **Owns:** the OpenCode selection and its boundaries; ADR 0007 continues to own SDD process responsibilities.

## Status

Proposed

## Context

ADR 0004 defines the worker/task execution model but deliberately selects no runtime technology. Its §9 requires a separate decision for each runtime technology when introduced.

The project owner identified OpenCode as part of the initial plan in the [#55 decision log](https://github.com/hlsekowski/qnagym/issues/55), with the qualifier that the plan "is not written in stone."

ADR 0008 previously bundled LangGraph, OpenCode, Kubernetes, and LiteLLM into a single decision record. This ADR separates the OpenCode decision as required by ADR 0004 §9.

## Decision

Use [OpenCode](https://opencode.ai/docs/) as the coding-agent execution technology for the SDD process.

OpenCode performs the SDD coding-agent role. Its configurable provider endpoint supports connecting to an OpenAI-compatible local model endpoint. OpenCode must be configured and tested against a local model endpoint before it is used for project work. Paid APIs, subscriptions, or cloud model defaults are not authorized.

OpenCode can use the LiteLLM OpenAI-compatible endpoint (ADR 0012) without taking over workflow orchestration.

## Consequences

### Positive

- Strong fit alongside LangGraph and LiteLLM for the SDD coding-agent role.
- Supports a local model endpoint, preserving the project's zero-cost constraint.
- Separate ADR per technology as ADR 0004 §9 requires.

### Limitations

- OpenCode must be configured and tested against a local model endpoint before project use.
- OpenCode does not replace workflow orchestration; that remains LangGraph's concern (ADR 0009).

## Related

- [ADR 0003: Local AI-Driven Development Workflow](0003-local-development-workflow.md) — local-first and zero-cost constraints
- [ADR 0004: Worker and Task Execution Model](0004-worker-task-model.md) — worker/task invariants and runtime neutrality
- [ADR 0007: SDD Process](0007-sdd-process.md) — responsibilities of the process that invokes a coding agent
- [ADR 0008: Workflow runtime and model-routing selection](0008-workflow-runtime-and-model-routing.md) — umbrella decision record
- [ADR 0012: LiteLLM model routing](0012-litellm-model-routing.md) — model routing for workflow-agent calls
- [#55: Applicability audit](https://github.com/hlsekowski/qnagym/issues/55) — records the owner's initial plan
- [Project constitution](../constitution.md) and [rule catalog](../rules.md) — constraints for technology selection
