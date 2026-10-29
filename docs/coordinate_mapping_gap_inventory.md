# Coordinate Mapping: Existing Support, Gaps, and Integration Plan

Companion to `specs/reference_coordinate_mapping_protocol.md`. This is a
planning record, made from the canonical tables of `source_canonicalization_v1`
and the existing provenance records. No mapping was run to produce it.

Header observations come from the first record of each class in each canonical
table (`original_header`). They describe what the headers contain, not whether
the coordinates are correct.

## Existing support to reuse

| Need | Existing component | Reuse |
| --- | --- | --- |
| Stable record identity | canonical `record_id`, `sequence_sha1` | primary key of every mapping row |
| Reference acquisition with digests and resumption | `capsprom.data.acquisition`, `scripts/acquire_sources.py --config` | new config for genomes and annotations; `v1` untouched |
| Atomic state | `capsprom.state.write_json_atomic` | `mapping_manifest.json` |
| Random access to UCSC 2bit genomes | `capsprom.data.twobit.TwoBitGenome.fetch(..., reverse_complement=)` | B1 extraction for hg38, mm10, sacCer3 |
| EPD BED parsing and TSS position | `capsprom.data.epd_resolution` (`load_epd_bed`, `epd_tss_zero_based`, `oriented_interval`) | `epd_bed_tss` rule; FP identifier resolution |
| Primary TSS table readers | `capsprom.data.primary_tss_audit` | TSS source evidence for Promotech bacteria |
| TSS window extraction, reverse complement | `capsprom.data.graphpro_reconstruction` | shared helpers; move to a common module only when a third caller needs them |
| Provenance records | `docs/provenance/` log, findings, lineage; `manifests/provenance/` | Stage A evidence and promotions |
| Prior evidence | feasibility inventory (`configs/control_coordinate_feasibility_inventory_v1.yaml`), log R-011, GraphPro EPD recreation | validation criterion 7 |

**Missing:** a reference registry; a FASTA (non-2bit) random-access reader for
NCBI genomes; a complete both-strand exact matcher (R-011 used scratch scripts
outside the repository); an aligner. Neither Bowtie 2 nor any other aligner is
installed in the project environment. Biopython is available.

## Gaps by dataset

Evidence levels follow the protocol: **D** declared, **I** inferred, **V**
verified, **C** conflicting, **U** unknown.

| Collections | Records with coordinates? | Reference status | Gaps and risks | Initial method |
| --- | --- | --- | --- | --- |
| `bhandari-human`, `bhandari-yeast` | Yes: `range=chrN:a-b strand=±`, `up_700`, `3'pad=300` | Assembly D (`hg38`, `sacCer3`), genomes acquired (2bit). RefSeq track D; snapshot date U | Convention V for the pilot (F-041); TSS at index 700 V for 58,816 Human and all Yeast records (F-047, F-055); U for 2,715 Human (F-056). Table Browser identifiers are not releases. 43% within-class duplicates (F-014) | Full B1; source release identified as NCBI AR 109 (F-053, F-054) |
| `bhandari-nominal-plant` | Yes, `mm10` headers | Organism **C**: paper says *A. thaliana* `araTha1`, headers say `mm10` (F-016) | F-017 (mouse set) is a hypothesis. B1 on `mm10` can verify the location only. The identity stays blocked | B1 on `mm10`; record conflict |
| `bhandari-human-random-genomic` | No positions observed (first header `chrM MT`) | Assembly I (`hg38`) | Construction rule and seed U; not a promoter source | B2 on `hg38` after a sample check of headers |
| `cdbprom-*` (11) | No headers at all | Accessions D in the paper. R-011 replaced two assemblies that did not contain the released sequences (now Nostoc PCC 7120 `GCF_000009705.1` and SL1344 `GCF_000210855.2`); the feasibility config still lists three accessions R-011 marks as wrong (CP034058.1, CP133487.1, AL939104.1) | Genomes only in `data/raw/references/` (F-027); TSS offset in the 1,001 nt U (F-018); negatives 100 nt from +1..+500 downstream, pairing and seed U | Acquire genomes; B2 (formalizes R-011) |
| `cnnprom-ecoli-sigma70` | Positives: RegulonDB `ECK12…`, strand, integer position. Negatives: integer only | Genome D (`NC_000913`), version U. RegulonDB 9.0 D; release file not acquired | Position semantics (TSS? 0/1-based?) I; negative integer meaning U | Acquire dated RegulonDB; B1 pilot, B2 fallback |
| `cnnprom-bacillus-subtilis` | Positives: gene name only. Negatives: integer | Genome D (`NC_000964`), version U; DBTBS D | Released counts are half of the paper's | B2 on `NC_000964.3` |
| `cnnprom-human-non-tata`, `-mouse-non-tata`, `-mouse-tata`, `-arabidopsis-*` | EPD `FP` identifiers; window -200..+50 D | EPDnew D, release U; human 006 and mouse 003 BEDs acquired; *Arabidopsis* EPDnew and genome not acquired | Release choice must be justified by recreation, not assumed. Mouse TATA headers have a `gt;` prefix. Negatives: GenBank entry descriptions, no coordinates | Resolve FP against candidate dated releases; B1. Negatives B2 per assembly |
| `cnnprom-mouse-tata-dbtss` | Yes: DBTSS row with `chr11` and positions | DBTSS D; assembly U (mouse build not stated) | Column semantics U | Identify DBTSS release, then B1 pilot |
| `graphpro-{bamy,cje,cpne,ecol,lint,rcap}` | Yes: accession, position, `(±)`; negatives in `acc:cA-B` form | Accessions D in headers; contig identity issues already found (ECOLI pAA, `Cpne`) | Labels exploratory (strand confound); conventions I | B1 pilot per convention; existing reconstruction contract governs reuse |
| `graphpro-human`, `graphpro-mouse` | EPD `FP` identifiers | **V**: all sequences recreated from EPDnew NC (Nov 2023) on hg38/mm10 | Import the existing evidence; do not recompute without need | Import as B1 results |
| `ipro-mp-*` (23) | No: `<species>--<n>` index only | Accessions D (paper Table 3); genomes not acquired; PPD version U | CD-HIT 0.8 and sampling seed not released; negatives CDS/convergent with no coordinates | Acquire genomes; B2 |
| `epd-128` | `EP` identifiers, window -499..+100 (600 nt) | Release 128 D; multi-organism; coordinate file for release 128 not acquired | Each entry needs organism and assembly resolution | Acquire EPD release-128 coordinate view; B1 |
| `bdgp-drosophila-1941`, `-1998`, `bdgp-human` | Clone/gene or old EPD identifiers; CDS/intron negatives with GenBank names or `DUMMY` | Assembly U (BDGP release not stated); publication not confirmed | Weakest lineage; old EPD identifiers may be retired | Defer; B2 on a declared assembly only after Stage A finds one |
| `promotech-*` (6) | Yes: `acc:a-b(±)`, 40 nt | Promotech BED acquired; ECOLI contig **C** (`NC_000913.3` declared, pAA `NC_018666.1` verified) | Rhodobacter primary source U; one 1-nt record (F-019) | B1 pilot; reuse the GraphPro primary-TSS audit |

## Prioritized implementation sequence

Each step is a separate, reviewable change. It ends with `make check` and a
research-log entry. Large runs start only after the preceding step is accepted.

1. **Reference registry, documentation only.** Write `reference_registry`
   entries for all 64 collections from the table above and
   `docs/dataset_reconstruction_sources.md`, with evidence levels. Record the
   three stale CDBProm accessions as `conflicting` and correct them in a new
   feasibility config version, not by editing v1. Check the publication's own
   accession list, which R-011 left unchecked. Exit: every collection has assembly and organism entries, even
   if `unknown`.
2. **Reference acquisition config.** `configs/reference_acquisition_v1.yaml`
   for NCBI assemblies (CDBProm 11 with the R-011 replacements, iPro-MP 23,
   CNNProm bacteria, GraphPro and Promotech bacteria, pAA), assembly reports,
   and the dated annotation releases needed by B1. Run with the existing
   acquisition code. Exit: all files hash-verified; R-011 FASTA hashes
   reproduced.
3. **Core library with fixtures.** Coordinate model, the named conversion
   rules, a FASTA random-access reader, the B1 verifier, and the exact matcher.
   Criteria 4 and 5 are tested on synthetic data. No real run yet.
4. **Persistence and resumption.** Record and locus writers, shard manifest,
   cache, and `runs[]`. Criterion 6 (determinism and resume equivalence) is
   tested with a forced interruption.
5. **B1 pilots, then B1.** The convention pilots (Bhandari, Promotech, GraphPro
   bacterial, CNNProm E. coli). Full B1 only for conventions whose pilot passes.
   Import the GraphPro Human/Mouse recreation. Exit: criteria 3 and 7 (EPD).
6. **B2 on bacterial genomes.** CDBProm, then iPro-MP and CNNProm Bacillus.
   Small genomes, so this runs locally and detached. Exit: R-011 counts
   reproduced (criterion 7).
7. **Identifier resolution.** EPD/EPDnew (CNNProm eukaryotes, EPD 128),
   RegulonDB, DBTSS, against dated releases acquired in step 2.
8. **B3 alignment fallback.** Only for records left `unmapped` or
   `inconsistent`. Requires a locked Bowtie 2 environment and cached indexes;
   mammalian indexes are built on a remote host, asynchronously.
9. **Audit and release.** Stratified manual sample (criterion 8), findings for
   every evidence change, committed summaries, and a lineage note. After this,
   dataset builds may reference the mapping version.

BDGP stays deferred until Stage A identifies a declared assembly.

## Open questions to resolve with evidence, not assumption

- Which EPDnew release reproduces the CNNProm `FP` windows (unknown; test
  candidate releases by recreation).
- Whether the CNNProm E. coli integer is a TSS position, and in which
  convention.
- Whether CDBProm negatives are ordered pairs of their positives (hypothesis
  only; file order is not evidence).
- The *A. thaliana* source of the Bhandari publication (no matching file was
  released).
