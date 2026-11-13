# ADR 0012: LiteLLM model routing for workflow-agent calls

> **Purpose:** Records the decision to use LiteLLM Proxy with Auto Routing for workflow-agent model routing.
> **Read when:** implementing or changing the model-routing layer for workflow-agent calls.
> **Owns:** the LiteLLM selection and its boundaries; ADR 0004 continues to own worker/task invariants.

## Status

Accepted

## Context

ADR 0004 defines the worker/task execution model but deliberately selects no runtime technology. Its §9 requires a separate decision for each runtime technology when introduced.

LiteLLM is not in #55, #98, or #9. It was introduced into ADR 0008 by [PR #101](https://github.com/hlsekowski/qnagym/pull/101) without a prior issue scoping it. This ADR records that provenance.

ADR 0008 previously bundled LangGraph, OpenCode, Kubernetes, and LiteLLM into a single decision record. This ADR separates the LiteLLM decision as required by ADR 0004 §9.

## Decision

Use [LiteLLM Proxy with Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing) for model routing for workflow-agent calls.

LiteLLM runs as a separately operated local gateway, not as a Python SDK dependency in qnagym. Existing clients continue using the OpenAI-compatible API, which preserves constitution C4 and rule NC3's dependency boundary.

Workflow-agent calls use LiteLLM router aliases and allowlists. Until a separate decision authorizes otherwise, the allowlist contains only locally hosted models; a failure or unknown model must not fall through to a paid or cloud provider.

Use a local classifier model with heuristic fallback. Send the minimum request context needed for classification, keep classifier and completion endpoints local, and do not log prompts or secrets.

LiteLLM's [no-database gateway setup](https://docs.litellm.ai/docs/proxy/docker_quick_start#running-without-a-database) does not enforce spend budgets, while its [virtual-key setup](https://docs.litellm.ai/docs/proxy/virtual_keys) requires PostgreSQL. C3 must therefore be enforced by the local-model allowlist, not assumed from gateway budget settings. Any non-local provider or spend-based control requires a separate decision and tested configuration.

### Required validation before adopting model routing

Before routing workflow or product traffic through LiteLLM:

1. Compare route decisions against a representative, labeled set of both workflow tasks and qnagym CLI tasks. Keep results separate by call path, task kind, and model; verify subject-specific assignments rather than only coarse complexity tiers.
2. Verify the local classifier, heuristic fallback, router default, and model-unavailable path. None may select a model outside the corresponding local allowlist.
3. Verify that every selected model meets the consuming call's output contract, including structured JSON for qnagym product calls.
4. Verify that prompts and relevant context sent to the classifier remain local and are not written to logs.
5. Before use, check the exact LiteLLM release and container artifact against current security advisories, verify its provenance and [image signature](https://docs.litellm.ai/proxy/docker_image_security), pin an immutable artifact, and audit its dependencies. Do not infer that a version is safe solely because it is earlier than a reported compromised version.
6. Confirm that the planned Auto Routing configuration is available without a paid license or hosted service. Auto Routing is beta, so pin its configuration and test upgrades before changing the pinned release.

The LiteLLM team confirmed that PyPI versions 1.82.7 and 1.82.8 were compromised in its [March 2026 incident report](https://docs.litellm.ai/blog/security-townhall-updates). It also confirmed that PyPI package 1.107.0 and several container tags were compromised on October 21, 2026, in its [incident report](https://docs.litellm.ai/blog/security-incident-oct-21-2026) and [canonical attack-chain report](https://docs.litellm.ai/blog/security-incident-oct-21-2026-attack-chain). This history makes artifact verification a blocking adoption gate, not a reason to reuse an old version pin.

## Consequences

### Positive

- A single OpenAI-compatible local gateway can route both development agents and qnagym model tasks without adding LiteLLM's SDK to the application dependencies.
- Local-first development remains the default.
- Separate ADR per technology as ADR 0004 §9 requires.

### Limitations

- LiteLLM Auto Routing is beta and adds a local gateway and classifier to operate.
- Its budget controls cannot be relied on in no-database mode.
- Its release history requires strict artifact verification.

## Related

- [ADR 0003: Local AI-Driven Development Workflow](0003-local-development-workflow.md) — local-first and zero-cost constraints
- [ADR 0004: Worker and Task Execution Model](0004-worker-task-model.md) — worker/task invariants and runtime neutrality
- [ADR 0008: Workflow runtime and model-routing selection](0008-workflow-runtime-and-model-routing.md) — umbrella decision record
- [AI provider policy](../ai_provider_policy.md) — model configuration, privacy, and zero-cost provider constraints
- [#101: PR introducing LiteLLM](https://github.com/hlsekowski/qnagym/pull/101) — introduced LiteLLM Proxy with Auto Routing into ADR 0008; no prior issue scoped LiteLLM
- [Project constitution](../constitution.md) and [rule catalog](../rules.md) — constraints for technology selection
