# Dataset Integrity Audit

## Purpose

Before a source-provided promoter/non-promoter dataset is admitted to baseline
or confirmatory experiments, its fixed train/test pair must pass a reproducible
sequence-integrity audit. The audit is independent of model configuration and
uses normalized uppercase DNA sequences as the identity key.

## Scope

The first batch audit covers the strict-DNA CDBProm, CNNProm, and GraphPro CSV
files under `data/processed/assembled_datasets/intra_strict_dna/`. Bhandari is
excluded because its promoter-only source and synthetic-negative correction are
specified separately.

## Pair Discovery

Files must follow the project naming convention and end in either `-train.csv`
or `-test.csv`. A dataset identity consists of source, domain, and dataset name.
Exactly one train and one test file must exist for each identity.

## Measurements

For each pair, record:

- train and test rows, class counts, unique sequences, and SHA-256 hashes;
- duplicate rows within each partition;
- sequences associated with conflicting labels within either partition;
- exact sequences shared between train and test;
- train and test rows belonging to shared sequences;
- shared sequences with conflicting labels;
- overlap counts separated by positive and negative label when labels agree.

## Eligibility Rules

Dataset construction must remove cross-label collisions before train/test
partitioning. After cropping and sequence normalization, let (C) be the set of
sequences observed with both labels. Every occurrence whose sequence belongs to
(C) is removed from both classes. Keeping one label would require an
unsupported relabeling decision and is therefore not permitted. A filtering
manifest must record the input, removed, and remaining row counts for every
dataset at cropping, collision removal, partitioning, and strict-DNA filtering.

A pair is `eligible` only when it contains both classes in both partitions and
has zero internal duplicate rows, zero label conflicts, and zero exact
train/test overlap. Otherwise it is classified as:

- `invalid`: the CSV contract, pairing contract, alphabet, length, or labels
  cannot be validated;
- `conflicting_labels`: one or more normalized sequences have inconsistent
  labels;
- `train_test_overlap`: exact sequences cross the partition boundary;
- `internal_duplicates`: duplicate rows occur within a partition but not across
  partitions.

The classifications are ordered by severity as listed above. A non-eligible
pair must not enter a confirmatory experiment until a source-aware correction
and a new immutable manifest are defined.

## Artifacts

The build command writes JSON and CSV filtering manifests plus a build report.
The batch audit then writes a machine-readable JSON report, a flat CSV summary,
and a Markdown report with the criteria, aggregate counts, and one row per
dataset. The report records a deterministic audit identifier derived from the
input file hashes and audit settings.
