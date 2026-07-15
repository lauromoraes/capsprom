# Biological Data Validation Report

Validated path: `data/processed/assembled_datasets/intra`

This report validates sequence-bearing files for DNA alphabet constraints, expected 81 bp processed CSV sequences, binary labels, and filename count consistency where available.

## Summary

- Total files inspected: 58
- Sequence-bearing files validated: 58
- Sequence-bearing files passed: 46
- Sequence-bearing files failed: 12
- Files requiring manual review: 0
- Valid sequence records in passed files: 462857

## Status Counts

- `fail`: 12
- `pass`: 46

## File Kind Counts

- `sequence_csv`: 58

## Failures

### `bhandari-eukaryotic-Human_promoter-p-196851-n-196851-train.csv`

- Kind: `sequence_csv`
- Records read: 393702
- Length range: 81-81
- Labels: {'0': 196851, '1': 196851}
- Issue: line 2077: invalid DNA symbols N
- Issue: line 2235: invalid DNA symbols N
- Issue: line 5699: invalid DNA symbols N
- Issue: line 8013: invalid DNA symbols N
- Issue: line 10298: invalid DNA symbols N
- Issue: line 15682: invalid DNA symbols N
- Issue: line 17291: invalid DNA symbols N
- Issue: line 17764: invalid DNA symbols N
- Issue: line 19350: invalid DNA symbols N
- Issue: line 20224: invalid DNA symbols N
- Issue: line 30322: invalid DNA symbols N
- Issue: line 32268: invalid DNA symbols N
- Issue: line 32654: invalid DNA symbols N
- Issue: line 32719: invalid DNA symbols N
- Issue: line 35643: invalid DNA symbols N
- Issue: line 35785: invalid DNA symbols N
- Issue: line 36552: invalid DNA symbols N
- Issue: line 37182: invalid DNA symbols N
- Issue: line 42784: invalid DNA symbols N
- Issue: line 44987: invalid DNA symbols N
- Issue: line 46721: invalid DNA symbols N
- Issue: line 53392: invalid DNA symbols N
- Issue: line 54625: invalid DNA symbols N
- Issue: line 54643: invalid DNA symbols N
- Issue: line 55332: invalid DNA symbols N

### `bhandari-eukaryotic-Human_promoter-p-49213-n-49213-test.csv`

- Kind: `sequence_csv`
- Records read: 98426
- Length range: 81-81
- Labels: {'1': 49213, '0': 49213}
- Issue: line 2018: invalid DNA symbols N
- Issue: line 4784: invalid DNA symbols N
- Issue: line 6443: invalid DNA symbols N
- Issue: line 6663: invalid DNA symbols N
- Issue: line 9012: invalid DNA symbols N
- Issue: line 9337: invalid DNA symbols N
- Issue: line 10829: invalid DNA symbols N
- Issue: line 12775: invalid DNA symbols N
- Issue: line 12874: invalid DNA symbols N
- Issue: line 13209: invalid DNA symbols N
- Issue: line 14670: invalid DNA symbols N
- Issue: line 16269: invalid DNA symbols N
- Issue: line 22723: invalid DNA symbols N
- Issue: line 23767: invalid DNA symbols N
- Issue: line 24667: invalid DNA symbols N
- Issue: line 26117: invalid DNA symbols N
- Issue: line 27198: invalid DNA symbols N
- Issue: line 32232: invalid DNA symbols N
- Issue: line 34064: invalid DNA symbols N
- Issue: line 35610: invalid DNA symbols N
- Issue: line 36295: invalid DNA symbols N
- Issue: line 45669: invalid DNA symbols N
- Issue: line 46697: invalid DNA symbols N
- Issue: line 47311: invalid DNA symbols N
- Issue: line 50481: invalid DNA symbols N

### `bhandari-eukaryotic-Plant_promoters-p-255636-n-255636-train.csv`

- Kind: `sequence_csv`
- Records read: 511272
- Length range: 81-81
- Labels: {'0': 255636, '1': 255636}
- Issue: line 10634: invalid DNA symbols N
- Issue: line 18653: invalid DNA symbols N
- Issue: line 25574: invalid DNA symbols N
- Issue: line 27918: invalid DNA symbols N
- Issue: line 37033: invalid DNA symbols N
- Issue: line 38275: invalid DNA symbols N
- Issue: line 97023: invalid DNA symbols N
- Issue: line 97846: invalid DNA symbols N
- Issue: line 97907: invalid DNA symbols N
- Issue: line 98689: invalid DNA symbols N
- Issue: line 111412: invalid DNA symbols N
- Issue: line 120417: invalid DNA symbols N
- Issue: line 126381: invalid DNA symbols N
- Issue: line 133025: invalid DNA symbols N
- Issue: line 143972: invalid DNA symbols N
- Issue: line 167826: invalid DNA symbols N
- Issue: line 174246: invalid DNA symbols N
- Issue: line 175411: invalid DNA symbols N
- Issue: line 202829: invalid DNA symbols N
- Issue: line 204427: invalid DNA symbols N
- Issue: line 218150: invalid DNA symbols N
- Issue: line 229813: invalid DNA symbols N
- Issue: line 237764: invalid DNA symbols N
- Issue: line 262088: invalid DNA symbols N
- Issue: line 284105: invalid DNA symbols N

### `bhandari-eukaryotic-Plant_promoters-p-63909-n-63909-test.csv`

- Kind: `sequence_csv`
- Records read: 127818
- Length range: 81-81
- Labels: {'0': 63909, '1': 63909}
- Issue: line 12622: invalid DNA symbols N
- Issue: line 26397: invalid DNA symbols N
- Issue: line 29742: invalid DNA symbols N
- Issue: line 33421: invalid DNA symbols N
- Issue: line 34498: invalid DNA symbols N
- Issue: line 40947: invalid DNA symbols N
- Issue: line 46200: invalid DNA symbols N
- Issue: line 49221: invalid DNA symbols N
- Issue: line 58065: invalid DNA symbols N
- Issue: line 67183: invalid DNA symbols N
- Issue: line 70329: invalid DNA symbols N
- Issue: line 74885: invalid DNA symbols N
- Issue: line 99794: invalid DNA symbols N
- Issue: line 100549: invalid DNA symbols N
- Issue: line 106267: invalid DNA symbols N
- Issue: line 112229: invalid DNA symbols N
- Issue: line 120146: invalid DNA symbols N

### `cdbprom-prokaryotic-helicobacter_pylori-p-1713-n-2272-train.csv`

- Kind: `sequence_csv`
- Records read: 3985
- Length range: 81-81
- Labels: {'0': 2272, '1': 1713}
- Issue: line 315: invalid DNA symbols Y
- Issue: line 1002: invalid DNA symbols Y
- Issue: line 2385: invalid DNA symbols Y
- Issue: line 2907: invalid DNA symbols Y
- Issue: line 2983: invalid DNA symbols Y
- Issue: line 3896: invalid DNA symbols Y

### `cdbprom-prokaryotic-pseudonomas_aeruginosa-p-1233-n-1640-test.csv`

- Kind: `sequence_csv`
- Records read: 2873
- Length range: 81-81
- Labels: {'0': 1640, '1': 1233}
- Issue: line 2727: invalid DNA symbols N

### `cdbprom-prokaryotic-pseudonomas_aeruginosa-p-4932-n-6556-train.csv`

- Kind: `sequence_csv`
- Records read: 11488
- Length range: 81-81
- Labels: {'0': 6556, '1': 4932}
- Issue: line 483: invalid DNA symbols N
- Issue: line 660: invalid DNA symbols N

### `cnnprom-eukaryotic-Arabidopsis_non_tata-p-14172-n-36668-train.csv`

- Kind: `sequence_csv`
- Records read: 50840
- Length range: 81-81
- Labels: {'0': 36668, '1': 14172}
- Issue: line 45800: invalid DNA symbols N
- Issue: line 48070: invalid DNA symbols N
- Issue: line 49544: invalid DNA symbols N

### `cnnprom-eukaryotic-Arabidopsis_non_tata-p-3543-n-9168-test.csv`

- Kind: `sequence_csv`
- Records read: 12711
- Length range: 81-81
- Labels: {'1': 3543, '0': 9168}
- Issue: line 4749: invalid DNA symbols N

### `cnnprom-eukaryotic-Human_non_tata-p-47546-n-88739-train.csv`

- Kind: `sequence_csv`
- Records read: 136285
- Length range: 81-81
- Labels: {'0': 88739, '1': 47546}
- Issue: line 2210: invalid DNA symbols N
- Issue: line 10422: invalid DNA symbols N
- Issue: line 124678: invalid DNA symbols N

### `graphpro-prokaryotic-leptospira_interrogans-p-1708-n-1693-test.csv`

- Kind: `sequence_csv`
- Records read: 3401
- Length range: 81-81
- Labels: {'0': 1693, '1': 1708}
- Issue: line 1824: invalid DNA symbols N

### `graphpro-prokaryotic-leptospira_interrogans-p-6833-n-6771-train.csv`

- Kind: `sequence_csv`
- Records read: 13604
- Length range: 81-81
- Labels: {'0': 6771, '1': 6833}
- Issue: line 2813: invalid DNA symbols N
- Issue: line 3702: invalid DNA symbols N
- Issue: line 7285: invalid DNA symbols N
- Issue: line 7387: invalid DNA symbols N
- Issue: line 7715: invalid DNA symbols N
- Issue: line 10071: invalid DNA symbols N
- Issue: line 10130: invalid DNA symbols N
- Issue: line 11080: invalid DNA symbols N
- Issue: line 12881: invalid DNA symbols N

## Manual Review Items

No files require manual review.

## Scope Notes

- Processed CSV files with `sequence,label` were checked for DNA alphabet, 81 bp length, binary labels, and filename count consistency.
- FASTA, FASTA-like TXT, and gzip-compressed sequence files were checked for DNA alphabet. Fixed length was enforced only when an expected length was encoded in the filename.
- Raw TXT files with one DNA sequence per line were checked for DNA alphabet, without fixed-length enforcement because raw sources may contain longer windows before cropping.
- Numeric feature CSVs, TSV physicochemical references, notebooks, scripts, and documentation were classified as not applicable for direct biological sequence validation.
- ZIP archives were inventoried but not expanded during validation; use extracted, named source directories for experimental inputs.
