# Notebook Logic Extraction Summary

This document summarizes the processing logic extracted from the exploratory
notebooks in `data/`. It intentionally records the reusable logic rather than a
verbatim copy of notebook cells, so repository documentation remains in English.

## `data/etl_fasta.ipynb`

Purpose: convert raw source datasets into a shared FASTA representation.

Extracted reusable logic:

- CNNProm FASTA files are classified as promoter or non-promoter from filename
  suffixes and tagged as prokaryotic for Bacillus/Ecoli, otherwise eukaryotic.
- GraphPro positive/negative files are mapped from compact organism folder names
  to full dataset names; variable-length records are normalized to the minimum
  observed length before writing FASTA.
- Bhandari gzip-compressed FASTA files are decompressed, filtered to the most
  common sequence length when lengths vary, and tagged as eukaryotic except for
  yeast.
- iPro-MP files are read as FASTA-like TXT files, but the notebook did not write
  final FASTA outputs for this source.

Implemented in:

- `capsprom.data.fasta_builders`
- `capsprom.data.sequences`

## `data/prepare_data_cdbpro.ipynb`

Purpose: convert CDBProm line-oriented TXT files into FASTA.

Extracted reusable logic:

- Each non-empty line is treated as one sequence.
- Files containing `negative` are labeled as non-promoter; other files are
  labeled as promoter.
- CDBProm is tagged as prokaryotic.
- If sequence lengths vary, records with the most common length are retained.

Implemented in:

- `capsprom.data.fasta_builders.build_cdbprom_fastas`

## `data/crop_seqs.ipynb`

Purpose: crop source windows to the 81 bp model input length.

Extracted reusable logic:

- The target window is 60 bp upstream of the TSS, the TSS base, and 20 bp
  downstream.
- TSS positions are source-specific and depend on original sequence length.
- Cropped FASTA filenames preserve the original naming scheme while replacing
  the source length with `81`.

Implemented in:

- `capsprom.data.dataset_builders.crop_fasta_directory`
- `capsprom.data.sequences.crop_sequence`

## `data/eda_features.ipynb`

Purpose: exploratory analysis and dataset pairing.

Extracted reusable logic:

- Cropped FASTA filenames can be parsed into class, study, organism type,
  dataset, count, and length fields.
- Promoter and non-promoter files can be paired by study, organism type, and
  dataset name.
- K-mer frequency profiles can be used for exploratory distance analysis.
- Alignment-derived consensus/profile analysis is exploratory and should remain
  outside the first deterministic dataset construction pipeline.

Implemented in:

- `capsprom.data.dataset_builders.parse_fasta_name`
- `capsprom.data.dataset_builders.group_promoter_pairs`
- `capsprom.data.dataset_builders.build_intra_dataset_csvs`

## Current Boundary

The current refactoring captures deterministic dataset construction and strict
DNA cleaning. EDA plots, clustering, MAFFT alignment, and feature-analysis code
were not moved into the core pipeline yet because they are exploratory analysis
steps rather than required dataset construction stages.
