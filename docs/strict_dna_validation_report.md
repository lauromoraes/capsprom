# Biological Data Validation Report

This report validates sequence-bearing files in `data/` for DNA alphabet constraints, expected 81 bp processed CSV sequences, binary labels, and filename count consistency where available.

## Summary

- Total files inspected: 60
- Sequence-bearing files validated: 58
- Sequence-bearing files passed: 58
- Sequence-bearing files failed: 0
- Files requiring manual review: 0
- Valid sequence records in passed files: 1828924

## Status Counts

- `not_applicable`: 2
- `pass`: 58

## File Kind Counts

- `non_sequence_artifact`: 1
- `non_sequence_csv`: 1
- `sequence_csv`: 58

## Failures

No sequence-bearing files failed validation.

## Manual Review Items

No files require manual review.

## Scope Notes

- Processed CSV files with `sequence,label` were checked for DNA alphabet, 81 bp length, binary labels, and filename count consistency.
- FASTA, FASTA-like TXT, and gzip-compressed sequence files were checked for DNA alphabet. Fixed length was enforced only when an expected length was encoded in the filename.
- Raw TXT files with one DNA sequence per line were checked for DNA alphabet, without fixed-length enforcement because raw sources may contain longer windows before cropping.
- Numeric feature CSVs, TSV physicochemical references, notebooks, scripts, and documentation were classified as not applicable for direct biological sequence validation.
- The `predictions_ecoli` folder was explicitly ignored by request and is outside this validation report.
- ZIP archives were inventoried but not expanded during validation; use extracted, named source directories for experimental inputs.
