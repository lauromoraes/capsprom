# CapsProm Agent Instructions

## Sources of Truth

- Read `specs/` before changing scientific behavior.
- Use `docs/roadmap.md` for current phase and `make status` for local execution state.
- Treat versioned YAML files as immutable contracts after their state file exists.
- Write repository documentation, code, comments, configuration, and experiment notes in English.

## Required Validation

- Run `make check` after code changes.
- Use focused tests during implementation, then the complete suite before committing.
- Run `make status-snapshot` at meaningful experimental checkpoints.
- Do not commit raw data, processed datasets, MLflow databases, models, predictions, or generated reports.

## Research Safety

- Never use test outcomes for model or feature selection.
- Preserve dataset and configuration hashes and MLflow run identifiers.
- Create a new versioned configuration and state path when data, features, seeds, models, output policy, or statistical inference changes.
- Verify scientific equivalence before reusing an earlier run.
- Keep long experiments resumable and persist their state atomically after each run.

## Scope Discipline

- Prefer the smallest change that satisfies the current research step.
- Do not introduce a generic framework until at least three concrete workflows require the same abstraction.
- Refactor `experiment.py` into model, tracking, evaluation, and runner modules before adding capsule-network training.
