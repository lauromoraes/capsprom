# Source Label Semantics Audit

## Purpose and decision

Exact deduplication cannot establish that a source label has the intended
biological meaning. This audit reviews the raw FASTA classes before admitting a
dataset to confirmatory promoter-versus-non-promoter experiments. The reviewed
scope retains the 11 CDBProm and 7 CNNProm datasets. All eight GraphPro datasets
are preserved for provenance but excluded from confirmatory inference until
their class construction can be independently verified.

## GraphPro findings

The GraphPro files were copied from the public repository identified by the
source README. The CapsProm builder maps files named `positive` and `negative`
literally; it does not infer labels from sequence content.

| Folder | Positive rows and strands | Negative rows and strands | Decision |
| --- | ---: | ---: | --- |
| Bamy | 928 `+` | 928 `-` | Exclude |
| Cje | 1,346 `+` | 1,346 `-` | Exclude |
| Cpne | 503 `+` | 431 `-` | Exclude |
| Ecol | 2,449 `+`, 70 `-` | 1,275 `+`, 2,599 `-` | Exclude |
| Lint | 2,847 `+` | 2,116 `-` | Exclude |
| Rcap | 3,607 `+` | 3,241 `-` | Exclude |

Table label: `tab:graphpro-source-label-semantics`.

For five bacterial folders, the supplied class is perfectly determined by the
strand symbol in the FASTA header. Strand is biologically meaningful metadata,
but it is not a promoter/non-promoter label. The available artifacts do not
demonstrate that these minus-strand records were independently selected as
non-promoters rather than promoter-associated records on the opposite strand.
Automatic relabeling is therefore prohibited.

The official GraphPro repository was inspected at commit
`f75c42bbe4c255dc0ad915ed58fe7161705f1a48`. Its preparation code assigns the
label from the `positive` or `negative` file name, and the repository provides
no upstream construction script or record-level provenance ledger. Therefore,
the public code reproduces the released mapping but does not independently
validate its biological semantics.

The GraphPro E. coli files contain 1,345 records with identical sequence,
complete header, accession, coordinate, and strand in both classes. Bilateral
collision filtering makes the resulting table internally consistent, but
cannot repair the uncertain meaning of the remaining source labels.

The Bacillus comparison supplies additional evidence. Of 928 GraphPro negative
81 bp records, 586 occur inside the 1,001 bp CDBProm positive regions and 535
start at offset 440. Offset 440 is exactly the canonical crop start for a
CDBProm TSS at position 500 (`500 - 60`). The resulting 535 windows receive
opposite labels across the sources. This relation exists in the raw inputs;
cropping only exposes it as exact identity.

## Organism mapping correction

The GraphPro folder `Cpne` was previously mapped by CapsProm to
`clostridium_phytofermentans`. Its raw headers instead identify accession
`NC_000922.1` and *Chlamydophila pneumoniae* CWL029. The builder now maps this
folder to `chlamydophila_pneumoniae`. Existing canonical-v3 artifacts and run
identities remain unchanged for provenance; the legacy GraphPro Cpne identity
is not eligible for new experiments.

## Confirmatory scope

The immutable decision is recorded in
`configs/dataset_eligibility_manifest_v1.yaml`. CDBProm is retained because its
publication documents curated promoter inputs and downstream negative-window
sampling. CNNProm is retained because its distributed documentation describes
the promoter resources and negative-set construction. GraphPro human and mouse
are also excluded because their negative-generation lineage has not yet been
independently verified; absence of the bacterial strand anomaly is not positive
evidence of valid negative labels.

All 2,339 records in each human class file and all 1,846 records in each mouse
class file use `FP` identifiers associated with EPD promoter records. This is
strong evidence that the directory name alone cannot establish a non-promoter
class. It does not, by itself, establish whether the upstream study transformed
or sampled those entries under an undocumented rule.

This produces 18 eligible datasets grouped into 14 dependency clusters in
`configs/dataset_dependency_manifest_v2.yaml`. Historical GraphPro results are
pipeline-development and provenance evidence, not confirmatory biological
evidence.

## Reinstatement rule

A GraphPro dataset may return only through a new versioned build after its
positive and negative construction is supported by source documentation or
independent genomic reconstruction, organism accessions are verified, and all
integrity audits are repeated. Neither agreement with another source nor model
performance is sufficient grounds for relabeling.

The reinstatement path is now defined in
`specs/graphpro_dataset_reconstruction.md` and
`configs/graphpro_reconstruction_v1.yaml`. Reconstructed datasets receive new
identities and may pass eligibility one organism at a time. The original eight
pairs remain unchanged and exploratory.
