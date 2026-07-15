# Notebook Logic Extraction Summary

This document summarizes only the notebook logic relevant to the final
intra-source datasets in `data/processed/assembled_datasets/intra/`. The active
sources are Bhandari, CDBProm, CNNProm, and GraphPro. Other notebook fragments or
raw folders are out of scope unless they are later connected to new final
processed datasets.

## `data/etl_fasta.ipynb`

Purpose: convert active raw source datasets into a shared FASTA representation.

Extracted reusable logic:

- CNNProm FASTA files are classified as promoter or non-promoter from filename
  suffixes and tagged as prokaryotic for Bacillus/Ecoli, otherwise eukaryotic.
- GraphPro positive/negative files are mapped from compact organism folder names
  to full dataset names; variable-length records are normalized before writing
  FASTA.
- Bhandari gzip-compressed FASTA files are decompressed, filtered to the most
  common sequence length when lengths vary, and tagged as eukaryotic except for
  yeast.

Implemented in:

- `capsprom.data.fasta_builders.build_cnnprom_fastas`
- `capsprom.data.fasta_builders.build_graphpro_fastas`
- `capsprom.data.fasta_builders.build_bhandari_fastas`
- `capsprom.data.sequences`

## `data/prepare_data_cdbpro.ipynb`

Purpose: convert active CDBProm line-oriented TXT files into FASTA.

Extracted reusable logic:

- Each non-empty line is treated as one sequence.
- Files containing `negative` are labeled as non-promoter; other files are
  labeled as promoter.
- CDBProm is tagged as prokaryotic.
- If sequence lengths vary, records with the most common length are retained.

Implemented in:

- `capsprom.data.fasta_builders.build_cdbprom_fastas`

## `data/crop_seqs.ipynb`

Purpose: crop active source windows to the 81 bp model input length.

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

Purpose: exploratory analysis and active dataset pairing.

Extracted reusable logic:

- Cropped FASTA filenames can be parsed into class, study, organism type,
  dataset, count, and length fields.
- Promoter and non-promoter files can be paired by study, organism type, and
  dataset name.
- Final intra-source CSVs are built from those paired active datasets.

Implemented in:

- `capsprom.data.dataset_builders.parse_fasta_name`
- `capsprom.data.dataset_builders.group_promoter_pairs`
- `capsprom.data.dataset_builders.build_intra_dataset_csvs`

## Out-of-Scope Notebook Content

Notebook references to data sources not represented in
`data/processed/assembled_datasets/intra/` are excluded from current generated
project information. This includes iPro-MP, EDP, Fuitfly, previous prediction
archives, and other exploratory files.
