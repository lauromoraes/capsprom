# Dataset Processing Workflow

This document describes the processing workflow for the active CapsProm
intra-source datasets. The active scope is restricted to the final CSV files in:

```text
data/processed/assembled_datasets/intra_strict_dna/
```

These files come only from the Bhandari, CDBProm, CNNProm, and GraphPro source
groups. Other files that may exist under `data/` are outside the current
experimental dataset scope.

## Active Sources

| Source prefix | Final intra-source CSV files |
| --- | ---: |
| `bhandari` | 6 |
| `cdbprom` | 22 |
| `cnnprom` | 14 |
| `graphpro` | 16 |

Total final intra-source CSV files: 58.


## Source Provenance

The active source folders contain README files documenting the origin of the raw
data used to build the final intra-source datasets. These README files identify
the source publications and repositories for Bhandari et al., CDBProm, CNNProm,
and GraphPro. A consolidated provenance summary is provided in
`docs/source_provenance.md`.

The README files also provide methodological context that should be preserved in
thesis writing and experiment reporting:

| Source | README-derived context relevant to this project |
| --- | --- |
| Bhandari et al. | Dataset associated with a cross-species promoter prediction comparison by Bhandari, Khare, Walambe, and Kotecha. |
| CDBProm | Dataset obtained from the CDBProm website and training-sequence archive described by Martinez et al. |
| CNNProm | Dataset obtained from CNNPromoterData and Softberry; the README documents distinct upstream resources for promoters and notes that bacterial non-promoters were sampled from opposite-strand coding fragments. |
| GraphPro | Dataset obtained from the GraphPro repository; the README records eukaryotic human/mouse data and bacterial data for six organisms. |

## Source Normalization

The active sources originally use heterogeneous formats, including FASTA,
gzip-compressed FASTA, and line-oriented TXT files. The processing notebooks
normalized these sources into a common FASTA naming scheme:

```text
[class]-[study]-[organism_type]-[dataset]-[count]-[length].fa
```

Where `class` is either `prom` or `nonprom`, `study` identifies one of the active
source groups, `organism_type` is `eukaryotic` or `prokaryotic`, `dataset`
identifies the organism or benchmark subset, `count` is the number of records,
and `length` is the sequence length before the 81 bp crop.

Reusable implementation:

- `capsprom.data.fasta_builders.build_cnnprom_fastas`
- `capsprom.data.fasta_builders.build_graphpro_fastas`
- `capsprom.data.fasta_builders.build_bhandari_fastas`
- `capsprom.data.fasta_builders.build_cdbprom_fastas`

## Sequence Length Normalization

All model-ready sequences are normalized to 81 bp around the transcription start
site (TSS). The crop contains 60 bp upstream, the TSS base, and 20 bp downstream.
The TSS positions are source-specific because the source windows differ across
active studies.

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

## Final CSV Construction

After cropping, promoter and non-promoter FASTA files were paired by source
study, organism type, and dataset name. Each pair was converted into CSV files
containing two fields:

| Column | Meaning |
| --- | --- |
| `sequence` | 81 bp DNA sequence |
| `label` | Binary label: `1` for promoter, `0` for non-promoter |

The final intra-source datasets follow this naming convention:

```text
[study]-[organism_type]-[dataset]-p-[positive_count]-n-[negative_count]-[partition].csv
```

Reusable implementation:

- `capsprom.data.dataset_builders.build_intra_dataset_csvs`
- `capsprom.data.dataset_builders.write_labeled_csv`

## Strict DNA Cleaning

The strict-DNA directory preserves all 58 final intra-source files as cleaned
copies. Cleaning removes only rows whose `sequence` contains characters outside
`A`, `C`, `G`, and `T`. Original final CSV files are preserved unchanged.
Cleaned filenames use updated positive and negative counts after row removal.

Current cleaned directory:

```text
data/processed/assembled_datasets/intra_strict_dna/
```

Current cleaning result:

- Source final intra-source CSV files: 58.
- Cleaned intra-source CSV files: 58.
- Files with removed rows: 12.
- Total removed rows: 338.
- Post-cleaning validation failures: 0.

Reusable implementation:

- `capsprom.data.dataset_builders.clean_processed_csv`
- `capsprom.data.dataset_builders.clean_processed_directory`
- `scripts/clean_processed_datasets.py`

## Reproducibility Boundary

Notebook-derived code has been refactored into `src/capsprom/data/`, but active
project documentation should only describe the subset that produced the final
intra-source CSV files. Exploratory notebooks, prediction archives, and raw data
not represented by `data/processed/assembled_datasets/intra_strict_dna/` are out of scope
for the current experiments.
