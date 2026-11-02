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

### TSS classes of bacterial positives

dRNA-seq TSS maps classify each TSS by its position relative to annotated
genes: primary (P) and secondary (S) TSSs lie upstream of a gene on the same
strand; internal (I) TSSs lie inside a coding region on the same strand;
antisense (A) TSSs lie inside or near a gene on the opposite strand; orphan
(O) TSSs have no associated gene. One TSS can hold several classes. The class
set defines what "promoter" means for a dataset, so it is declared per
organism in the build config before any build or model result, and is never
tuned against model outcomes.

The Promotech BED files do not apply one class rule. The inventory
`scripts/inventory_graphpro_tss_classes.py` (log R-035, F-115 to F-117) joins
every BED row to its primary table:

| Organism | Promotech positives | Classes present |
| --- | --- | --- |
| *E. coli* pAA | all 248 TSSs of Dataset S1 | 51 gene-associated (P or S), 58 internal, 111 antisense, 47 orphan; 100 are antisense only |
| *C. jejuni* NCTC 11168 | all 1,905 TSSs of Table S4 | 675 P, 180 S, 653 I, 843 A, 17 O |
| *C. pneumoniae* | 530 primary TSSs; the 41 second TSSs are omitted | P only |
| *L. interrogans* | the 2,791 TSSs classed primary at 30 °C (F-118; not 37 °C) | all P; 905 also I at the other temperature |
| *B. amyloliquefaciens*, *R. capsulatus* | not inventoried | primary table not available |

Rules:

1. Positive classes are declared per organism. The conservative default is P
   plus S (gene-associated TSSs); any other set is a separate, versioned
   condition. A TSS is positive when its class set contains P or S, whatever
   other classes it also holds (log R-039). Positives are taken from the
   verified primary table, not limited to the Promotech BED rows. Declared
   sets:

   | Organism | Positive classes | Positives |
   | --- | --- | ---: |
   | *C. jejuni* | contains P or S | 855 |
   | *C. pneumoniae* | contains P or S (530 P plus the 41 S omitted by Promotech) | 571 |
   | *L. interrogans* | contains P or S at 30 °C (log R-042); exclusion uses both temperatures | 5,143 |
   | *B. amyloliquefaciens*, *R. capsulatus* | declared after their primary tables are verified | — |
   | *E. coli* pAA | excluded; no pAA identity is built (log R-040) | — |
2. Every positive keeps its full class set in the pair ledger, so results can
   be stratified by class.
3. The control exclusion set is the complete primary TSS table of the source,
   all classes, both strands, not only the selected positives
   (see Negative-set reconstruction).

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
  inventory, on either strand. The source inventory is the complete primary
  TSS table (all classes), never only the selected positives;
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

Each candidate is checked against all of these conditions before it is
accepted. A candidate that fails any of them is discarded and the next
candidate of the deterministic permutation is drawn, until a valid control is
found or the attempt ceiling is reached; the rejection reasons are counted per
positive. After selection, every accepted control is verified again,
independently, against the complete exclusion set, and the build fails if any
control is inside a TSS margin (`reconstruct_genomic_controls`,
`find_control_exclusion_violations`). The builder requires the exclusion set
explicitly and refuses one that omits a positive.

The exclusion radius depends on the domain window of
`specs/sequence_window_policy.md`. The exclusion is symmetric and applies to
both strands, so a radius `r` keeps a control clear of the interval
`[TSS - r, TSS + r]` of every known TSS. To prevent a control from sharing bases
with the promoter window of any known TSS, whichever strand that TSS is on,
`r` must be at least the upstream length `U` of the domain window. A margin
`m` is added on top of `U` for TSS mapping imprecision and nearby alternative
TSSs. The eukaryotic margin is wider because broad eukaryotic promoters spread
initiation over tens of nucleotides around the annotated representative TSS:

| Domain | Window | `U` | Margin `m` | Radius `r = U + m` |
| --- | --- | ---: | ---: | ---: |
| Prokaryota | -60..+20, 81 nt | 60 | 40 | 100 |
| Eukaryota | -200..+50, 251 nt | 200 | 50 | 250 |

The prokaryotic radius is unchanged, so the existing bacterial contracts
already satisfy the rule. The 100-nt margin of the 81-nt Human/Mouse
contracts, through `configs/graphpro_epd_gc_matched_reconstruction_v5.yaml`,
was adequate for that window. Those contracts remain valid provenance, but no
251-nt eukaryotic build may use them. A 251-nt Human/Mouse successor uses
`r = 250` (log R-036).

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
