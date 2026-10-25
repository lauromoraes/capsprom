# Negative-Control Experimental Protocol

## Purpose and status

This specification defines negative construction as an explicit experimental
factor in CapsProm. It does not replace the active confirmatory source-negative
protocol and does not authorize dataset generation, splitting, training, or
test access. The machine-readable design is
`configs/negative_control_evaluation_v1.yaml`.

The central hypothesis is that a model whose decisions remain stable across
defensible negative definitions is more likely to learn promoter-associated
sequence structure than a model that succeeds only against one source-specific
background. A higher MCC under an easier negative condition is not evidence of
better genomic promoter detection.

## Locked negative conditions

### Source-native (`native`)

The negative records distributed or independently documented by the source
study are retained under their corrected, leakage-controlled identity. This is
the primary condition for reproducing eligible CDBProm and CNNProm studies.
Source-native labels are never pooled with reconstructed controls under the
original dataset identity.

### GC-matched genomic (`genomic_gc_matched`)

One genomic control is constructed for each independently verified promoter
TSS from the same assembly. The control has the same window length and declared
strand policy, lies outside the frozen margin around known TSSs, does not
overlap another selected control, contains strict DNA, is not identical to a
positive or another control in either orientation, and satisfies a predeclared
GC-count caliper. The promoter-control pair is indivisible during filtering and
partitioning. Random genomic controls retain positive-unlabeled uncertainty:
absence from the TSS inventory does not prove biological inactivity.

### Synthetic shuffle (`synthetic_shuffle`)

A deterministic shuffle preserves the explicitly declared composition level
(mononucleotide or dinucleotide) while perturbing sequence order. It is a
development or mechanistic control, not a genomic non-promoter. Every promoter
and all shuffles derived from it form one partition group. The existing
Bhandari Human condition remains a mononucleotide-shuffle development task;
changing to dinucleotide shuffling requires a new dataset identity.

### CDS-derived (`cds_derived`)

Controls are sampled from independently annotated coding sequence under a
versioned organism, assembly, strand, frame, overlap, length, and GC policy.
This is a separate sensitivity condition because it asks the model to
distinguish promoters from coding background and can introduce codon,
periodicity, and composition shortcuts. CDS controls are never treated as
interchangeable with general genomic controls.

### Multi-negative training (`multi_negative`)

Multi-negative training is an ablation of training exposure, not a fifth claim
about biological ground truth. A positive is represented once logically and is
linked to every associated negative family. Training batches allocate 50% of
their weight to positives and divide the remaining 50% equally across available
negative families unless a successor contract states otherwise. Repeating the
same positive once per negative family is forbidden because it would silently
increase its weight. Validation and test metrics remain separate by negative
panel.

## Eligibility before construction

A dataset may enter a genomic or CDS condition only when all required source
facts are independently available: organism and strain, exact assembly,
contig, zero-based TSS, strand, coordinate convention, source citation, and
source-file hash. Sequence-to-genome mapping is acceptable only when the
assembly is known and the declared rule yields a unique defensible locus;
ambiguous mappings are excluded and counted rather than resolved using model
performance.

The feasibility inventory is performed without training models:

| Source family | Native | Genomic GC-matched | Shuffle | CDS | Current decision |
| --- | --- | --- | --- | --- | --- |
| CDBProm | primary for eligible datasets | feasibility audit required per organism | optional mechanistic sensitivity | optional sensitivity | wait for independent coordinate and assembly verification |
| CNNProm | primary for eligible datasets | feasibility audit required per dataset | optional mechanistic sensitivity | optional sensitivity | wait for independent coordinate and assembly verification |
| Bhandari | unavailable in downloaded promoter-only source | conditional on unique coordinate and assembly resolution | current Human development control | conditional on provenance | perform coordinate-resolution feasibility only |
| GraphPro reconstructed | released labels remain exploratory | implemented primary reconstructed condition | optional sensitivity | planned sensitivity | finish organism-level eligibility before any new condition |

The first implementation pilot must be one small dataset selected by provenance
completeness and computational feasibility before any model outcome is
available. The pilot dataset and parameters are frozen in a successor contract.

## Grouping and leakage prevention

Every record linked by the same TSS, promoter sequence, source experiment,
sampled control pair, shuffle parent, or near-sequence component belongs to one
global group. Group identities are shared across negative conditions. Thus a
promoter or derivative cannot be in training under one condition and test under
another. Exact and reverse-complement dependencies across all active sources
are incorporated into the dependency manifest before partitioning.

All feature fitting, control-policy selection, GC caliper selection, mixture
weighting, threshold selection, and hyperparameter selection use training data
only. No held-out outcome may determine which negative condition is retained.

## Evaluation matrix

The initial sensitivity design compares three training conditions where the
required data exist:

1. `train_native`;
2. `train_genomic_gc_matched`; and
3. `train_multi_negative_native_plus_genomic`.

Each locked model is evaluated independently on `test_native` and
`test_genomic_gc_matched`. Shuffle and CDS panels are separately labeled
sensitivity analyses. When a genome-scale scan with independently annotated
regions is available, false positives per scanned megabase and promoter-level
recall are reported as an additional external-behaviour panel.

MCC is reported per panel and is never computed after concatenating different
negative families. Secondary effectiveness, calibration, efficiency, and
explainability outcomes follow the active evaluation protocol. The same folds,
seeds, architecture, representation, training budget, and selection rule are
used across training conditions whenever scientifically compatible.

Within one fixed test panel, model comparisons use identical records and the
active paired prediction-level bootstrap. Comparisons across negative panels do
not claim record-level pairing merely because they share positives. Policy
effects are summarized within dataset and seed, then aggregated by audited
dependency cluster. Model-by-negative-policy interactions are exploratory in
version 1; confirmatory interaction inference requires a successor statistical
contract with enough independent clusters.

## Required artifacts

Each derived condition records source and assembly hashes, coordinate and
exclusion ledgers, parent-positive and control-family identifiers, sequence and
reverse-complement identities, GC and positional distributions, exact and near
dependencies, group-safe split manifests, configuration hashes, and MLflow run
identifiers. Multi-negative runs additionally persist per-family sampling
counts and effective loss weights.

## Execution gates

The version-1 protocol is design-only. Execution requires, in order:

1. complete the current GraphPro Human/Mouse manual source audit;
2. validate paired-seed and dependency-cluster aggregation with fixtures;
3. create a source-only coordinate and assembly feasibility inventory;
4. select and freeze one pilot without model outcomes;
5. implement fixture-tested construction and global grouping;
6. audit distributions and dependencies; and
7. approve a new eligibility manifest before any real training.

## Primary methodological references

- González et al., "Negative dataset selection impacts machine learning-based
  predictors for multiple bacterial species promoters," *Bioinformatics*,
  2025: <https://doi.org/10.1093/bioinformatics/btaf135>.
- Kr\u00fctzfeldt et al., "The impact of different negative training data on
  regulatory sequence predictions," *PLOS ONE*, 2020:
  <https://doi.org/10.1371/journal.pone.0237412>.
- Cassiano and Silva-Rocha, "Benchmarking bacterial promoter prediction tools:
  potentialities and limitations," *mSystems*, 2020:
  <https://doi.org/10.1128/mSystems.00439-20>.
