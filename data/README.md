# Data Directory

## Active Intra-Source Scope

Only the data used to create `data/processed/assembled_datasets/intra/` is currently in scope for generated project information, validation summaries, and thesis text. The active source prefixes are `bhandari`, `cdbprom`, `cnnprom`, and `graphpro`. Other folders may remain present for provenance or future work, but they are out of scope until explicitly added to a processed dataset specification.

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
└── *.ipynb                      # Legacy or exploratory preparation notebooks
```

## Processed Dataset Contract

The current processed CSV files under `data/processed/assembled_datasets/` match
the project contract used by the MVP pipeline:

- Column `sequence`: DNA sequence.
- Column `label`: binary class label.
- Expected sequence length: 81 bp.
- Expected alphabet: `A`, `C`, `G`, `T`.
- Filename convention includes source study, organism/group, positive count,
  negative count, and partition.

Example:

```text
data/processed/assembled_datasets/intra/bhandari-eukaryotic-Human_promoter-p-196851-n-196851-train.csv
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

