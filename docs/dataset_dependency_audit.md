# Canonical Cross-Dataset Dependency Audit

## Status

This local audit covers the 26 canonical v3 dataset identities and does not
inspect model outcomes. Its exact-sequence component is reproducible with
`scripts/audit_cross_dataset_dependency.py`. The versioned dependency manifest
is provisional because absence of exact overlap does not establish independent
source pools or biological independence.

## Exact-sequence findings

Eight dataset pairs share at least one normalized 81 bp sequence when their
complete canonical train and test partitions are considered:

| Left dataset | Right dataset | Shared | Same label | Opposite label |
| --- | --- | ---: | ---: | ---: |
| CDBProm *B. amyloliquefaciens* | GraphPro *B. amyloliquefaciens* | 535 | 0 | 535 |
| CDBProm *C. pneumoniae* | GraphPro *C. phytofermentans* | 195 | 195 | 0 |
| CDBProm *S. typhimurium* | CNNProm *E. coli* | 1 | 1 | 0 |
| CNNProm Arabidopsis non-TATA | CNNProm Arabidopsis TATA | 1 | 1 | 0 |
| CNNProm human non-TATA | CNNProm mouse non-TATA | 25 | 25 | 0 |
| CNNProm mouse non-TATA | CNNProm mouse TATA | 5 | 5 | 0 |
| CNNProm *E. coli* | GraphPro *E. coli* | 16 | 1 | 15 |
| GraphPro human | GraphPro mouse | 1 | 1 | 0 |

These are cross-dataset findings. They do not invalidate the already verified
absence of exact train--test overlap within each canonical dataset. They do show
that treating all 26 dataset identities as independent statistical units would
be unsafe without a dependency policy.

The 535 opposite-label identities require source-level investigation before
biological interpretation because the same input receives promoter and non-
promoter labels across the two studies. The 195 shared positives between
apparently different organisms also require verification of source identifiers,
cropping provenance, and possible dataset naming or reuse.

## Provisional clusters

The initial manifest uses connected components of exact overlap as conservative
clusters. Singleton datasets remain provisional singleton clusters. Manual
review must still determine whether apparently disjoint datasets share an
original database, negative pool, organism collection, or derivation lineage.
Until that review is complete, `dependency_manifest_complete` remains false and
confirmatory cross-dataset ranking is blocked.

## Required completion work

1. Trace each dataset to its original accession or downloadable source file.
2. Verify organism labels for the Chlamydophila--Clostridium overlap.
3. Explain the cross-source label reversal for *B. amyloliquefaciens* and
   *E. coli*.
4. Determine whether CNNProm and GraphPro eukaryotic sets reuse EPDnew, DBTSS,
   or another shared source pool.
5. Freeze reviewed cluster identifiers before implementing the Wilcoxon and
   Friedman aggregation used in the thesis.
