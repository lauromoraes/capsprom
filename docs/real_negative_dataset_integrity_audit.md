# Source-Provided Negative Dataset Integrity Audit

## Purpose

This report evaluates the legacy exact-sequence integrity in every strict-DNA CDBProm,
CNNProm, and GraphPro train/test pair. These sources include non-promoter
examples and were intended to support the primary biological benchmarks. The
audit follows `specs/dataset_integrity_audit.md` and excludes Bhandari, whose
synthetic-negative workflow has a separate corrective audit.

The deterministic audit identifier is
`59ba1a13ae21cfdd3e4fd992bfdce7ac0ba709f66f8cca2ec2a0afafff8d191b`.

## Aggregate Finding

Table `tab:real-negative-audit-by-source` summarizes the integrity outcomes by
source. None of the 26 pairs meets the strict acceptance rule. Across all
sources, 347,197 of 529,014 training rows (65.63%) and 31,849 of 132,272 test
rows (24.08%) are duplicate occurrences within their respective partitions.
Most importantly, 129,739 test rows (98.09%) belong to exact sequences also
present in training.

| Source | Pairs | Eligible | Train duplicate rows | Test duplicate rows | Shared unique sequences | Test rows in overlap | Test overlap (%) | Unique label conflicts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CDBProm | 11 | 0 | 56,628 | 5,094 | 16,639 | 21,413 | 97.86 | 2 |
| CNNProm | 7 | 0 | 231,293 | 21,270 | 66,166 | 86,338 | 98.19 | 0 |
| GraphPro | 8 | 0 | 59,276 | 5,485 | 16,828 | 21,988 | 97.90 | 1,346 |
| Total | 26 | 0 | 347,197 | 31,849 | 99,633 | 129,739 | 98.09 | 1,348 |

Table label: `tab:real-negative-audit-by-source`.

## Dataset Eligibility

Table `tab:real-negative-dataset-eligibility` reports the outcome for each
train/test pair. A conflict status takes precedence over overlap because a
sequence assigned to both classes makes the label definition ambiguous. Every
overlap-status pair also contains internal duplicate rows.

| Source | Domain | Dataset | Status | Train duplicates | Test duplicates | Shared sequences | Unique label conflicts |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| CDBProm | prokaryotic | anabaena_sp | conflicting_labels | 9,078 | 799 | 2,692 | 1 |
| CDBProm | prokaryotic | bacillus_amyloliquefaciens | train_test_overlap | 3,812 | 314 | 1,160 | 0 |
| CDBProm | prokaryotic | chlamydophila_pneumoniae | train_test_overlap | 1,459 | 139 | 422 | 0 |
| CDBProm | prokaryotic | corynebacterium_glutamicum | train_test_overlap | 2,082 | 190 | 609 | 0 |
| CDBProm | prokaryotic | helicobacter_pylori | train_test_overlap | 2,573 | 222 | 768 | 0 |
| CDBProm | prokaryotic | klebisiella_pneumoniae | train_test_overlap | 4,787 | 446 | 1,403 | 0 |
| CDBProm | prokaryotic | mycrobacterium_tuberculosis | conflicting_labels | 6,398 | 584 | 1,872 | 1 |
| CDBProm | prokaryotic | pseudonomas_aeruginosa | train_test_overlap | 7,400 | 656 | 2,201 | 0 |
| CDBProm | prokaryotic | salmonella_typhimurium | train_test_overlap | 3,525 | 321 | 1,038 | 0 |
| CDBProm | prokaryotic | streptomyces_coelicolor | train_test_overlap | 9,607 | 876 | 2,756 | 0 |
| CDBProm | prokaryotic | synechocistis | train_test_overlap | 5,907 | 547 | 1,718 | 0 |
| CNNProm | eukaryotic | Arabidopsis_non_tata | train_test_overlap | 33,544 | 3,101 | 9,546 | 0 |
| CNNProm | eukaryotic | Arabidopsis_tata | train_test_overlap | 8,447 | 781 | 2,404 | 0 |
| CNNProm | eukaryotic | Human_non_tata | train_test_overlap | 89,677 | 8,296 | 25,583 | 0 |
| CNNProm | eukaryotic | Mouse_non_tata | train_test_overlap | 77,632 | 7,075 | 22,374 | 0 |
| CNNProm | eukaryotic | Mouse_tata | train_test_overlap | 11,478 | 1,025 | 3,342 | 0 |
| CNNProm | prokaryotic | Bacillus | train_test_overlap | 2,728 | 255 | 763 | 0 |
| CNNProm | prokaryotic | Ecoli | train_test_overlap | 7,787 | 737 | 2,154 | 0 |
| GraphPro | eukaryotic | Human | conflicting_labels | 8,447 | 725 | 2,535 | 1 |
| GraphPro | eukaryotic | Mouse | train_test_overlap | 6,668 | 594 | 1,972 | 0 |
| GraphPro | prokaryotic | bacillus_amyloliquefaciens | train_test_overlap | 3,354 | 295 | 991 | 0 |
| GraphPro | prokaryotic | campylobacter_jejuni | train_test_overlap | 4,861 | 431 | 1,439 | 0 |
| GraphPro | prokaryotic | clostridium_phytofermentans | train_test_overlap | 1,654 | 144 | 501 | 0 |
| GraphPro | prokaryotic | escherichia_coli | conflicting_labels | 13,409 | 1,454 | 3,142 | 1,345 |
| GraphPro | prokaryotic | leptospira_interrogans | train_test_overlap | 8,664 | 782 | 2,590 | 0 |
| GraphPro | prokaryotic | rhodobacter_capsulatus | train_test_overlap | 12,219 | 1,060 | 3,658 | 0 |

Table label: `tab:real-negative-dataset-eligibility`.

## Consequences

The current fixed partitions must not support confirmatory model ranking. The
overlap pattern is consistent with repeated sequence occurrences having been
distributed across partitions, although determining the exact originating
processing step requires tracing each source-specific builder. The next data
version must resolve conflicting labels with a predeclared exclusion rule,
collapse exact sequence groups, and assign each group wholly to train or test.
Source-provided non-promoters must be retained; no synthetic negatives should be
introduced for these datasets.

The provenance investigation subsequently traced the dominant replication to
append-mode writes in the legacy cropping notebook. The corrected regeneration
and its before-and-after audit are reported in
`docs/real_negative_dataset_regeneration_report.md`. This report remains the
audit record for the contaminated legacy partitions.

The generated JSON, CSV, and Markdown artifacts are stored under
`data/processed/audits/real_negative_v1/` and can be reproduced with:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_real_negative_datasets.py
```
