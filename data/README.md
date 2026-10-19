# Data Directory

## Active Intra-Source Scope

The canonical source-negative datasets in
`data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/` are the
validated confirmatory inputs for CDBProm, CNNProm, and GraphPro. The legacy
strict-DNA datasets in `intra_strict_dna/` remain development and provenance
inputs only because their fixed partitions contain exact overlap. The original processed files in
`data/processed/assembled_datasets/intra/` are preserved for provenance and
preprocessing audit. The in-scope source prefixes are `bhandari`, `cdbprom`,
`cnnprom`, and `graphpro`.

Exception: Bhandari human experiments must use the leakage-controlled dataset
in `data/processed/leakage_controlled/bhandari_human_shuffle_v1/`. The legacy
Bhandari human files under `intra_strict_dna/` are retained only for provenance
and contaminated-split comparability.

The CDBProm, CNNProm, and GraphPro audit identified exact train/test overlap in
all 26 pairs; 98.09% of their combined test rows belong to sequences present in
training. Corrected group-safe versions must preserve their source-provided
non-promoter examples. The deterministic audit identifier is
`59ba1a13ae21cfdd3e4fd992bfdce7ac0ba709f66f8cca2ec2a0afafff8d191b`.

The active corrected rebuild is `intra_regenerated_v3_strict_dna`. It corrects
append-mode output, removes every cross-label collision bilaterally, removes
same-label exact duplicates, applies the strict-DNA filter, and assigns unique
sequence groups deterministically to train or test. Across the 26 pairs, the
build removes 1,348 positive and 1,348 negative collision rows, 301 positive
and 759 negative duplicate rows, and eight invalid-DNA rows. All 26 pairs pass
the exact-integrity audit. Its deterministic audit identifier is
`87371a88ca1c5456db340201de5c19558b1a5773cb441787ffffc0803b66d853`.

Filtering provenance is recorded in
`data/processed/audits/real_negative_regenerated_v3/filtering_manifest.json`
and `.csv`. These artifacts report, per dataset and stage, how many rows entered,
were removed, and remained after cropping, cross-label collision removal,
partitioning, and strict-DNA filtering. Generated datasets and audit artifacts
are intentionally ignored by Git; the builder, configuration, tests, and
documentation are versioned.

This directory contains research datasets and intermediate data artifacts for
CapsProm. Large data files are intentionally ignored by Git; only lightweight
metadata and documentation should be versioned.

## Current Layout

```text
data/
├── raw/                         # Original source datasets and references
├── interim/                     # FASTA conversion, cropped sequences, and feature intermediates
├── processed/assembled_datasets # CSV datasets ready for pipeline experiments
│   └── intra_strict_dna          # Cleaned CSV copies with strict A/C/G/T sequences
├── processed/leakage_controlled  # Deduplicated, group-split corrective datasets
└── *.ipynb                      # Legacy or exploratory preparation notebooks
```

## Processed Dataset Contract

The current source-negative model-ready CSV files under
`data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/` match the
project contract used by the confirmatory pipeline:

- Column `sequence`: DNA sequence.
- Column `label`: binary class label.
- Expected sequence length: 81 bp.
- Expected alphabet: `A`, `C`, `G`, `T`.
- Filename convention includes source study, organism/group, positive count,
  negative count, and partition.

Example:

```text
data/processed/assembled_datasets/intra_strict_dna/bhandari-eukaryotic-Human_promoter-p-196756-n-196757-train.csv
```

## Git Policy

The repository tracks this README and configuration files that reference data,
but it does not track raw, interim, processed, model, or run-output artifacts.
This keeps the GitHub repository usable while preserving reproducible paths in
configuration files.

## Notes for Future Cleanup

- Replace temporary folder names such as `Nova pasta` with descriptive source
  names after confirming their provenance.
- Convert reusable notebook logic into versioned Python modules before relying
  on it in the experimental pipeline.
- Add dataset inventory metadata before running large comparison experiments.

## Cleaned Processed Datasets

`data/processed/assembled_datasets/intra_strict_dna/` contains cleaned copies of all processed intra-study CSV datasets. Original processed CSVs are preserved unchanged. Cleaning removes only rows whose `sequence` contains characters outside `A`, `C`, `G`, and `T`; filenames in the cleaned directory use updated positive and negative counts.

