# GraphPro Reconstructed Split Report

## Scope and contract

This report records the first deterministic train/test split of the six
bacterial `graphpro-reconstructed-v2` candidates. It is a data-integrity result,
not authorization for model training or confirmatory use. The immutable split
contract is `configs/graphpro_reconstructed_split_v1.yaml`, with SHA-256
`2aecaeecb3b0694efb178ba5b77fb400495b52d62f677c054c856976c5a28a90`.

Each reconstructed positive and its sampled genomic control remain a pair.
Pairs connected by any forward/reverse-complement Hamming distance of at most
eight form an indivisible similarity group. Groups are assigned by a
deterministic hash using seed 42 and a target test fraction of 0.20.

## Materialized counts

| Source key | Train pairs | Test pairs | Train rows | Test rows | Largest group |
| --- | ---: | ---: | ---: | ---: | ---: |
| BACILLUS | 850 | 213 | 1,700 | 426 | 1 |
| CJEJUNI_2 | 1,506 | 376 | 3,012 | 752 | 2 |
| CPNEUMONIAE | 423 | 106 | 846 | 212 | 1 |
| ECOLI | 198 | 50 | 396 | 100 | 1 |
| LINTERROGANS | 2,226 | 557 | 4,452 | 1,114 | 1 |
| RHODOBACTER_1 | 4,257 | 1,064 | 8,514 | 2,128 | 2 |
| **Total** | **9,460** | **2,366** | **18,920** | **4,732** | **2** |

Every train and test partition has an equal number of positive and negative
rows. The split summary SHA-256 is
`0bb74ed35cc15ba0f9f5e599bdf380390d1d76443932f5f37fec15ca74eb20ad`.

## Independent audit

The post-split audit rereads the partition files and directly searches all
train--test sequence pairs using minimum Hamming distance over forward and
reverse-complement orientations. It found:

- zero positive--control pair identifiers shared between partitions;
- zero similarity-group identifiers shared between partitions;
- zero exact or reverse-complement train--test identities;
- zero train--test neighbor edges at cumulative distances 1, 2, 4, and 8; and
- exact class balance in all 12 partition files.

The audit report SHA-256 is
`734d34fc07b7b105fa437279f36102bf430796fa3d1c1c0a03733009e50be6f2`.
A second build in a clean temporary directory reproduced all dataset manifests
and CSV files byte-for-byte.

## Remaining eligibility gates

These results close the split and within-dataset similarity-integrity gates.
They do not validate the biological labels or authorize predictive comparison.
Primary TSS source samples, dated EPD resolution for human and mouse,
distribution diagnostics, cross-dataset dependency auditing, licensing/source
archival, and independent manual review remain pending. Model-training and
confirmatory-use gates remain false.
