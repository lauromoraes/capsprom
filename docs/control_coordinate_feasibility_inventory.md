# Negative-Control Coordinate and Assembly Feasibility Inventory

## Decision

The source-only inventory is complete for the 29 locally available dataset
identities, but it does not authorize control construction. Feasibility is
recorded per dataset because source families do not expose uniform metadata.
The machine-readable record is
`configs/control_coordinate_feasibility_inventory_v1.yaml`.

## Evidence classes

`verified_coordinates_and_assembly` is reserved for a hash-bound coordinate
source whose sequences have been recreated against the declared assembly.
Embedded FASTA coordinates, stable-looking accessions, publication-level
assembly tables, and sequence-only rows are weaker and remain separate states.
No model result was consulted to assign these states or the pilot shortlist.

## Findings by source

| Source | Dataset identities | Strongest available evidence | Decision for new genomic controls |
| --- | ---: | --- | --- |
| Bhandari | 3 | Every FASTA header contains a range, strand, and assembly token | Conditional on complete recreation and identity review |
| CDBProm | 11 | The paper reports assemblies, but local rows contain sequences only | Requires authoritative row ledger or unique sequence mapping |
| CNNProm | 7 | RegulonDB positions, gene names, or EPD-style identifiers depending on dataset | Resolve each dataset against a dated original resource |
| GraphPro reconstructed | 8 | Coordinate sources and assemblies are frozen; all eukaryotic sequences and bacterial candidates were recreated | Technically feasible, but release gates remain |

The Bhandari audit found 61,546/61,546 Human headers with `hg38` coordinates,
106,520/106,520 nominal Plant headers with `mm10` coordinates, and 6,125/6,125
Yeast headers with `sacCer3` coordinates. The `Plant_promoters.fa` name therefore
conflicts with its exclusively mouse-assembly metadata. This condition blocks
that identity; it is not silently renamed or interpreted as plant or mouse.

CDBProm's publication gives an assembly for every active organism, but the
downloaded positive files have no row identifiers, coordinates, or strands.
Assembly-level provenance alone cannot generate one matched control per local
positive. Unique mapping may establish a derived coordinate ledger, but
ambiguous mappings must be excluded and counted, and the result must use a new
dataset version.

CNNProm requires dataset-specific resolution. E. coli headers carry RegulonDB
identifiers, strand, and an integer position; Bacillus headers generally expose
gene names rather than coordinates; the non-TATA and Arabidopsis files use
EPD-style identifiers; and the Mouse TATA headers contain a literal `gt;`
prefix and mixed EPD/DBTSS provenance. None is promoted to a verified coordinate
until a dated database release, assembly, and convention reproduce the local
sequence.

## GraphPro manual-source status

Promotech's primary article independently confirms the expected assembly,
source TSS count, sequencing method, and source publication for five of the six
bacterial candidates. The Rhodobacter source is listed as an unpublished or
in-preparation source and has no PMID in that article. This establishes the
dataset-level lineage of the Promotech BED files, but not a row-level comparison
against each primary study. A stratified manual sample of the five published
sources remains required; Rhodobacter requires an accessible authoritative TSS
source or must remain excluded.

Human and Mouse have the strongest current coordinate evidence. Every released
sequence was recreated exactly from the November 2023 EPDnewNC coordinates and
the hg38/mm10 assemblies. This closes coordinate provenance, not dataset
eligibility: their GC-matched candidates still require the declared manual
source review, dependency decision, and eligibility approval.

A later public Rhodobacter resource was found under GEO accession GSE117537,
but its BED contains 4,045 TSSs, whereas the Promotech candidate contains 5,374.
The downloaded gzip has SHA-256
`7deb0d2f4e0d03897266d7d430fd0c5a8da298e08a63e294f446eb18797a14c5`.
Because the row counts and coordinate sets differ, this public collection is
recorded as a related resource rather than silently substituted for the
unidentified 5,374-row primary source.

## Pilot decision

No pilot is frozen. E. coli is shortlisted because it is the smallest bacterial
candidate with a publication-backed TSS lineage; Human and Mouse are shortlisted
because their coordinate recreation is complete. This shortlist uses
provenance and computational size only. Model outcomes are prohibited from the
final choice.

## Remaining actions

1. Compare a predeclared sample of Promotech bacterial BED rows with the five
   accessible primary TSS sources.
2. Locate an authoritative Rhodobacter coordinate source or retain its
   exclusion.
3. Resolve the Bhandari nominal-Plant identity conflict before using it.
4. Freeze dated upstream releases before resolving CNNProm identifiers.
5. Use assembly mapping for CDBProm only under a separately versioned mapping
   contract that reports ambiguous and missing matches.

The manual bacterial sample is frozen in
`configs/graphpro_primary_tss_sample_audit_v1.yaml`: ten rows per published
dataset are selected by SHA-256 rank, stratified by strand where possible, and
must match assembly, strand, and TSS exactly after a documented coordinate
conversion. The sample is selected before inspecting the primary tables.

The selection has now been materialized: 50 rows were chosen and the resulting
CSV hash is
`751a9a757f0b0080dc9aa3778c3c94c87d057e6b74a49cacfe5754265d8c78f9`.
This freezes sample membership but does not close the comparison gate.

Control generation, grouped splits, model training, and confirmatory use remain
disabled.
