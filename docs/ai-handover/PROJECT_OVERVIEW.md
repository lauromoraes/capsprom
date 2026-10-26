# Project Overview

## Scientific purpose

CapsProm is a doctoral research codebase for binary promoter-region prediction from 81-bp DNA sequences. It aims to develop, evaluate, and interpret capsule-network models under reproducible data, tracking, and statistical protocols. The proposed families are CapsProm and SparseCapsProm; comparison families include logistic regression, XGBoost, CNNProm, iPro-MP, EDEN, and fine-tuned DNA-BERT.

## Hypotheses

- **Untested central hypothesis:** capsule networks may capture structured motif relationships more effectively than conventional encoders or standard neural models.
- **Partially supported development hypothesis:** basic CapsProm optimization instability is caused by early capsule-norm saturation rather than a disconnected capsule path. Training-only traces and learning-rate controls support this, but no confirmatory test was performed.
- **Verified baseline result, not a capsule claim:** on the active 18-dataset scope, ten-seed XGBoost outperformed deterministic logistic regression on 17 datasets; see `EXPERIMENTS.md`.

The central capsule hypothesis is not yet expressed as a completed confirmatory comparison. Do not infer it from feasibility runs, inner folds, or exploratory development data.

## Active scope

The active confirmatory source-negative scope is the 18 eligible CDBProm/CNNProm identities in `configs/dataset_eligibility_manifest_v1.yaml`, stored under `data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/`. Statistical units are the 14 dependency clusters in `configs/dataset_dependency_manifest_v2.yaml`.

The eight GraphPro identities are excluded and deferred by `configs/graphpro_deferral_policy_v1.yaml`. Historical GraphPro artifacts are exploratory provenance only. Bhandari human data is a separate synthetic-shuffle development control at `data/processed/leakage_controlled/bhandari_human_shuffle_v1/`, not a substitute for genomic negatives.

## Scientific boundaries

- Test outcomes must not select features, models, epochs, thresholds, or execution policy.
- Exact-sequence cleanliness does not prove biological label validity.
- One-hot basic CapsProm is the current canonical architecture boundary. Learned embeddings and multi-head variants require new identities and contracts.
- No final-fit or external-test CapsProm evaluation is released.
- Confirmatory ranking remains disabled in `configs/evaluation_protocol_v3.yaml`.
- GraphPro work cannot resume without a new explicit project decision.

Canonical sources: `specs/project_spec.md`, `docs/project_brief.md`, `docs/qualification_context.md`, and `docs/roadmap.md`.
