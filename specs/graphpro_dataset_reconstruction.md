# GraphPro Dataset Reconstruction Contract

## Decision

The eight released GraphPro class pairs are preserved unchanged for reproduction
and exploratory investigation. They are not repaired by swapping, deleting, or
inferring labels from strand, sequence content, another dataset, or model
predictions. Any dataset admitted again to confirmatory evaluation is a new
derived resource named `graphpro-reconstructed-v1` and has its own hashes,
filtering ledger, dependency identity, and experimental configuration.

This distinction is necessary because the official GraphPro repository contains
the released `positive` and `negative` files and code that maps the directory
names directly to labels, but no construction script or provenance ledger that
independently establishes the biological meaning of those classes.

## Evidence to preserve

The source audit must record the official repository URL and commit, every raw
file hash, record counts, identifier/accession fields, header labels, strand
counts, exact duplicates, and exact cross-class collisions. The current audit
finds:

- perfect released-class/strand association in Bamy, Cje, Cpne, Lint, and Rcap;
- 1,345 identical full records in both E. coli class files;
- EPD-style `FP` promoter identifiers in every one of the 2,339 human records
  in each released class and every one of the 1,846 mouse records in each class;
- one human sequence shared across the released classes, although its complete
  records differ; and
- no source construction program in official GraphPro commit
  `f75c42bbe4c255dc0ad915ed58fe7161705f1a48`.

These observations diagnose uncertainty in source-label semantics; they do not
prove which individual records were annotated incorrectly.

## Positive-set reconstruction

### Bacterial datasets

Positive examples must be recreated from independently documented,
experimentally mapped TSS coordinates and the exact reference assembly. The
Promotech data and its cited primary TSS maps are the first candidate sources
because its organism/accession inventory overlaps the released GraphPro
bacterial inventory. A released GraphPro row may corroborate a recreated
window but cannot be its only source of truth.

Every positive must retain: organism and strain, assembly accession and version,
contig, zero-based TSS, strand, original coordinate convention, primary-source
identifier, source citation, source-file hash, and the final oriented window.
The window follows `specs/sequence_window_policy.md`: 60 nt upstream, the TSS
base, and 20 nt downstream for bacteria, and 200 nt upstream, the TSS base, and
50 nt downstream for the eukaryotic (Human, Mouse) reconstructions, oriented
5-prime to 3-prime relative to transcription.

The source contig is part of the biological identity and must be verified
against the primary table before extracting any window. In particular, the
Promotech file named `ECOLI.bed` reproduces all 278 ordered rows of
Supplementary Dataset S1 from PMID 27748404, which describes the 74,217-bp pAA
plasmid of *E. coli* O104:H4. Although that BED declares chromosome accession
`NC_000913.3`, all 278 published 51-nt source windows match plasmid
`NC_018666.1`. Consequently, the nominal MG1655 reconstruction is invalid and
cannot be repaired by renaming its already extracted sequences. A successor
must extract new windows from `NC_018666.1` under a new pAA-specific dataset
identity and repeat every downstream audit and split.

### Human and mouse datasets

The `FP` identifiers must first be resolved against a dated Eukaryotic Promoter
Database release and its declared genome assembly. EPD is a promoter/TSS
resource, so records from the released GraphPro `negative` file are not accepted
as non-promoters solely because of their directory. After identifier and
coordinate verification, the union may contribute positive candidates; exact
duplicates and multiple records derived from the same TSS remain one biological
group. Unresolved identifiers are excluded and counted.

## Negative-set reconstruction

The primary negative condition is one deterministic genomic control per
positive, sampled from the same assembly and matched to window length, strand
distribution, and GC content. A candidate must:

- lie outside the frozen exclusion radius around every known TSS in the source
  inventory;
- not overlap another selected control;
- contain strict DNA only;
- not equal a positive or another negative in either orientation; and
- satisfy the configured absolute GC-distance tolerance.

A control whose exact strand-invariant identity is labeled positive in an
independently versioned active dataset is unsuitable for the reconstructed
negative condition and may be excluded under a predeclared, hash-bound rule.
This exclusion applies to the control only: it neither proves that the external
label is biologically correct nor authorizes relabeling either source. The
external dataset identity, label, orientation, input hashes, and excluded
control identifier must be retained in the filtering ledger.

The exact exclusion radius, GC tolerance, sampling seed, attempt ceiling, and
eligible genomic masks are frozen before model evaluation. Random genomic
controls can still contain undiscovered promoters; this is reported as
positive-unlabeled uncertainty, not hidden by the pipeline.

A separately versioned CDS-derived negative condition is planned as a
predeclared sensitivity analysis. It must not be pooled with the primary
condition because negative selection changes the prediction task and may create
composition shortcuts. Synthetic random sequences may be explored but are not
treated as genomic non-promoters.

## Split and leakage policy

All windows linked to one TSS, source experiment, or sampled positive-control
pair are an indivisible group. Source-level and exact/near-sequence dependencies
are resolved before train/test partitioning. Selection folds use training data
only. The held-out test partition cannot influence exclusion radii, GC
tolerance, source filtering, representation, architecture, epoch choice, or
threshold choice.

## Eligibility gates

A reconstructed organism is admitted only after all of the following pass:

1. assembly and organism identity verification;
2. independent positive-label provenance and coordinate recreation;
3. deterministic negative generation with a complete candidate/rejection
   ledger;
4. exact collision, within-class duplicate, reverse-complement duplicate,
   train/test overlap, and near-duplicate audits;
5. class, GC, positional, strand, and source-distribution reports;
6. immutable input/output hashes and group-safe split manifest;
7. fixture validation and an independent manual sample audit; and
8. a new eligibility and dependency manifest approved before any confirmatory
   model run.

Reinstatement is per organism. Failure or unresolved provenance in one organism
does not force acceptance or rejection of the other seven.

## Primary references

- GraphPro paper: <https://doi.org/10.1016/j.compbiomed.2024.108974>
- Official GraphPro repository: <https://github.com/liuliwei1980/GraphPro>
- Eukaryotic Promoter Database archive: <https://www.expasy.org/archives/epd>
- Promotech paper and TSS-source inventory:
  <https://doi.org/10.1186/s13059-021-02514-9>
- Promotech repository: <https://github.com/BioinformaticsLabAtMUN/Promotech>
- Study of negative-set sensitivity in multi-species promoter prediction:
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC11993300/>
