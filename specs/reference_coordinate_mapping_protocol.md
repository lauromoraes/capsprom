# Reference Identification and Coordinate Mapping Protocol

## Status and scope

Design-only. This protocol defines how CapsProm identifies the references of
every canonical collection and locates its sequences, promoters and
non-promoters alike, on a reference genome. It authorizes no large-scale
mapping, no dataset reconstruction, and no change to the acquired or canonical
data. Execution follows the integration order in
`docs/coordinate_mapping_gap_inventory.md`.

It extends, and must not contradict:

- `specs/source_acquisition_protocol.md` (acquisition and canonical tables);
- `specs/data_provenance_policy.md` (records, evidence classes, logging);
- `specs/graphpro_dataset_reconstruction.md` and
  `specs/negative_control_protocol.md` (which already require verified
  coordinates before any reconstruction).

The input unit is the canonical record of `source_canonicalization_v1`
(`record_id`, `sequence_sha1`). Acquired and canonical files are never edited.
Every result is a new, versioned, derived layer.

## Principles

1. **Location is not label evidence.** A record that maps to a genome is
   located, not validated. Mapping never changes `label` or `source_class`.
   Overlap with annotations is a separate, later context layer.
2. **Declared before inferred.** Coordinates stated by the source are verified
   first. Search or alignment runs only for records without usable declared
   coordinates, or whose declared coordinates fail verification.
3. **No silent choice.** Every candidate locus that meets the acceptance rule
   is persisted. A record with several candidates is `ambiguous`; none is
   promoted to primary.
4. **No arbitrary reference.** An organism, assembly, release, or convention is
   recorded only with its evidence level. When evidence is missing or
   conflicting, the field stays empty and the conflict is recorded.
5. **Original values are kept.** Source coordinates are stored verbatim next
   to their normalized form, with the named conversion rule that links them.
6. **Frozen before execution.** Tools, versions, parameters, reference files,
   and acceptance thresholds are fixed in a versioned config before a run. No
   model outcome may influence them.

## Stage A: reference identification

For each canonical collection, build a reference registry with one entry per
reference role:

| Role | Examples |
| --- | --- |
| `publication` | article DOI, PMID, supplement |
| `release` | repository commit, download URL, database release |
| `organism` | species and strain, NCBI Taxonomy ID |
| `assembly` | assembly accession and version (`GCF_`/`GCA_`), UCSC name (`hg38`) |
| `contig` | sequence accession and version (`NC_000913.3`) |
| `annotation` | TSS map, RefSeq table, EPD/EPDnew release, GFF3 |
| `construction` | window definition, negative-sampling rule, filtering steps, seed |

Every entry records an **evidence level**:

| Level | Meaning |
| --- | --- |
| `declared` | stated by the authors in the publication, supplement, README, or file header |
| `inferred` | derived by the project from indirect evidence (counts, names, header patterns) and not yet tested against sequence |
| `verified` | reproduced by the project: sequences recreated from, or uniquely mapped to, the reference under this protocol |
| `conflicting` | two or more sources disagree; all values are kept |
| `unknown` | no evidence found; the search performed is recorded |

Each entry also stores the source of the claim (document plus location), the
URL or accession, version or release, acquisition time, SHA-256 of the
supporting file when one was acquired, and a free-text note. A reference file
that is used for mapping must exist in an acquisition manifest. Files that are
only in `data/raw/` (for example the CDBProm RefSeq genomes, finding F-027) are
first acquired under a new acquisition config. `source_acquisition_v1` stays
unchanged.

Promoting an entry from `declared` or `inferred` to `verified` requires a
completed Stage B result, and is logged in `docs/provenance/research_log.md`.
A changed level is a new finding row in `docs/provenance/findings_register.md`.
The old row is never rewritten.

## Stage B: coordinate mapping

### B1. Declared coordinates

When a record carries coordinates, or carries an identifier that a dated
resource resolves to coordinates (EPD/EPDnew, RegulonDB, DBTSS, Promotech BED):

1. Parse the verbatim value into contig, start, end, strand, and the source
   convention (see [Coordinate conventions](#coordinate-conventions)).
2. Convert to the canonical convention with a named rule.
3. Extract the oriented sequence from the declared reference.
4. Compare it with the canonical sequence.

The result is `verified` only on an exact full-length match. If the declared
locus fails, the record goes to B2 and the declared value is kept with
`declared_check = mismatch`.

Each source convention is first tested on a predeclared pilot sample (the
first 20 records by `sequence_sha1` rank, plus every strand) before it is
applied to a whole collection. A convention whose pilot fails is reported
and is not tuned against the full collection.

### B2. Exact search

Exact search covers sequence-only records, and declared records that failed
B1. It looks for every occurrence of the record, on both strands, across all
contigs of each candidate assembly (including plasmids). The engine is an
in-house exact matcher with full enumeration, so that multiplicity is
complete. Upper-case comparison is used after soft-mask removal.

Reference bases other than A/C/G/T in the genome are recorded. They match a
record base only under the IUPAC compatibility table, and such a match is
classed `iupac_compatible`, not `exact`.

### B3. Alignment fallback

Alignment runs only for records that B2 leaves without a hit, so that
divergent, partial, and wrong-assembly cases are characterized. The tool is
Bowtie 2 in `--end-to-end` mode (its default), with `-k <cap>` to report up to
`cap` distinct alignments per read. A `--local` run is diagnostic only and
never yields an accepted locus.

The command line, tool version, index hash, and parameters are frozen in the
config. Every tool runs from a locked, versioned environment whose lock file
hash is recorded.

**Acceptance rule for version 1** (frozen in the config, not tuned):

| Class | Rule |
| --- | --- |
| `exact` | full query length, edit distance 0 |
| `iupac_compatible` | full length; every difference involves a non-ACGT base on either side |
| `divergent` | full query length (end-to-end), edit distance `1 <= NM <= max(1, floor(0.02 x length))` |
| `partial` | only a local alignment covering less than the full query; diagnostic, never accepted |
| no hit | nothing above |

### B4. Multiplicity

`n_candidates` counts every accepted locus. When the search stops at `cap`,
`n_candidates_truncated = true`, and the record can never be `verified`. A
reverse-complement occurrence is a separate candidate. Palindromic loci, which
match on both strands at one interval, are stored once with `strand = .`.

### Record status

| Status | Rule |
| --- | --- |
| `not_evaluated` | no attempt yet, or the reference is unavailable (with `status_reason`) |
| `verified` | exactly one `exact` or `iupac_compatible` candidate, on a reference whose identity is `declared` or `verified`, and no conflict with a declared locus |
| `ambiguous` | two or more accepted candidates (including truncated searches) |
| `inconsistent` | located, but contradicts a declared fact: declared locus mismatch, other assembly or organism, other strand, only `divergent` candidates, or TSS offset different from the declared window |
| `unmapped` | evaluated against every candidate reference with no accepted candidate |

Every non-`verified` status carries one or more `status_reason` codes:
`reference_unavailable`, `assembly_unresolved`, `declared_locus_mismatch`,
`assembly_mismatch`, `organism_mismatch`, `strand_mismatch`,
`sequence_divergence`, `tss_offset_mismatch`, `multiple_loci`,
`search_truncated`, `ambiguous_bases`, `label_conflict`, `no_candidate`.
`label_conflict` is copied from the canonical `cross_label_collision` flag and
records the conflict, not a decision about it.

## Coordinate conventions

All normalized coordinates use **0-based, half-open intervals on the forward
strand of the contig**, the convention of UCSC BED and database tables. The
UCSC "position" format shown in the browser is 1-based and fully closed.
Converting it adds 1 to the start (to read 1-based) or subtracts 1 from the
start (to go from 1-based to 0-based), and leaves the end unchanged
([UCSC coordinate counting systems](https://genome-blog.gi.ucsc.edu/blog/?p=333)).
SAM `POS` is the "1-based leftmost mapping POSition", and FLAG `0x10` marks a
reverse-complemented sequence
([SAM specification](https://github.com/samtools/hts-specs)).

`strand` is `+` or `-` relative to the contig. For `-`, the record sequence
equals the reverse complement of `[start, end)`.

Named conversion rules (each fixture-tested before use):

| Rule | Source form | Status |
| --- | --- | --- |
| `bed0_halfopen` | BED rows (EPDnew, Promotech BED) | Evidence: UCSC format definition |
| `ucsc_position_1closed` | UCSC `range=chr:a-b` (Bhandari headers) | Evidence: B1 pilot passed on hg38, sacCer3, and mm10 (F-041) |
| `colon_range_strand` | `acc:a-b(+/-)` with `b - a` equal to the length (Promotech 40-nt) | Hypothesis: 0-based half-open, as written by `bedtools getfasta`; pilot required |
| `ncbi_efetch_complement` | `acc:cA-B` (GraphPro negatives) | Hypothesis: NCBI 1-based closed complement range; pilot required |
| `epd_bed_tss` | EPDnew BED 60-nt interval to TSS base | Implemented in `capsprom.data.epd_resolution` |
| `sam_pos_1based` | aligner output | Evidence: SAM specification |

`source_coordinate_text` keeps the verbatim string, and `conversion_rule`
names the rule. A conversion is never inferred silently per record.

## TSS and non-promoter provenance

- **Promoters.** `tss_genomic` is the 0-based contig position of the TSS base,
  stored only when a source declares the TSS (an annotation row, an EPD
  identifier, or a window definition agreed between publication and release,
  which is the canonical `tss_index`). `tss_source` names it. A mapped locus
  alone never implies a TSS. CDBProm's undocumented TSS offset (F-018) stays
  empty.
- **Non-promoters.** `tss_genomic` is always empty. Provenance is recorded as
  the declared construction rule (`construction_rule`), the paired promoter
  `record_id` when the source states one (`paired_record_id`), and the evidence
  level of each. No artificial TSS, pairing, or seed is assigned.

## Persistence

Root: `data/coordinates/reference_coordinate_mapping_v<N>/` (ignored by Git).
Committed summaries go to
`manifests/provenance/reference_coordinate_mapping_v<N>/` and hold hashes and
counts, never sequences.

| File | Grain |
| --- | --- |
| `reference_registry.json` | one entry per collection and reference role (Stage A) |
| `records/<collection_id>.csv.gz` | one row per canonical record |
| `loci/<collection_id>.csv.gz` | one row per record and candidate locus (zero or more per record) |
| `evidence/<collection_id>/` | aligner outputs (SAM/PAF), pilot reports, parser logs |
| `cache/` | sequence-level results keyed by `sequence_sha1 + reference_sha256 + method_id` |
| `mapping_manifest.json` | config SHA-256, inputs, per-shard status and output SHA-256, `runs[]` |

All CSV.gz files are byte-reproducible (fixed gzip mtime, no embedded name,
stable row order by `record_id` and then locus), as for canonical tables.

### Record table (`records/`)

| Field | Content |
| --- | --- |
| `mapping_version` | config name and SHA-256 |
| `record_id`, `collection_id`, `sequence_sha1`, `length` | link to the canonical record |
| `source_class`, `label` | copied; never modified |
| `organism_declared`, `taxon_id`, `organism_evidence` | per Stage A |
| `assembly_accession`, `assembly_name`, `assembly_evidence` | per Stage A |
| `declared_coordinate_text`, `declared_conversion_rule` | verbatim value and rule, or empty |
| `declared_check` | `match`, `mismatch`, `unparsed`, or `absent` |
| `method_id` | `declared`, `exact_search`, `bowtie2_end_to_end`, ... (resolved in the config) |
| `n_candidates`, `n_candidates_truncated` | multiplicity |
| `status`, `status_reason` | the record status above |
| `tss_genomic`, `tss_source`, `tss_evidence` | promoters only, when declared |
| `construction_rule`, `paired_record_id`, `construction_evidence` | non-promoters only |
| `evidence_path`, `run_id` | link to evidence and the run record |

### Locus table (`loci/`)

| Field | Content |
| --- | --- |
| `record_id`, `locus_rank` | link; rank by score, then contig and start |
| `assembly_accession`, `contig_accession`, `contig_name_source` | NCBI accession.version, plus the name as written by the source (`chr1`) |
| `start`, `end`, `strand` | 0-based half-open, forward-strand contig coordinates |
| `match_class` | `exact`, `iupac_compatible`, `divergent`, `partial` |
| `edit_distance`, `mismatches`, `query_coverage`, `aligner_score`, `second_best_score`, `mapq` | quality metrics, empty when not applicable |
| `ambiguous_bases_record`, `ambiguous_bases_reference` | counts of non-ACGT bases |
| `coordinate_source` | `declared`, `resolved_identifier`, `exact_search`, `alignment` |
| `reference_file_sha256` | SHA-256 of the genome file used |

## Execution, resumption, and reuse

- **Sharding.** Work is split into shards of one collection and one reference
  (and, for collections above 20,000 records, contiguous `record_id` ranges).
  Each shard's inputs hash is the canonical table SHA-256, the reference SHA-256,
  and the config SHA-256.
- **Atomicity.** Every shard output is written to a temporary sibling and
  renamed, and `mapping_manifest.json` is rewritten with
  `capsprom.state.write_json_atomic` after each shard. A rerun skips shards whose
  inputs hash and output SHA-256 still match.
- **Run records.** Each run appends a `runs[]` entry: UTC start and end, status,
  command, shard filter, tool versions, environment lock hash, code commit and
  clean flag, and module SHA-256. This mirrors the acquisition manifest.
- **Long jobs.** Index builds and alignments run detached and logged (`nohup`,
  or a remote host following `docs/remote_job_operations.md`). Interruption
  leaves at most one shard incomplete. Index files are cached and keyed by
  reference SHA-256, tool version, and build parameters, so they are never
  rebuilt for an unchanged key.
- **Reuse.** Before searching, the cache is consulted by `sequence_sha1`,
  reference, and method, so identical sequences across collections (for
  example GraphPro, Promotech, and CDBProm on shared genomes) are located once.
  A changed config, reference, or rule creates `v<N+1>` and never overwrites a
  validated result.
- **Querying.** Downstream builds read the record and locus tables, filtered by
  `status`. A dataset build that uses coordinates names the mapping version and
  manifest SHA-256 in its own config.

## Validation criteria

A mapping version is accepted only when all of these hold:

1. **Coverage.** Every canonical record of every collection in scope has
   exactly one row in `records/`. No record is silently absent, and
   `not_evaluated` is a status.
2. **Consistency.** `n_candidates` equals that record's row count in `loci/`
   (truncation aside). `verified` implies exactly one accepted candidate.
   `ambiguous` implies two or more.
3. **Round trip.** Re-extracting every `verified` locus from the reference
   reproduces the canonical sequence exactly. The check covers all verified
   loci, not a sample.
4. **Convention fixtures.** Each conversion rule passes unit tests on
   hand-built cases (both strands, contig start and end, 1-based versus 0-based
   boundaries), and its B1 pilot passes before full use.
5. **Search completeness.** On synthetic genomes with planted occurrences
   (repeats, reverse complements, palindromes, overlapping hits, plasmids, IUPAC
   bases), exact search reports every planted locus and no other.
6. **Determinism.** Two runs from the same inputs produce byte-identical
   outputs. A resumed run equals an uninterrupted one.
7. **Reproduced earlier evidence.** The protocol reproduces existing verified
   results: GraphPro Human/Mouse recreation from EPDnew, and the R-011 CDBProm
   exact mapping counts on the replaced assemblies. A discrepancy is
   investigated before acceptance.
8. **Independent sample audit.** A predeclared stratified sample (by status and
   collection) is checked manually against the source documents, and its
   result is logged.
9. **Records.** The research log entry, findings for every changed evidence
   level, and committed summaries exist before any build uses the result.

## Primary references

- UCSC Genome Browser, "The UCSC Genome Browser Coordinate Counting Systems":
  <https://genome-blog.gi.ucsc.edu/blog/?p=333>
- SAM/BAM format specification (`SAMv1`): <https://github.com/samtools/hts-specs>
- Bowtie 2 manual (`-k`, `--end-to-end`, `XS:i`, `NM:i`, MAPQ):
  <https://bowtie-bio.sourceforge.net/bowtie2/manual.shtml>
- NCBI assembly accession format (`GCF_`/`GCA_` with version):
  <https://support.nlm.nih.gov/knowledgebase/article/KA-03451/en-us>
- Source-specific publications and releases:
  `docs/dataset_reconstruction_sources.md`.
