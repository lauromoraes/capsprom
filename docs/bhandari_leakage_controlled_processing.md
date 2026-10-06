# Leakage-Controlled Bhandari Human Dataset

## Purpose

This workflow replaces the contaminated legacy Bhandari human split with a
deterministic dataset built directly from the downloaded raw FASTA. It removes
exact positive duplicates before partitioning, makes negative generation
explicit, and assigns each positive--negative pair wholly to one partition.

## Raw Provenance

The source is `data/raw/Bhandari_etal/Human_promoter.fa`, whose SHA-256 is
`be6befb98673fc70a7135c21742461038470b40b56cfaff830812b1e9b72e2e5`.
This file is byte-identical to the decompressed `Human_promoter.gz` download.

The raw source contains 61,546 records. The workflow retains the 61,516 records
with the modal length of 1,000 bp, crops positions 640--720 around the declared
TSS at position 700, removes 30 non-strict-DNA windows, and collapses exact
81-bp duplicates. This produces 33,925 unique positive windows and removes
27,561 duplicate positive occurrences.

## Negative Generation

The raw source provides promoter windows but no explicit non-promoter class.
For each unique positive window, the workflow creates one deterministic
mononucleotide shuffle. The shuffle preserves the positive sequence's A, C, G,
and T counts while changing nucleotide order. Candidate negatives are rejected
when they equal any positive or previously generated negative.

The random state for each shuffle is derived from the global seed and the
positive sequence hash. Generation is therefore stable even if raw record order
changes. This method is versioned as
`bhandari-deduplicated-mononucleotide-shuffle-v1`.

Synthetic shuffled negatives isolate sequence-order signal under a controlled
composition distribution. They do not represent real genomic non-promoter
regions and must not be used alone to support claims about genome-wide false
positive behavior. Experiments using this dataset must be labeled as
shuffle-control experiments.

## Grouped Split

Each positive and its derived negative form one indivisible group. Groups are
shuffled with seed 42 and assigned approximately 80/20 to train and test.
Table `tab:bhandari-leakage-controlled-counts` summarizes the resulting dataset.

| Partition | Positive | Negative | Total | Unique sequences |
| --- | ---: | ---: | ---: | ---: |
| Train | 27,140 | 27,140 | 54,280 | 54,280 |
| Test | 6,785 | 6,785 | 13,570 | 13,570 |
| Total | 33,925 | 33,925 | 67,850 | 67,850 |

Table label: `tab:bhandari-leakage-controlled-counts`.

The train SHA-256 is
`1cdb2180ab1025cf77cb24f3cb3fc763d3ab147616ee1f77c9bc4bff554222be`,
the test SHA-256 is
`8e570bcbc39d502c7f3480a1b114d4963a37bcff95fdb168caabb37783160836`,
and the group-manifest SHA-256 is
`a236b9db5be8d55d66880cd37a4f35a91e0d9b58f86adb8a1558b9631f0d22f6`.

## Acceptance Audit

The generated train and test files contain no duplicate sequences, no
conflicting labels, and no exact sequence shared across partitions. The group
manifest stores positive and negative sequence hashes, raw positive
multiplicity, and partition assignment without reproducing raw sequences.

## Reproduction

From the repository root, run:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_bhandari_leakage_controlled.py
PYTHONPATH=src .venv/bin/python -m capsprom audit-data configs/leakage_controlled_logistic.yaml
```
