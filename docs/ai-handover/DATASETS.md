# Datasets

## Active confirmatory inventory

**Verified:** the active root `data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/` contains train/test CSV pairs for 26 identities (52 files). Eligibility is narrower: 11 CDBProm and 7 CNNProm identities are active; 8 GraphPro identities are excluded. Do not derive active scope by listing the directory—always apply `configs/dataset_eligibility_manifest_v1.yaml`.

CSV semantics are `sequence` (81 bp, uppercase A/C/G/T) and binary `label` (0 non-promoter, 1 promoter). Filenames encode study, organism, counts, and partition. Dataset and filtering hashes are recorded by the builders/manifests rather than duplicated here.

## Provenance and treatments

- `data/processed/assembled_datasets/intra/`: original processed audit source; not active.
- `.../intra_strict_dna/`: legacy strict-DNA derivative; not active.
- regenerated v1/v2: retained historical correction stages; not active.
- `.../intra_regenerated_v3_strict_dna/`: canonical v3 active build.
- `data/processed/leakage_controlled/bhandari_human_shuffle_v1/`: group-safe synthetic-shuffle development control.

Canonical v3 order is: crop to 81 bp; remove every post-crop cross-label collision from both classes; deduplicate within each class; enforce strict DNA; split deterministic unique-sequence groups. The build removed 1,348 conflicting sequences from each class (2,696 rows total), then 301 positive and 759 negative duplicate rows. All 26 pairs pass exact-identity checks, but biological semantics independently exclude GraphPro.

## Eligibility and dependency

The 18 eligible datasets form 14 audited dependency clusters in `configs/dataset_dependency_manifest_v2.yaml`. Shared source pools and exact overlap prevent treating all dataset identities as independent. Exact overlap absence is not proof of biological independence.

GraphPro exclusions include strand/class confounding in five bacterial folders, 1,345 duplicated raw E. coli records across classes, 535 Bacillus negatives matching CDBProm positive windows, unverified eukaryotic negative lineage, and the incorrect legacy `Cpne` organism mapping. The Promotech E. coli BED is a pAA plasmid supplement whose coordinates were incorrectly applied to MG1655; descendants of that mapping are invalidated. See `docs/source_label_semantics_audit.md`, `docs/dataset_dependency_audit.md`, and GraphPro reports.

## Positive and negative definitions

CDBProm and CNNProm retain source-provided promoter/non-promoter definitions documented by their sources. GraphPro labels are not eligible. Bhandari generates one deterministic shuffled negative per deduplicated positive and is explicitly synthetic. Source-native, GC-matched genomic, synthetic-shuffle, CDS-derived, and multi-negative conditions must retain separate identities under `specs/negative_control_protocol.md`.

## Validation and gaps

Canonical v3 has exact-collision, duplicate, overlap, strict-DNA, and near-duplicate audit support. Source-level semantics remain the limiting criterion. Do not use the older `docs/processed_dataset_validation_summary.md` counts as active-v3 counts; that report explicitly audits older `intra/` and legacy strict-DNA directories.

Reproducibility references: `specs/project_spec.md`, `specs/dataset_integrity_audit.md`, `docs/dataset_processing.md`, `docs/real_negative_dataset_regeneration_report.md`, `docs/label_collision_filtering_report.md`, and `docs/intra_source_data_scope.md`.
