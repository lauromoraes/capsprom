# GraphPro Reconstruction Feasibility

## Outcome

The six bacterial datasets can be reconstructed from independent TSS tables and
matching reference assemblies distributed by the official Promotech repository.
This is a feasibility result, not a release of model-ready datasets and not a
validation of the original GraphPro labels. Human and mouse remain blocked on
resolution of their `FP` identifiers against a dated EPD release.

The candidate source was inspected at Promotech commit
`56251ad9b883ef831b4753fc623d5ec970fe65e0`. Its BED6 files provide point TSS
features with strand, while its FASTA files provide the corresponding versioned
assemblies. These inputs are traceable to the Promotech paper and its primary
TSS-source inventory, but the original cited TSS files still require a sample
cross-check before confirmatory release.

## Controlled feasibility run

The reconstruction primitive was exercised locally with an 81 nt
transcription-oriented window, a 100 nt exclusion radius around all source TSSs,
one same-strand genomic control per eligible positive, and seed 20261021. The
GC analysis tested discrete tolerances corresponding to one, two, three, and
four GC nucleotides in an 81 nt window. One through three failed to supply a
control for every TSS in at least one organism; four nucleotides
($4/81=0.04938$) was the smallest common feasible tolerance and was frozen
without model training or outcome inspection.

| Candidate organism/source key | Source rows | Unique TSS groups | Eligible strict-DNA windows | Generated pairs | Mean sampling attempts |
| --- | ---: | ---: | ---: | ---: | ---: |
| BACILLUS | 1,064 | 1,064 | 1,064 | 1,064 | 25.41 |
| CJEJUNI_2 | 1,905 | 1,905 | 1,905 | 1,905 | 70.42 |
| CPNEUMONIAE | 530 | 530 | 529 | 529 | 127.45 |
| ECOLI | 278 | 248 | 248 | 248 | 5.78 |
| LINTERROGANS | 2,865 | 2,791 | 2,783 | 2,783 | 5.83 |
| RHODOBACTER_1 | 5,374 | 5,374 | 5,374 | 5,374 | 19.08 |

All six runs found the required number of controls under the frozen four-base
GC tolerance. Thirty repeated E. coli rows and 74 repeated Leptospira rows were
collapsed by biological TSS identity. One Chlamydophila TSS was outside the
complete-window bounds; seven Leptospira windows contained ambiguous DNA and
one was out of bounds. The generator uses a deterministic constant-memory
permutation of genomic start positions, excludes known-TSS regions and already
selected controls, rejects strict-DNA failures and exact or reverse-complement
identities, and records rejection counts per positive.

## Post-generation integrity correction

The first materialized candidate retained one pair per unique TSS, but exact
sequence auditing found strand-invariant positive duplicates: one pair in
BACILLUS, 23 in CJEJUNI_2, and 53 in RHODOBACTER_1. Because the version-1 build
manifests already existed, they were not overwritten. Version 2 removes the
entire positive--control pair for every repeated positive after the first in
source order. This preserves class balance and prevents an independently
sampled control from remaining after its positive is removed.

The version-2 candidate contains 11,826 pairs: 1,063 BACILLUS, 1,882
CJEJUNI_2, 529 CPNEUMONIAE, 248 ECOLI, 2,783 LINTERROGANS, and 5,321
RHODOBACTER_1. All positive and negative sequence identities are unique under
strand-invariant canonicalization; the classes have zero exact or
reverse-complement collisions, every sequence is strict 81 nt DNA, and every
pair respects the four-base GC limit. These results pass the exact-integrity
gate.

## Similarity-aware partitioning

The version-2 pairs were audited before partitioning at strand-invariant
Hamming-distance thresholds 1, 2, 4, and 8. BACILLUS, CPNEUMONIAE, ECOLI, and
LINTERROGANS had no pair-to-pair neighbors through distance 8. CJEJUNI_2 and
RHODOBACTER_1 each contained three distance-8 edges involving six pairs; every
edge joined sequences with the same label and every non-singleton component
contained two positive--control pairs.

The frozen split contract therefore treats each positive--control pair and each
connected similarity component at distance at most 8 as indivisible. A
deterministic component hash with seed 42 assigns approximately 80% of pairs to
training and 20% to testing. The resulting six splits contain 9,460 training
pairs (18,920 rows) and 2,366 test pairs (4,732 rows), with exact class balance
in every partition. An independent direct train--test audit found zero pair or
component overlap and zero forward/reverse-complement Hamming neighbors through
distance 8. A clean deterministic rebuild reproduced every partition file
byte-for-byte.

## Interpretation and remaining gates

The result supports technical feasibility for all six bacterial organisms.
It does not yet establish the final negative definition: the exclusion radius,
eligible genomic masks and primary-versus-CDS sensitivity design require final
release review. The eight
original GraphPro datasets remain excluded, and the 18-dataset confirmatory
scope is unchanged.

Before a bacterial candidate returns, the project must copy the authoritative
inputs into the non-versioned raw-data area with hashes and licensing metadata,
cross-check a sample of BED entries against the primary TSS sources, and pass
the distribution, cross-dataset dependency, and manual audit gates. Group-safe
splits and their exact/near-integrity audit are now complete. No model should be
trained on these candidates before the remaining release decision.
