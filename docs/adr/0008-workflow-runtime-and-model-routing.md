# ADR 0008: Workflow runtime and model-routing selection

> **Purpose:** Records the chosen technologies for workflow orchestration, model routing, coding-agent execution, and worker hosting.
> **Read when:** implementing or changing the automated workflow runtime or model-routing layer.
> **Owns:** the chosen technologies and their boundaries; ADR 0004 continues to own worker/task invariants.

## Status

Accepted

## Context

[ADR 0003](0003-local-development-workflow.md) defines the Issue, SDD, and PR processes and requires the workflow to use the existing local environment without subscriptions, paid services, cloud charges, or hardware upgrades. [ADR 0004](0004-worker-task-model.md) defines the worker/task model but deliberately selects no runtime technology. Its §9 requires a separate decision for each runtime technology.

The project owner identified LangGraph, OpenCode, and Kubernetes as the initial plan in the [#55 decision log](https://github.com/hlsekowski/qnagym/issues/55), with the qualifier that the plan "is not written in stone" and the runner recorded as TBD among those three. #55 did not select the stack or LiteLLM — LiteLLM is not in #55, #98, or #9. Issue [#98](https://github.com/hlsekowski/qnagym/issues/98) recorded LangGraph as a candidate workflow runtime under consideration before Kubernetes; #98 selected no runtime — the Accepted ADR 0008 is the decision record. Issue [#9](https://github.com/hlsekowski/qnagym/issues/9) scopes Kubernetes work to a local cluster and explicitly excludes cloud deployment.

These choices favor Python-compatible workflow development and a path from one local worker to multiple workers. They do not claim that any one chosen product implements every ADR 0004 invariant. In particular, agent-graph persistence is not by itself proof of cross-worker claims, fencing, shared execution state, workspace isolation, or safe effect recovery.

The chosen routing layer classifies each workflow-agent request and selects a configured model while preserving the existing OpenAI-compatible `base_url` + `model` boundary. The owner chose LiteLLM for workflow-agent model routing. LiteLLM's [Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing) supports one client-facing model name, a classifier, configured model tiers, and a heuristic fallback; the feature is explicitly beta.

## Decision

### 1. Chosen technologies

| Layer | Chosen solution | Scope |
|---|---|---|
| Agent/workflow graph orchestration | [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | Defines and runs stateful agent/workflow graphs. Its checkpointer can persist graph state and support resumption ([persistence docs](https://docs.langchain.com/oss/python/langgraph/persistence)). It is not, by this decision alone, the ADR 0004 task queue, claim coordinator, or effect guard. |
| Coding-agent execution | [OpenCode](https://opencode.ai/docs/) | Initial coding-agent tool for the SDD process. Its configurable provider endpoint supports connecting to an OpenAI-compatible local model endpoint ([provider docs](https://opencode.ai/docs/providers/)). |
| Worker hosting | [Kubernetes](https://kubernetes.io/docs/concepts/overview/) | Target for running multiple workers. Initial adoption and validation are local-cluster only, as scoped by issue #9; no hosted deployment is authorized. |
| Model routing for workflow-agent calls | [LiteLLM Proxy with Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing) | OpenAI-compatible gateway using separate router aliases and model allowlists for workflow agents. Classifier: a local LLM with heuristic fallback. Auto Routing is beta; no version or artifact is selected here. |

### 2. Why this starting stack

- **LangGraph:** It provides a Python graph model for stateful agent workflows and persistence for resuming graph state. That fits the project’s multi-step agent workflow and allows the graph logic to live with the Python application. It is chosen for graph-level orchestration, not as a substitute for ADR 0004’s separate task-claim and effect-safety mechanisms.
- **Kubernetes:** It is the container-orchestration choice for the planned multi-worker deployment, scoped by the open #9 experiment — #9 is the open experiment, not the source of acceptance. A local cluster supports a gradual, no-cloud path to testing worker behavior; Kubernetes is not required for ordinary single-worker development.
- **OpenCode:** It is a strong fit alongside LangGraph and LiteLLM: it performs the SDD coding-agent role, supports a local model endpoint, and can use the LiteLLM OpenAI-compatible endpoint without taking over workflow orchestration.
- **LiteLLM:** It can present one OpenAI-compatible endpoint to workflow-agent clients, keeping qnagym code on its current provider boundary while routing workflow-agent tasks by model. Its router offers fallback behavior and a local heuristic classifier, but the chosen LLM classifier adds another inference call and must itself use a local endpoint. Routing quality and tier assignment must be measured on this project's workflow-agent tasks.

The other durable workflow candidates considered were [Temporal](https://docs.temporal.io/), [Restate](https://docs.restate.dev/), [DBOS](https://docs.dbos.dev/), [Inngest](https://www.inngest.com/docs), and [Hatchet](https://docs.hatchet.run/). They are not selected for the initial implementation because the project will first validate its chosen LangGraph design and the smallest coordination layer needed to satisfy ADR 0004. A dedicated durable workflow engine should be reconsidered if that design fails the required tests.

### 3. Rollout boundaries

- The initial workflow remains usable in ADR 0003’s local development environment with one worker. A local Kubernetes cluster is introduced for the multi-worker experiment, not made a prerequisite for ordinary development.
- OpenCode must be configured and tested against a local model endpoint before it is used for project work. Paid APIs, subscriptions, or cloud model defaults are not authorized.
- LiteLLM runs as a separately operated local gateway, not as a Python SDK dependency in qnagym. Existing clients continue using the OpenAI-compatible API, which preserves constitution C4 and rule NC3's dependency boundary.
- Workflow-agent calls use LiteLLM router aliases and allowlists. Until a separate decision authorizes otherwise, the allowlist contains only locally hosted models; a failure or unknown model must not fall through to a paid or cloud provider.
- Use a local classifier model with heuristic fallback. Send the minimum request context needed for classification, keep classifier and completion endpoints local, and do not log prompts or secrets.
- LiteLLM's [no-database gateway setup](https://docs.litellm.ai/docs/proxy/docker_quick_start#running-without-a-database) does not enforce spend budgets, while its [virtual-key setup](https://docs.litellm.ai/docs/proxy/virtual_keys) requires PostgreSQL. C3 must therefore be enforced by the local-model allowlist, not assumed from gateway budget settings. Any non-local provider or spend-based control requires a separate decision and tested configuration.
- LangGraph graph state must use durable persistence where restart recovery is required. The persistence choice and configuration must be documented and tested before relying on it.
- Kubernetes hosts workers; it does not provide the application’s task identity, claim expiry and fencing, shared execution state, deduplication, or effect-recovery rules.
- No worker may run concurrently or produce workflow effects until the complete implementation satisfies and tests the applicable ADR 0004 invariants.

### 3a. LangGraph dependency gate (C9 erratum)

LangGraph is accepted as the workflow graph technology, but acceptance is not a C9 waiver. No `langgraph` Python dependency may be added to `pyproject.toml` until all of the following are complete:

1. A measured need for the `langgraph` dependency is documented (what graph capability it provides that the current implementation cannot).
2. The exact `langgraph` release is checked against current security advisories, its provenance verified, and an immutable version pin recorded in `pyproject.toml`.
3. Its dependencies are audited (rule NC3 / constitution C9) and the audit result is recorded.

This mirrors the LiteLLM artifact-verification gate in §4. Until the gate is passed, LangGraph graph logic may be prototyped in application code but no `langgraph` dependency is introduced.

### 4. Required validation before adopting model routing

Before routing workflow or product traffic through LiteLLM:

1. Compare route decisions against a representative, labeled set of both workflow tasks and qnagym CLI tasks. Keep results separate by call path, task kind, and model; verify subject-specific assignments rather than only coarse complexity tiers.
2. Verify the local classifier, heuristic fallback, router default, and model-unavailable path. None may select a model outside the corresponding local allowlist.
3. Verify that every selected model meets the consuming call's output contract, including structured JSON for qnagym product calls.
4. Verify that prompts and relevant context sent to the classifier remain local and are not written to logs.
5. Before use, check the exact LiteLLM release and container artifact against current security advisories, verify its provenance and [image signature](https://docs.litellm.ai/docs/proxy/docker_image_security), pin an immutable artifact, and audit its dependencies. Do not infer that a version is safe solely because it is earlier than a reported compromised version.
6. Confirm that the planned Auto Routing configuration is available without a paid license or hosted service. Auto Routing is beta, so pin its configuration and test upgrades before changing the pinned release.

The LiteLLM team confirmed that PyPI versions 1.82.7 and 1.82.8 were compromised in its [March 2026 incident report](https://docs.litellm.ai/blog/security-townhall-updates). It also confirmed that PyPI package 1.107.0 and several container tags were compromised on October 21, 2026, in its [incident report](https://docs.litellm.ai/blog/security-incident-oct-21-2026) and [canonical attack-chain report](https://docs.litellm.ai/blog/security-incident-oct-21-2026-attack-chain). This history makes artifact verification a blocking adoption gate, not a reason to reuse an old version pin.

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

- The chosen stack gives the project a concrete, incremental starting point aligned with the owner’s stated direction: LangGraph, OpenCode, local Kubernetes, and LiteLLM routing.
- A single OpenAI-compatible local gateway can route both development agents and qnagym model tasks without adding LiteLLM's SDK to the application dependencies.
- Local-first development remains the default while Kubernetes provides a path to verify multi-worker behavior.
- Responsibilities are explicit: graph execution, coding-agent tool, and worker hosting are separate concerns.
- The validation gate prevents product names from being mistaken for guarantees of ADR 0004 correctness.

### Limitations

- LangGraph’s graph persistence does not replace the task coordination and effect-safety mechanisms required by ADR 0004.
- Kubernetes adds local operational complexity; it is limited to the multi-worker milestone rather than required for every development session.
- LiteLLM Auto Routing is beta and adds a local gateway and classifier to operate. Its budget controls cannot be relied on in no-database mode, and its release history requires strict artifact verification.

## Related

- [ADR 0003: Local AI-Driven Development Workflow](0003-local-development-workflow.md) — local-first and zero-cost constraints
- [ADR 0004: Worker and Task Execution Model](0004-worker-task-model.md) — worker/task invariants and runtime neutrality
- [ADR 0007: SDD Process](0007-sdd-process.md) — responsibilities of the process that invokes a coding agent
- [AI provider policy](../ai_provider_policy.md) — model configuration, privacy, and zero-cost provider constraints
- [#9: Introduce k8s as worker runtime](https://github.com/hlsekowski/qnagym/issues/9) — local multi-worker Kubernetes experiment
- [#98: Introduce LangGraph as the first workflow runtime](https://github.com/hlsekowski/qnagym/issues/98) — prior decision to start with LangGraph
- [#55: Applicability audit](https://github.com/hlsekowski/qnagym/issues/55) — records the owner’s initial LangGraph/OpenCode/Kubernetes plan
- [Project constitution](../constitution.md) and [rule catalog](../rules.md) — constraints for technology selection
