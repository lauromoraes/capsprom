# GraphPro EPD GC-Matched Reconstruction

## Objective

This stage creates the primary Human and Mouse candidate condition from the
union of source EPD identifiers rather than reusing the historical GraphPro
downstream class. It generates one genomic control per verified TSS under the
versioned contracts ending in
`configs/graphpro_epd_gc_matched_reconstruction_v5.yaml`. No predictive result
is used to define or relax the control policy.

## Meaning of pairing

Pairing is a construction and grouping relationship, not a claim that the two
sequences are biologically homologous. Each `pair_id` links one promoter window
to one independently sampled control that has the same assembly, chromosome,
strand, length, and GC count within two bases. The pair is an indivisible unit in later
filtering and partitioning: if either sequence is invalidated, both are removed,
and both must remain in the same fold. This preserves class balance and prevents
the positive from being evaluated against a control chosen in another fold.

## Frozen generation policy

Promoters are strand-oriented 81-nt windows spanning 60 nt upstream, the TSS
base, and 20 nt downstream. Candidate controls are sampled deterministically
from the same chromosome and oriented on the same strand. A candidate is
rejected if it lies within the 100-nt expanded margin of a coding or non-coding
EPD TSS, overlaps a previously selected control, contains ambiguous DNA, shares
an exact strand-invariant identity with any target positive, selected control,
or active external positive, or differs from its paired promoter by more than
two GC bases. The fixed seed is 20261022 and the random-probe ceiling is 100,000
candidates per TSS. A preregistered feasibility attempt at exact equality
exhausted that ceiling for Human promoter `LIFR-AS1_1`; no partial dataset was
published. The one-base tolerance was the first discrete relaxation and was
chosen without model outcomes.

The separate version-2 feasibility run showed that this relaxation is still
insufficient: Mouse promoter `0610009L18Rik_1` exhausted the same 100,000
candidate ceiling. Version 2 also published no partial dataset. Version 3 tested
the next discrete tolerance of two GC bases in 81 nt while preserving both
failure logs and all other sampling parameters, but the random probe again
failed for the same Mouse promoter. Its window contains 75 G/C bases (92.59%),
showing that uniform probing was the limiting factor rather than proving that a
matched genomic window did not exist.

Version 4 added a bounded-memory exhaustive chromosome scan only after random
exhaustion, retaining the two-base caliper and every exclusion. Eligible
fallback windows are selected by deterministic reservoir sampling. Version 5
corrects the separation between the random-probe counter and the
exhaustive-window counter; this metadata correction does not change sequence
selection. The version-5 candidate contains 2,332 balanced Human pairs and
2,571 balanced Mouse pairs after bilateral removal of seven and five duplicate
positive pairs, respectively. Two Mouse promoters required exhaustive fallback:
`0610009L18Rik_1` (75/81 G/C, matched to 74/81) and `Gm15327_1` (76/81,
matched exactly). No Human promoter required fallback.

The two-base pair constraint strongly controls but does not mathematically make
the aggregate GC-count distributions identical. It also does not guarantee
equivalence in dinucleotide composition, positional nucleotide frequencies,
chromatin context, gene proximity, or unobserved promoter status. Those remain
separate distribution and positive-unlabeled uncertainty checks.

## Execution and gates

The large UCSC hg38/mm10 assemblies are hash-verified on the bounded
`bioserver04` campaign workspace. Outputs are staged and published atomically;
FASTAs, the pair ledger, rejection counters, configuration hash, source hashes,
and sampling statistics are retained. Reconstruction does not authorize split
generation, model training, or confirmatory use. Those gates require a clean
dependency audit, distribution report, near-duplicate grouping, deterministic
fold construction, and manual source sample review.

The version-5 descriptive audit reduced the mean positive-minus-negative GC
fraction from approximately 0.11 in the historical condition to 0.00289 for
Human and 0.00405 for Mouse. Two-sided Mann--Whitney and Kolmogorov--Smirnov
tests did not identify an aggregate GC-distribution difference after Holm
correction. This is evidence that the intended univariate shortcut was reduced,
not proof of distributional or biological equivalence. Exact dependency checks
found only same-label positive overlap: 14 Human identities with CNNProm Human
non-TATA, 18 Mouse identities with CNNProm Mouse non-TATA, two with CNNProm
Mouse TATA, and one shared Human--Mouse positive. These dependencies must be
grouped or separated by the future evaluation design; no opposite-label overlap
was observed.

A clean version-5 rebuild reproduced the complete output tree and execution log
byte-for-byte. The build-summary SHA-256 is
`518b526b2e8144a0e3bbb982340a2301531ad8e92c130aeb5368368848e9288e`.

The strand-invariant Hamming audit at distance eight grouped 53 of 2,332 Human
pairs and 49 of 2,571 Mouse pairs with at least one neighbor. The largest
component contains six pairs in each organism. Human has three cross-label
neighbor edges at distance eight, one already present at distance four; Mouse
has none. These are near similarities rather than exact label collisions. Any
future partition must assign each complete pair component to a single fold and
then independently verify the absence of train--test neighbors.
