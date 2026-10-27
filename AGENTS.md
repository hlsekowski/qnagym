# Agent instructions

Read `docs/constitution.md` (principles C1–C10) and `docs/spec.md` (v1 product) before changing this repo.

- Follow `docs/constitution.md` (C1–C10).
- Implementation order: `docs/plan.md` (spec→code mapping: `docs/spec/traceability.md`).
- Spec-first workflow: `docs/development.md`.
- Dedicated branches: every modification must be done in a dedicated branch; no direct commits to `main` (rule D6 in `docs/rules.md`).

## Documentation rules

- `README.md` is for end users: keep it short, and include a simple end-user scenario. Link out for anything more complex.
- Complex cases go in the relevant `docs/` file as a section. Do not grow `README.md`.
- Developer sections (setup, tests, tooling) live in `docs/development.md`. `README.md` only references them.
- Keep docs consistent with the code: defaults, flags, and model names must match `src/`.
- Separate **standard-use models** (end users, in `docs/spec.md`) from **development-only models** (docs and tooling, in `docs/development.md`). Never mix the two lists.

## Agent behavior rules

- **References over duplication**: When a value, threshold, URL, principle, or rule exists in a referenced document, reference it (e.g., "C7", "`docs/spec.md`") rather than repeating the value. Do not duplicate constants, numbers, or lists that are defined elsewhere.
- **Verify before writing**: Before emitting a specific value (confidence threshold, model name, URL, version number), check if it's defined in `docs/constitution.md`, `docs/spec.md`, `docs/development.md`, or `src/` config. If so, reference the source.
- **DRY across docs and code**: Configuration values (model names, endpoints, defaults) must match `src/` — reference or derive, never hardcode separately.
- **Honesty about confidence**: Models do not emit calibrated 95% probabilities. Use self-reported `confidence` in structured output. If the top score is below the threshold defined in `docs/spec.md`, show it. If another answer is within the margin defined in `docs/spec.md`, show that alternative too. Never claim statistical calibration.

> **Rule catalog:** See [`docs/rules.md`](rules.md) for the complete rule-to-check matrix (IDs, severity, enforcement).
