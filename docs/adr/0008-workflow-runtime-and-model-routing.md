# ADR 0008: Workflow runtime and model-routing selection

> **Purpose:** Records the chosen technologies for workflow orchestration, model routing, coding-agent execution, and worker hosting.
> **Read when:** implementing or changing the automated workflow runtime or model-routing layer.
> **Owns:** the chosen technologies and their boundaries; ADR 0004 continues to own worker/task invariants.

## Status

Proposed

## Context

[ADR 0003](0003-local-development-workflow.md) defines the Issue, SDD, and PR processes and requires the workflow to use the existing local environment without subscriptions, paid services, cloud charges, or hardware upgrades. [ADR 0004](0004-worker-task-model.md) defines the worker/task model but deliberately selects no runtime technology. Its §9 requires a separate decision for each runtime technology when introduced.

The project owner identified LangGraph, OpenCode, and Kubernetes as the initial plan in the [#55 decision log](https://github.com/hlsekowski/qnagym/issues/55), with the qualifier that the plan "is not written in stone" and the runner recorded as TBD among those three. #55 did not select the stack or LiteLLM — LiteLLM is not in #55, #98, or #9. Issue [#98](https://github.com/hlsekowski/qnagym/issues/98) recorded LangGraph as a candidate workflow runtime under consideration before Kubernetes; #98 selected no runtime — this ADR is the umbrella decision record. Issue [#9](https://github.com/hlsekowski/qnagym/issues/9) scopes Kubernetes work to a local cluster and explicitly excludes cloud deployment.

Per ADR 0004 §9, each runtime technology is decided in its own ADR:

- [ADR 0009: LangGraph workflow graph orchestration](0009-langgraph-workflow-orchestration.md) — Proposed
- [ADR 0010: OpenCode coding-agent execution](0010-opencode-coding-agent.md) — Proposed
- [ADR 0011: Kubernetes worker hosting](0011-kubernetes-worker-hosting.md) — Proposed
- [ADR 0012: LiteLLM model routing for workflow-agent calls](0012-litellm-model-routing.md) — Proposed

These choices favor Python-compatible workflow development and a path from one local worker to multiple workers. They do not claim that any one chosen product implements every ADR 0004 invariant. In particular, agent-graph persistence is not by itself proof of cross-worker claims, fencing, shared execution state, workspace isolation, or safe effect recovery.

The chosen routing layer classifies each workflow-agent request and selects a configured model while preserving the existing OpenAI-compatible `base_url` + `model` boundary. The owner chose LiteLLM for workflow-agent model routing. LiteLLM's [Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing) supports one client-facing model name, a classifier, configured model tiers, and a heuristic fallback; the feature is explicitly beta.

## Decision

### 1. Chosen technologies

| Layer | Chosen solution | Decision ADR | Status |
|---|---|---|---|
| Agent/workflow graph orchestration | [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | [ADR 0009](0009-langgraph-workflow-orchestration.md) | Proposed |
| Coding-agent execution | [OpenCode](https://opencode.ai/docs/) | [ADR 0010](0010-opencode-coding-agent.md) | Proposed |
| Worker hosting | [Kubernetes](https://kubernetes.io/docs/concepts/overview/) | [ADR 0011](0011-kubernetes-worker-hosting.md) | Proposed |
| Model routing for workflow-agent calls | [LiteLLM Proxy with Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing) | [ADR 0012](0012-litellm-model-routing.md) | Proposed |

### 2. Why this starting stack

- **LangGraph:** See [ADR 0009](0009-langgraph-workflow-orchestration.md).
- **Kubernetes:** See [ADR 0011](0011-kubernetes-worker-hosting.md).
- **OpenCode:** See [ADR 0010](0010-opencode-coding-agent.md).
- **LiteLLM:** See [ADR 0012](0012-litellm-model-routing.md).

The other durable workflow candidates considered were [Temporal](https://docs.temporal.io/), [Restate](https://docs.restate.dev/), [DBOS](https://docs.dbos.dev/), [Inngest](https://www.inngest.com/docs), and [Hatchet](https://docs.hatchet.run/). They are not selected for the initial implementation because the project will first validate its chosen LangGraph design and the smallest coordination layer needed to satisfy ADR 0004. A dedicated durable workflow engine should be reconsidered if that design fails the required tests.

### 3. Rollout boundaries

- The initial workflow remains usable in ADR 0003's local development environment with one worker. A local Kubernetes cluster is introduced for the multi-worker experiment, not made a prerequisite for ordinary development.
- OpenCode must be configured and tested against a local model endpoint before it is used for project work. Paid APIs, subscriptions, or cloud model defaults are not authorized.
- LiteLLM runs as a separately operated local gateway, not as a Python SDK dependency in qnagym. Existing clients continue using the OpenAI-compatible API, which preserves constitution C4 and rule NC3's dependency boundary.
- Workflow-agent calls use LiteLLM router aliases and allowlists. Until a separate decision authorizes otherwise, the allowlist contains only locally hosted models; a failure or unknown model must not fall through to a paid or cloud provider.
- Use a local classifier model with heuristic fallback. Send the minimum request context needed for classification, keep classifier and completion endpoints local, and do not log prompts or secrets.
- LiteLLM's [no-database gateway setup](https://docs.litellm.ai/docs/proxy/docker_quick_start#running-without-a-database) does not enforce spend budgets, while its [virtual-key setup](https://docs.litellm.ai/docs/proxy/virtual_keys) requires PostgreSQL. C3 must therefore be enforced by the local-model allowlist, not assumed from gateway budget settings. Any non-local provider or spend-based control requires a separate decision and tested configuration.
- LangGraph graph state must use durable persistence where restart recovery is required. The persistence choice and configuration must be documented and tested before relying on it.
- Kubernetes hosts workers; it does not provide the application's task identity, claim expiry and fencing, shared execution state, deduplication, or effect-recovery rules.
- No worker may run concurrently or produce workflow effects until the complete implementation satisfies and tests the applicable ADR 0004 invariants.

### 3a. LangGraph dependency gate (C9 erratum)

See [ADR 0009 §Dependency gate](0009-langgraph-workflow-orchestration.md#dependency-gate-c9-erratum).

### 4. Required validation before adopting model routing

See [ADR 0012 §Required validation before adopting model routing](0012-litellm-model-routing.md#required-validation-before-adopting-model-routing).

### 5. Required validation before multi-worker use

The implementation must verify, with stub tasks and no model calls:

1. At most one task for a work item can hold a valid claim; claims expire, takeover is safe, and stale workers are fenced from effects.
2. Durable execution state is shared and survives process or worker restart.
3. Each task receives an isolated workspace.
4. Replayed or retried work cannot duplicate external effects.
5. The workflow recovers after downtime without losing required task state.

Issue #9 tracks the local Kubernetes experiment and already requires testing claim exclusivity, expiry, and takeover. The remaining cases must also be covered before multi-worker operation is treated as supported.

This ADR does not select the database, claim-store implementation, local-cluster distribution, or hosted platform. Those choices require a separate decision if implementation needs them; they must remain consistent with ADR 0003, constitution principles C3, C4, and C9, and rule NC3.

## Consequences

### Positive

- The chosen stack gives the project a concrete, incremental starting point aligned with the owner's stated direction: LangGraph, OpenCode, local Kubernetes, and LiteLLM routing.
- A single OpenAI-compatible local gateway can route both development agents and qnagym model tasks without adding LiteLLM's SDK to the application dependencies.
- Local-first development remains the default while Kubernetes provides a path to verify multi-worker behavior.
- Responsibilities are explicit: graph execution, coding-agent tool, and worker hosting are separate concerns.
- The validation gate prevents product names from being mistaken for guarantees of ADR 0004 correctness.
- Each technology has its own ADR as ADR 0004 §9 requires.

### Limitations

- LangGraph's graph persistence does not replace the task coordination and effect-safety mechanisms required by ADR 0004.
- Kubernetes adds local operational complexity; it is limited to the multi-worker milestone rather than required for every development session.
- LiteLLM Auto Routing is beta and adds a local gateway and classifier to operate. Its budget controls cannot be relied on in no-database mode, and its release history requires strict artifact verification.
- All four technologies remain Proposed pending the validation in §4 and §5; none is accepted for production use until that validation passes.

## Related

- [ADR 0003: Local AI-Driven Development Workflow](0003-local-development-workflow.md) — local-first and zero-cost constraints
- [ADR 0004: Worker and Task Execution Model](0004-worker-task-model.md) — worker/task invariants and runtime neutrality
- [ADR 0007: SDD Process](0007-sdd-process.md) — responsibilities of the process that invokes a coding agent
- [ADR 0009: LangGraph workflow graph orchestration](0009-langgraph-workflow-orchestration.md) — LangGraph decision
- [ADR 0010: OpenCode coding-agent execution](0010-opencode-coding-agent.md) — OpenCode decision
- [ADR 0011: Kubernetes worker hosting](0011-kubernetes-worker-hosting.md) — Kubernetes decision
- [ADR 0012: LiteLLM model routing for workflow-agent calls](0012-litellm-model-routing.md) — LiteLLM decision
- [AI provider policy](../ai_provider_policy.md) — model configuration, privacy, and zero-cost provider constraints
- [#9: Introduce k8s as worker runtime](https://github.com/hlsekowski/qnagym/issues/9) — local multi-worker Kubernetes experiment
- [#98: Introduce LangGraph as the first workflow runtime](https://github.com/hlsekowski/qnagym/issues/98) — prior decision to start with LangGraph
- [#55: Applicability audit](https://github.com/hlsekowski/qnagym/issues/55) — records the owner's initial LangGraph/OpenCode/Kubernetes plan
- [#101: PR introducing LiteLLM](https://github.com/hlsekowski/qnagym/pull/101) — introduced LiteLLM Proxy with Auto Routing into ADR 0008; no prior issue scoped LiteLLM
- [Project constitution](../constitution.md) and [rule catalog](../rules.md) — constraints for technology selection
