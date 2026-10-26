# Continuation Roadmap

## P0 — Critical

1. **Completed — preserve the audited implementation state.** The coherent campaign/consolidation changes are in `315f5cc`; the handover is committed separately. No datasets, MLflow databases, models, predictions, or generated experiment outputs were committed.
2. **Keep scientific gates closed.** Dependency: none. Completion: no external-test, final-fit, GraphPro, or embedding execution occurs without a successor contract/release. Artifact: unchanged gate assertions/tests.
3. **Completed — resolve status/document contradictions.** `make status` names the post-v4 action, environment docs point to policy v3, and XGBoost v2 status exposes the exact `ten_seed_summary.json` path without changing the completed result.

## P1 — High priority

1. **Apply Ponytail to every refactoring slice.** Map callers, tests, fixtures, configs, and persisted contracts first; choose the smallest complete change; reuse existing code and dependencies; add no speculative abstraction. Never remove validation, atomic state, error handling, gates, provenance, or necessary tests to reduce code. See `PROJECT_INDEX.md`.
2. **Completed at the versioning checkpoint — validate readiness implementation.** The full suite passed with 160 tests, lint passed, and `make status-snapshot` was refreshed before `315f5cc`. Revalidate after future code changes.
3. **Predeclare the next bounded training-only release.** Dependencies: v4 tranche review, resource/integrity checks, explicit authorization. Completion: new immutable release YAML names only intended folds/seed; no final/test jobs. Artifact: release contract and review note.
4. **Execute and verify that tranche only if authorized.** Dependencies: remote parity, backup plan, release. Completion: released jobs finish or are safely resumable; SQLite, hashes, MLflow identities, state, and `external_test_accessed: false` verify. Artifacts: registry entry, report, checksums.
5. **Define the stop/continue rule for campaign expansion before observing more outcomes.** Completion: objective stability/resource/integrity criteria are versioned. Artifact: policy/config update with tests.

## P2 — Intermediate

1. Expand basic CapsProm training-only folds/seeds/datasets through bounded releases while preserving predeclared rules.
2. Complete the frozen final-refit/test implementation and fixtures, but keep execution disabled until the design and campaign are ready.
3. Predeclare the basic-CapsProm versus classical comparison using dependency clusters and multiplicity controls.
4. Design, version, and independently review embedding/multi-head comparisons; do not retrofit them into the one-hot baseline.
5. Produce thesis-ready results only after evidence classification and provenance review.

Each P2 item completes only with versioned contracts, passing tests, hash-linked state/MLflow artifacts, and a report that distinguishes exploratory from confirmatory evidence.

## P3 — Future

- SparseCapsProm, attention, conformal prediction, DNA-BERT fine-tuning, and broader baselines.
- Performance optimization and reusable abstractions only after three concrete workflows justify them.
- Revisit GraphPro only through a new explicit decision and new dataset identities.
- Improve automated handover/status generation while keeping scientific interpretation human-reviewable.
