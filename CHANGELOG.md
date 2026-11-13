# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ADR 0006: PR Process — Feedback Evaluation, Check Monitoring, Lifecycle, and Completion
- ADR 0005: Issue Process
- ADR 0004: Worker and Task Execution Model
- ADR 0003: Local AI-Driven Development Workflow
- ADR 0002: Architecture Dependency Model with granular levels
- ADR 0001: Spec-Driven Development
- Constitution principles (C1-C10) and rules (A1-A4, D1-D5, NC1-NC8)
- Spec contracts: cli, session, config, flow, prompts, questions, traceability
- Contracts layer: types, validation, constants, config, flow, prompts, questions
- Domain logic: flow, questions, scoring, session
- Services: generate, refine, confirm, drill, evaluate, progress
- Adapters: cli, config, client, session_store, display
- Test structure: unit, contracts, integration with mocked HTTP
- CI pipeline: lint, typecheck, test, security, dependencies, traceability, doc-defaults
- Pre-commit hooks: ruff, mypy, gitleaks, traceability, doc-defaults, pytest
- No-cost AI rules enforced (local-first, free-tier cloud only)
- Worker/task execution model (ADR 0004): contracts, domain, and services
- Issue Process (ADR 0005): contracts, domain, and services
- PR Process (ADR 0006): contracts, domain, and services
- SDD Process (ADR 0007): contracts, domain, and services
- Worker/task model (ADR 0004): contracts, domain, and services

## [v0.1.0] - 2026-11-13

### Added
- ADR 0001–0007: Spec-driven development, architecture, local workflow, worker/task model, issue process, PR process, SDD process
- Constitution principles C1-C10 and rules A1-A4, D1-D8, NC1-NC8
- Spec contracts: cli, session, config, flow, prompts, questions, traceability
- CLI commands: generate, refine, confirm, drill, evaluate, repeat (--weak-only), reset, delete, export, list, show
- Worker/task execution: execution state, task runner, claims, safe effects, observation, git workspace, PR creation
- Per-question progress tracking with streak-based break suggestion
- Golden-set evaluator quality harness (skippable without local model)
- CI pipeline: lint, typecheck, test, security, dependencies, traceability, doc-defaults, pre-commit

### Changed
- flow.md: drilling reset transition corrected to prepared (matches implementation)
- flow.md: break-suggestion logic aligned to streak-based definition
- ADR 0007: status Proposed → Accepted
- ADR 0008: status Proposed → Accepted
