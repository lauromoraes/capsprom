# CDS-Derived Negative-Control Protocol

## Status and scope

Design (2026-11-02, log R-038). Machine-readable contract:
`configs/cds_negative_control_v1.yaml`. This protocol specifies the
`cds_derived` condition of `specs/negative_control_protocol.md`. It authorizes
no reference acquisition, control generation, split, training, or test access;
every execution gate in the contract is false.

The condition is a coding-background sensitivity panel. It asks whether a model
separates promoters from coding sequence, not from the genome at large. It is
never pooled with the genomic GC-matched condition, never reported as one MCC
with another panel, and never used for model, feature, epoch, or threshold
selection.

## Scope

Version 1 covers prokaryotic reconstructed datasets only: GraphPro Cje, Cpne,
and Lint, and Bacillus and Rhodobacter once their source gates pass. Each
dataset receives its own identity `<collection_id>.recon-cds-v1`. Eukaryotic
datasets are excluded: coding exons are short and a 251 nt window
(`specs/sequence_window_policy.md`) frequently crosses exon-intron boundaries.

## Annotation source

CDS features come from the RefSeq GFF of the exact assembly accession and
version that carries the positive TSS coordinates. The GFF release date and
SHA-256 are recorded. A feature is eligible only when all of the following
hold:

- feature type `CDS`, without a `pseudo` attribute;
- length at least 201 nt (60 + 81 + 60, see below);
- exact boundaries: no partial or fuzzy start or end;
- a single contiguous segment: no join, splice, ribosomal slippage, frameshift,
  or translation exception.

## Window construction

For each positive, one control is drawn from an eligible CDS on the same
replicon (chromosome or plasmid) as the positive.

- **Length and strand.** 81 nt, extracted on the sense strand of the CDS and
  oriented 5' to 3' in the direction of translation.
- **Frame.** Frames 0, 1, and 2 are assigned deterministically in a repeating
  0, 1, 2 cycle over positives in stable source order, before position
  sampling. Frame `f` means the window starts at codon position `f` relative to
  the annotated start codon. The frame of every control is recorded.
- **Position.** The whole window lies inside the CDS, at least 60 nt after the
  first base of the start codon and at least 60 nt before the last base of the
  stop codon. The margins guard against misannotated start codons and against
  downstream-gene promoters at the end of upstream operon genes.

## Exclusions

A candidate is rejected when it:

- lies within 100 nt of any known TSS on either strand (the prokaryotic radius
  `r = U + m = 60 + 40` of log R-036). The exclusion set is the complete
  primary TSS table of the source, all classes, not only the selected
  positives (`specs/graphpro_dataset_reconstruction.md`, log R-035). Internal
  and antisense TSSs therefore exclude their surroundings inside CDSs;
- overlaps any other annotated CDS or RNA feature on either strand;
- overlaps another selected control of the same dataset in any condition;
- contains non-ACGT bases;
- equals any positive or any selected control, forward or reverse complement;
- differs from its paired positive by more than four G/C bases.

## Sampling

The sampling seed is predeclared and distinct from the genomic-condition seeds.
Up to 100,000 random candidate positions are probed per positive. After random
exhaustion, a deterministic exhaustive scan of the eligible positions on the
replicon selects one window by reservoir sampling, under the same frame and
exclusion rules. Random-probe and exhaustive-scan counters are recorded
separately.

## Failures

A positive with no viable CDS control loses its pair in the CDS panel only. It
remains in the genomic GC-matched panel. Each failure is recorded with the
positive identifier, its GC count, and the counters. Version 1 publishes the
dataset with these exclusions; relaxing the GC caliper requires a successor
contract.

## Grouping and split

The CDS panel reuses the positives and groups of the genomic GC-matched
successor build of the same dataset, under its declared positive TSS classes
(default P plus S, log R-035). The reconstructed-v2 bacterial candidates are
not a valid basis: their *L. interrogans* controls violate the complete-table
exclusion and their split predates homology grouping v1. A positive in the test partition stays in the
test partition. Each CDS control inherits the group of its positive and then
enters homology grouping v1 (`specs/homology_grouping_protocol.md`), including
genomic-overlap edges. If grouping links a CDS control to a record in another
partition, the pair is excluded from the CDS panel and recorded; the genomic
split is not changed.

## Statistics

Inference is within the CDS panel, with the paired bootstrap of
`specs/statistical_evaluation_protocol.md` on shared test indices.

When the CDS and genomic panels of a dataset contain different positive sets,
every cross-panel comparison is restricted to the intersection of their test
positives and the pairs built on them. The intersection identifiers are fixed
from the build ledgers before any model is evaluated on either panel. Union or
unrestricted cross-panel comparisons are not reported. Within-panel results use
the full panel.

## Required diagnostics

Descriptive only; none alters the construction:

- three-nucleotide periodicity spectrum per class;
- realized frame proportions;
- GC distribution per class with the aggregate positive-minus-control gap;
- distance from each control to the nearest TSS and to the nearest CDS
  boundary;
- failure count and the GC of failed positives.
