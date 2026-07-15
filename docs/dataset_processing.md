# Dataset Processing Workflow

This document describes the reusable processing workflow used to construct the
CapsProm promoter prediction datasets from the original source files. It is
intended to support both software reproducibility and thesis writing.

## Source Normalization

The raw datasets originate from multiple studies and use heterogeneous formats,
including FASTA files, gzip-compressed FASTA files, and line-oriented TXT files.
The first processing stage converts these inputs into a common FASTA naming
scheme:

```text
[class]-[study]-[organism_type]-[dataset]-[count]-[length].fa
```

Where `class` is either `prom` or `nonprom`, `study` identifies the source
study, `organism_type` is `eukaryotic` or `prokaryotic`, `dataset` identifies
the organism or benchmark subset, `count` is the number of records, and `length`
is the sequence length before the 81 bp crop.

Reusable implementation:

- `capsprom.data.fasta_builders.build_cnnprom_fastas`
- `capsprom.data.fasta_builders.build_graphpro_fastas`
- `capsprom.data.fasta_builders.build_bhandari_fastas`
- `capsprom.data.fasta_builders.build_cdbprom_fastas`

## Sequence Length Normalization

All model-ready sequences are normalized to 81 bp around the transcription start
site (TSS). The crop contains 60 bp upstream, the TSS base, and 20 bp downstream.
The TSS positions are dataset-specific because the source windows differ across
studies.

| Study | Source length | TSS position | Output length |
| --- | ---: | ---: | ---: |
| GraphPro | 81 | 60 | 81 |
| CNNProm | 81 | 60 | 81 |
| CNNProm | 251 | 200 | 81 |
| CDBProm | 100 | 60 | 81 |
| CDBProm | 1001 | 500 | 81 |
| Bhandari et al. | 1000 | 700 | 81 |

Reusable implementation:

- `capsprom.data.dataset_builders.crop_fasta_directory`
- `capsprom.data.sequences.crop_sequence`

## Processed CSV Construction

After cropping, promoter and non-promoter FASTA files are paired by source
study, organism type, and dataset name. Each paired dataset is converted into a
CSV with two columns:

| Column | Meaning |
| --- | --- |
| `sequence` | 81 bp DNA sequence |
| `label` | Binary label: `1` for promoter, `0` for non-promoter |

The intra-study processed datasets follow this naming convention:

```text
[study]-[organism_type]-[dataset]-p-[positive_count]-n-[negative_count]-[partition].csv
```

Reusable implementation:

- `capsprom.data.dataset_builders.build_intra_dataset_csvs`
- `capsprom.data.dataset_builders.write_labeled_csv`

## Strict DNA Cleaning

The final strict-DNA dataset directory removes only rows whose `sequence`
contains characters outside the alphabet `A`, `C`, `G`, and `T`. Original CSV
files are preserved unchanged. Cleaned filenames use updated positive and
negative counts after row removal.

Current cleaned directory:

```text
data/processed/assembled_datasets/intra_strict_dna/
```

Current cleaning result:

- Source processed CSV files: 58.
- Cleaned processed CSV files: 58.
- Files with removed rows: 12.
- Total removed rows: 338.
- Post-cleaning validation failures: 0.

Reusable implementation:

- `capsprom.data.dataset_builders.clean_processed_csv`
- `capsprom.data.dataset_builders.clean_processed_directory`
- `scripts/clean_processed_datasets.py`

## Reproducibility Notes

The notebook-derived logic is now available as versioned Python functions under
`src/capsprom/data/`. The notebooks can remain useful for exploration, but the
experimental pipeline should call these modules directly. This ensures that
future MLflow runs can record deterministic processing code, configuration, and
input/output paths.
