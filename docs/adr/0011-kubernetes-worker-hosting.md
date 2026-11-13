# ADR 0011: Kubernetes worker hosting

> **Purpose:** Records the decision to use Kubernetes as the worker hosting technology for multi-worker deployment.
> **Read when:** implementing or changing the worker hosting layer.
> **Owns:** the Kubernetes selection and its boundaries; ADR 0004 continues to own worker/task invariants.

## Status

Accepted

## Context

ADR 0004 defines the worker/task execution model but deliberately selects no runtime technology. Its §9 requires a separate decision for each runtime technology when introduced. The current backlog item is [#9](https://github.com/hlsekowski/qnagym/issues/9).

The project owner identified Kubernetes as part of the initial plan in the [#55 decision log](https://github.com/hlsekowski/qnagym/issues/55), with the qualifier that the plan "is not written in stone." Issue #9 scopes Kubernetes work to a local cluster and explicitly excludes cloud deployment. #9 is closed; the multi-worker experiment is not done and has no open issue.

ADR 0008 previously bundled LangGraph, OpenCode, Kubernetes, and LiteLLM into a single decision record. This ADR separates the Kubernetes decision as required by ADR 0004 §9.

## Decision

Use [Kubernetes](https://kubernetes.io/docs/concepts/overview/) as the worker hosting technology for multi-worker deployment.

Initial adoption and validation are local-cluster only, as scoped by issue #9; no hosted deployment is authorized. A local cluster supports a gradual, no-cloud path to testing worker behavior; Kubernetes is not required for ordinary single-worker development.

Kubernetes hosts workers; it does not provide the application's task identity, claim expiry and fencing, shared execution state, deduplication, or effect-recovery rules. Those remain ADR 0004's responsibility.

This architectural neutrality does not authorize paid infrastructure, additional hardware, or a change to the zero-cost constraint. Hosted or paid infrastructure requires a separate decision amending ADR 0003.

## Consequences

### Positive

- Container-orchestration choice for the planned multi-worker deployment.
- Local cluster supports a gradual, no-cloud path to testing worker behavior.
- Separate ADR per technology as ADR 0004 §9 requires.

### Limitations

- Kubernetes adds local operational complexity; it is limited to the multi-worker milestone rather than required for every development session.
- Kubernetes does not provide ADR 0004 invariants (task identity, claim expiry and fencing, shared execution state, deduplication, effect recovery).
- No hosted deployment is authorized.

## Related

- [ADR 0003: Local AI-Driven Development Workflow](0003-local-development-workflow.md) — local-first and zero-cost constraints
- [ADR 0004: Worker and Task Execution Model](0004-worker-task-model.md) — worker/task invariants and runtime neutrality
- [ADR 0008: Workflow runtime and model-routing selection](0008-workflow-runtime-and-model-routing.md) — umbrella decision record
- [#9: Introduce k8s as worker runtime](https://github.com/hlsekowski/qnagym/issues/9) — local multi-worker Kubernetes experiment
- [#55: Applicability audit](https://github.com/hlsekowski/qnagym/issues/55) — records the owner's initial plan
- [Project constitution](../constitution.md) and [rule catalog](../rules.md) — constraints for technology selection
