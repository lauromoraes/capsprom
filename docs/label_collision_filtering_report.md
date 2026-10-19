# Cross-Label Sequence Collision Filtering Report

## Problem Definition

A cross-label collision occurs when the same normalized 81 bp sequence is
assigned both promoter label 1 and non-promoter label 0 within one dataset.
Because the classifier receives only the 81 bp sequence, the two examples are
observationally identical and cannot be separated by any deterministic model.
Keeping both labels introduces irreducible label noise and makes exact-group
partitioning ambiguous.

## Provenance Investigation

Table `tab:cross-label-collision-origins` separates conflicts already present
before cropping from collisions introduced when distinct longer records map to
the same 81 bp window.

| Source | Dataset | Before cropping | After cropping | Introduced by cropping |
| --- | --- | ---: | ---: | ---: |
| CDBProm | anabaena_sp | 0 | 1 | 1 |
| CDBProm | mycrobacterium_tuberculosis | 0 | 1 | 1 |
| GraphPro | Human | 1 | 1 | 0 |
| GraphPro | escherichia_coli | 1,345 | 1,345 | 0 |
| Total | -- | 1,346 | 1,348 | 2 |

Table label: `tab:cross-label-collision-origins`.

The two CDBProm collisions involve different full-length positive and negative
records whose cropped windows become identical. Their sequence SHA-256 values
are `253335cac2b0d647b6d309cb6577c4257002fcc94c366391bf6d07199747cad8`
for Anabaena and
`1659dcedbb2ae77fa8d5033ae87e86d17d21d00516dfea5e8f23563684988a47`
for M. tuberculosis. The corresponding source record identifiers are 2226/2232
and 23/24, respectively.

The GraphPro human conflict uses source identifiers
`FP000174|SERTAD4-AS1_2` and `FP000175|SERTAD4-AS1_1`. The 1,345 GraphPro
E. coli conflicts occur in the source-provided positive and negative sets before
any project cropping; their records share the source identifier `NC_000913.2`.

## Mandatory Policy

After cropping and before train/test partitioning, the builder computes the
intersection of positive and negative sequence sets. Every occurrence of every
sequence in that intersection is removed from both classes. This policy is
mandatory and has no keep option. Removing both sides avoids choosing one label
without source evidence and prevents the same observable input from carrying
contradictory targets.

## Filtering Manifest

The regenerated-v3 filtering manifest records each stage per dataset. Across
the 26 pairs:

| Stage | Positive | Negative | Total |
| --- | ---: | ---: | ---: |
| After cropping | 77,554 | 106,147 | 183,701 |
| Removed as cross-label collisions | 1,348 | 1,348 | 2,696 |
| After collision filtering | 76,206 | 104,799 | 181,005 |
| Removed as same-label duplicates | 301 | 759 | 1,060 |
| After within-class deduplication | 75,905 | 104,040 | 179,945 |
| Removed by strict-DNA filtering | 6 | 2 | 8 |
| Final train | 60,717 | 83,229 | 143,946 |
| Final test | 15,182 | 20,809 | 35,991 |

Table label: `tab:cross-label-filtering-stages`.

The eight strict-DNA removals occur before splitting and are recorded separately
from collision and duplicate filtering. The JSON and CSV manifests are stored under
`data/processed/audits/real_negative_regenerated_v3/` together with dataset
hashes and the ordered filter contract:

```text
crop -> remove_cross_label_collisions -> deduplicate_within_class -> strict_dna -> group_safe_split
```

The final v3 audit contains zero duplicate rows, zero conflicting-label
sequences, and zero exact train/test overlap in all 26 pairs. Its identifier is
`87371a88ca1c5456db340201de5c19558b1a5773cb441787ffffc0803b66d853`.
