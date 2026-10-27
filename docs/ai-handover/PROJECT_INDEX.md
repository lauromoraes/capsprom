# Project Index

Verified on 2026-10-26 at commit `af0788f6193be7670800fd178e1cdf41c9e0ea06` on branch `codex/estruturar-projeto-de-doutorado`. Use this compact index to route later investigation; authoritative detail remains in the linked contracts, state, and reports.

## Recovery path

1. Read `AGENTS.md`, `docs/ai-handover/README.md`, `AI_CONTEXT.md`, and `CURRENT_STATE.md`.
2. Run `git status --short`, `git rev-parse HEAD`, and `make status`.
3. Before scientific changes, read `specs/project_spec.md`, `specs/statistical_evaluation_protocol.md`, and `specs/capsprom_canonical_experiment.md`.
4. Check `RUNNING_TASKS.md`, then use `ROADMAP.md` for released work only.

## Logical map

| Area | Responsibility | Primary paths |
| --- | --- | --- |
| Contracts | Scientific, statistical, data, and execution invariants | `specs/`; versioned YAML in `configs/` |
| CLI/config | Command entry points and strict configuration | `src/capsprom/cli.py`, `config.py`, `runner.py` |
| Data | Loading, validation, reconstruction, leakage and dependency audits | `src/capsprom/data/`, `scripts/`, `data/` |
| Features | k-mer, one-hot, physicochemical, sequence-derived, DNA-BERT interfaces | `src/capsprom/features/` |
| Models | Classical, sequence-CNN, and basic CapsProm | `src/capsprom/models/` |
| Classical experiments | Execution, evaluation, tracking, batches, replication | `runner.py`, `evaluation.py`, `tracking.py`, `baseline_batch.py`, `xgboost_replication.py` |
| Neural experiments | Plan, training, resume, locks, MLflow identity, final/test gates | `canonical_neural.py`, `neural_training.py`, `neural_experiment.py` |
| Statistics | Paired and dependency-cluster-aware comparisons | `statistical_comparison.py`; `specs/statistical_evaluation_protocol.md` |
| Operations | Atomic state, local status, remote registry | `state.py`, `project_status.py`, `remote_operations.py`, `manifests/` |
| Verification | Unit, contract, workflow, resume, and gate coverage | `tests/`; `make check` |

The compatibility module `src/capsprom/experiment.py` is a thin facade over the already separated model, runner, evaluation, tracking, and data modules. Preserve it until callers are inventoried.

## Data and experiment map

- Active dataset: `data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/` (26 train/test pairs present; only 18 CDBProm/CNNProm identities eligible).
- Eligibility and dependence: `configs/dataset_eligibility_manifest_v1.yaml` and `configs/dataset_dependency_manifest_v2.yaml` (18 datasets, 14 inference clusters).
- Bhandari control: `data/processed/leakage_controlled/bhandari_human_shuffle_v1/`; synthetic-shuffle development control only.
- GraphPro: excluded/deferred by `configs/graphpro_deferral_policy_v1.yaml`; historical artifacts are provenance only.
- Evaluation: `configs/evaluation_protocol_v3.yaml`; design locked, confirmatory ranking disabled.
- Classical state: fixed-seed batch 50/50; XGBoost v2 250/250; active result in `outputs/reports/active_baseline_consolidation_v1/summary.json`.
- Neural state: GPU v4 Chlamydophila seed 13 folds 0-4 completed; training-only, selected epoch 30, external test not accessed. See `docs/capsprom_v4_seed13_training_report.md` and `manifests/remote_jobs.json`.
- Local storage: `configs/capsprom_local_storage_policy_v1.yaml` (8 GB budget); legacy `data/interim/{dinuc,trinuc,aligned_fasta,cropped_fasta}` and `outputs/neural_smoke/**/*.pt` archive to `bioserver04:/home/lauro/backups/capsprom/local-archive-v1` via `scripts/storage_archive.sh {check|copy|prune}`; `data/interim/ARCHIVED.md` appears after pruning.
  - Measured 2026-10-26 (pre-archive): `data/interim` 14 GB (`dinuc` 11 GB, `trinuc` 1.9 GB, `aligned_fasta` 719 MB, `cropped_fasta` 223 MB), `outputs/neural_smoke` 1.1 GB, `data/raw` 967 MB, `data/processed` 381 MB, `mlruns` 613 MB, `mlflow.db` 7 MB. Archive set ~15 GB; the remainder (~3.5 GB) fits the budget.
  - Verified 2026-10-26 after archive: project 2 GB of 8 GB budget; WSL Ubuntu-24.04 (only distro) lives at `D:\WSL\Ubuntu-24.04\ext4.vhdx` (47 GB); `.venv` depends on WSL `~/miniconda3` Python 3.13.11; `make status` passes from WSL; bioserver03 (RTX 3060 idle, 99 GB free) and bioserver04 (141 GB free) reachable, no CapsProm/MLflow process.
  - bioserver04 reachable from WSL Ubuntu-24.04 only with `-i ~/.ssh/capsprom_bioserver04` (the `~/.ssh/config` entry has no `IdentityFile`); 157 GB free; no GPU; no MLflow running.
  - Smoke configs reference `outputs/neural_smoke/*/best.pt`; those runs are complete, so pruning only blocks re-inspection until restored.
  - MLflow: no persistent server. Tracking URIs are SQLite paths inside immutable versioned configs, and remote campaigns already keep per-root `mlflow.db` on the execution host. Browse on demand: `ssh -L 5000:localhost:5000 <host> 'mlflow ui --backend-store-uri sqlite:///<root>/mlflow.db'`. shortcut: reconsider a server only when two concurrent hosts must write one store.
- No registered remote job is pending. Live remote state remains unverified and requires explicit authorization.

## Verified inconsistencies and limits

- Resolved 2026-10-26: root `README.md` stale layout tree replaced by a pointer to this index.
- Resolved: XGBoost v2 status explicitly reports `outputs/reports/xgboost_ten_seed_replication_v2/ten_seed_summary.json`; the active consolidation has its own `summary.json`.
- XGBoost v1 is superseded and incomplete (35/250); do not resume it by default.
- Ignored outputs and remote backup parity were not independently verified.
- 2026-10-26 audit: `project_status.py`, `tests/test_project_status.py`, and several handover files have mtimes after the last commit (`Refresh post-handover project status`); likely uncommitted. Confirm with `git status --short`.
- Resolved 2026-10-26: obsolete `AGENTS.md` `experiment.py` refactor rule replaced by a facade-preservation rule.
- GraphPro v1/v2 scripts duplicate `_load_hashed_fasta`/`_verify_hash`; keep as is (deferred line, provenance only).

## Refactoring queue (ENG)

Apply the [Ponytail](https://github.com/DietrichGebert/ponytail) smallest-complete-change ladder together with YAGNI, KISS, and DRY: reuse repository helpers first, then the standard library or an installed dependency; add no speculative abstraction or dependency; prefer deletion only after caller and contract checks. Never reduce trust-boundary validation, atomic persistence, error handling, security, scientific gates, provenance, or tests.

| Priority | Opportunity | Impact | Effort | Risk/dependency |
| --- | --- | --- | --- | --- |
| Done | Expose the exact XGBoost summary filename/path in status and handover | Medium | Low | Focused status test preserves the contract |
| P1 | Split `canonical_neural.py` (1,288 lines) along existing plan, fold runner, final-fit/external-evaluation, MLflow, and locked-state responsibilities | High | Medium-high | High scientific risk; characterization tests and behavior/hash equivalence first |
| P1 | Centralize only proven duplicate canonical state-update/MLflow identity paths | High | Medium | Do not generalize beyond the concrete neural workflows |
| P1 | `canonical_neural.py`: plan load + `protocol_sha256` check repeated 5x, `train_sha256` check 3x; extract one private verified-plan loader as the first split step | High | Low | Gate-critical; `tests/test_canonical_neural.py` must pass unchanged; add one mismatch test |
| P2 | `_sha256` redefined in `explainability.py`, `project_status.py`, `remote_operations.py`, `scripts/consolidate_active_baselines.py`; reuse `data.loading.sha256_file` | Medium | Low | Digest is byte-identical; keep chunked reading for large files |
| P2 | `_mapping` identical in 5 modules (`config`, `baseline_batch`, `xgboost_replication`, `neural_experiment`, `canonical_neural`); import from `config.py` | Low-medium | Low | Error messages unchanged; no new module |
| P2 | Contract hash expression repeated 3x in `neural_training.py`; one private `_contract_sha256()` | Low-medium | Low | Must yield identical hashes or resume breaks; test against an existing state file |
| P2 | Summary JSON written non-atomically in 3 scripts and `runner.py`; reuse `state.write_json_atomic` | Low-medium | Low | Scripts already use `sort_keys`+newline (byte-identical); `runner.py` does not, so leave it or version the change |
| P2 | Retire `experiment.py` facade: only callers are `cli.py`, `baseline_batch.py`, `xgboost_replication.py` (no tests) | Low | Low | Drop the `AGENTS.md` facade rule in the same change |
| P3 | Review broad optional dependency groups against exercised workflows | Low-medium | Low | Environment locks and remote compatibility must remain reproducible |

First refactoring slice completed: status/document path ambiguity fixed with one focused test and no experimental change. Next, create characterization tests for one bounded canonical inner-fold lifecycle before moving any neural orchestration code.

