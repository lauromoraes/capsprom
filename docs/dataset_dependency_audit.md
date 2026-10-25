# Canonical Cross-Dataset Dependency Audit

## Status

This local audit covers the 26 canonical v3 dataset identities and does not
inspect model outcomes. Its exact-sequence component is reproducible with
`scripts/audit_cross_dataset_dependency.py`. The versioned dependency manifest
v1 remains the historical all-source audit. Source-label review subsequently
excluded all eight GraphPro identities from confirmatory inference. The reviewed
18-dataset, 14-cluster scope is frozen in
`configs/dataset_dependency_manifest_v2.yaml`; absence of exact overlap still
does not establish biological independence.

## Exact-sequence findings

Eight dataset pairs share at least one normalized 81 bp sequence when their
complete canonical train and test partitions are considered:

| Left dataset | Right dataset | Shared | Same label | Opposite label |
| --- | --- | ---: | ---: | ---: |
| CDBProm *B. amyloliquefaciens* | GraphPro *B. amyloliquefaciens* | 535 | 0 | 535 |
| CDBProm *C. pneumoniae* | GraphPro `Cpne` (legacy name: *C. phytofermentans*) | 195 | 195 | 0 |
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

## Confirmatory clusters

The initial manifest used connected components of exact overlap as conservative
clusters. Version 2 additionally groups known shared source pools and excludes
GraphPro rather than attempting unsupported relabeling. It contains 14 clusters,
which is above the predeclared minimum of ten for cross-dataset inference.
Confirmatory ranking nevertheless remains blocked until the statistical
aggregation fixtures pass.

## Remaining work

1. Implement and fixture-test cluster-level Wilcoxon and Friedman aggregation.
2. Independently reconstruct or source-verify GraphPro labels before any future
   reinstatement in a new dataset contract.
3. Retain all GraphPro and canonical-v3 results as explicitly exploratory
   provenance.
