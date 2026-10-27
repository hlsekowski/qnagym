# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with Spec-Driven Development (SDD) architecture
- Constitution principles (C1-C10) and rules (A1-A4, D1-D5, NC1-NC8)
- ADR 0001: Spec-Driven Development
- ADR 0002: Architecture Dependency Model with granular levels
- Spec contracts: cli, session, config, flow, prompts, questions, traceability
- Contracts layer: types, validation, constants, config, flow, prompts, questions
- Domain logic: flow, questions, scoring, session
- Services: generate, refine, confirm, drill, evaluate, progress
- Adapters: cli, config, client, session_store, display
- Test structure: unit, contracts, integration with mocked HTTP
- CI pipeline: lint, typecheck, test, security, dependencies, traceability, doc-defaults
- Pre-commit hooks: ruff, mypy, gitleaks, traceability, doc-defaults, pytest
- No-cost AI rules enforced (local-first, free-tier cloud only)
