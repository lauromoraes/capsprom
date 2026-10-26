# AI Context

## What this project is

CapsProm is doctoral research on reproducible promoter prediction from 81-bp DNA using capsule networks. The active scientific question is whether a locked one-hot basic CapsProm can offer useful, stable performance relative to established baselines without leakage or invalid statistical independence assumptions.

## Preserve these decisions

- Active confirmatory scope is exactly the 18 eligible CDBProm/CNNProm datasets and 14 dependency clusters.
- GraphPro is excluded/deferred; preserve its artifacts but do not relabel, reconstruct, train, or claim confirmatory results.
- Bhandari is a synthetic-shuffle development control.
- MCC is primary; folds select within training, ten seeds measure algorithmic stability, clusters are inferential units, and test outcomes never select anything.
- Current basic CapsProm is one-hot k=1, LR 0.0001, 30 epochs, patience 15, decoder disabled. Variants need new model/config identities.
- Used YAML/state paths are immutable. Preserve hashes and MLflow run IDs.
- Final fit and external test are closed. Only explicitly bounded releases authorize remote training.

## Verified state

Classical infrastructure and neural resumability are implemented. The 50-job fixed-seed batch and 250-job XGBoost v2 replication are complete. Consolidation favors XGBoost on 17/18 datasets with median MCC difference 0.0681. A five-fold training-only CapsProm v4 tranche for Chlamydophila seed 13 completed and selected epoch 30; it is not a test result. No registered job is pending. The reviewed readiness/release/consolidation work is preserved in `315f5cc`; this handover is in the following documentation commit.

## Resources

Read `specs/`, `docs/roadmap.md`, `manifests/current_status.json`, `manifests/remote_jobs.json`, relevant YAML, experiment state under ignored `outputs/`, and MLflow SQLite databases. Use `.venv/`, `make check`, `make status`, and `make status-snapshot`. Remote details are in `ENVIRONMENT.md` and `RUNNING_TASKS.md`.

## Open problems

Verify that both versioning commits and required ignored artifacts are present; resolve the remaining XGBoost summary-path ambiguity; predeclare the next bounded seed only after review and authorization; then continue training-only campaign expansion. Confirmatory CapsProm comparison, final fits/tests, embeddings, SparseCapsProm, and GraphPro are not ready.

## Verification before advancing

Run Git/status checks, read the actual YAML gates, run focused tests then `make check`, verify config/dataset/fold hashes, ensure existing state paths are not being repurposed, inspect MLflow/state consistency, and confirm `external_test_accessed: false`. Do not infer completion from roadmap prose alone.

## Agent conduct

Write repository artifacts in English. Prefer the smallest change. Do not rerun completed experiments for context. Do not contact remote hosts, launch work, change scientific decisions, or expose credentials without explicit scope/authorization. Clearly label verified facts, decisions, hypotheses, and unknowns.
