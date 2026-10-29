# Source Acquisition and Canonicalization Protocol

## Decision

Future datasets are built from freshly acquired upstream files, not from the
hand-collected copies in `data/raw/`. Acquisition and canonicalization are two
separate, versioned stages:

1. `configs/source_acquisition_v1.yaml` declares every upstream file and the
   digest it must reproduce. Output: `data/acquired/source_acquisition_v1/`.
2. `configs/source_canonicalization_v1.yaml` declares how each acquired file is
   parsed into a collection. Output: `data/canonical/source_canonicalization_v1/`.

`data/raw/` is preserved unchanged as the provenance of completed experiments
and is used only as a parity reference. Neither stage selects, filters,
crops, splits, or relabels records; those decisions belong to later, separately
versioned dataset builds that read the canonical tables.

The source inventory and the publication-versus-release comparison that
motivate the declared counts are in `docs/dataset_reconstruction_sources.md`.

## Stage 1: acquisition

- GitHub sources are pinned to a full 40-hex commit. The file list is expanded
  from that commit's tree and every blob must reproduce the Git blob SHA-1 the
  tree reports. The expanded list is frozen in the manifest on first use.
- Direct URLs are verified against every declared digest (`sha256`, `md5`, or
  `git_blob_sha1`). Digests published upstream (UCSC `md5sum.txt`) or already
  recorded by earlier project contracts are declared. A file without a declared
  digest is trusted on first acquisition and verified against the manifest on
  every later run; the canonicalization stage then checks it against legacy
  copies where they exist.
- A server that omits its intermediate certificate is reached by trusting the
  issuer's AIA copy of that intermediate, pinned by SHA-256. TLS verification is
  never disabled.
- Each file is streamed to a temporary sibling and atomically renamed. The
  manifest (`acquisition_manifest.json`) is written atomically after every
  verified file, so an interrupted run resumes and skips files whose size and
  SHA-256 still match.
- The manifest records the config SHA-256. A run with a changed config is
  refused; changing sources, URLs, commits, or digests requires a new version.
- Every executed run, including a pure re-verification, appends a `runs[]`
  entry (start and end time in UTC, status, command, source filter, Python,
  platform, code commit and clean flag, module SHA-256). Each downloaded file
  records `acquired_at` and the upstream `Last-Modified`, `ETag`,
  `Content-Length`, and `Content-Type` headers. These describe the upstream copy
  and are never used as the acquisition date.

## Stage 2: canonicalization

Each collection groups the inputs of one biological dataset as released by its
source (for example one CNNProm organism, one iPro-MP species with its train and
test files, or one BDGP promoter set with its CDS and intron negatives).

### Cleaning

Cleaning is limited to removing whitespace inside sequences and uppercasing
bases. No record is dropped, cropped, padded, deduplicated, or relabelled.
Whether a case change occurred is kept per record.

### Canonical table

One byte-reproducible `<collection_id>.csv.gz` per collection (gzip with fixed
mtime and no embedded file name), with these columns:

| Column | Meaning |
| --- | --- |
| `record_id` | `<collection_id>:<source file>[!<zip member>]:<7-digit record index>` |
| `collection_id`, `source`, `organism`, `domain` | Collection metadata from the config |
| `source_file`, `source_member`, `record_index` | Exact origin inside the acquisition root |
| `source_split` | Split declared by the source (`train`, `test`, `training`, `validation`) or `none` |
| `source_class` | Class as released (`positive`, `negative`, `negative_cds`, `negative_intron`, `negative_intergenic`, `negative_downstream`, `negative_opposite_strand_cds`, `negative_post_first_exon`, `negative_random_genomic`) |
| `label` | 1 for promoters, 0 for every negative class |
| `original_header` | FASTA header without `>`; empty for headerless line files |
| `sequence`, `length`, `sequence_sha1` | Cleaned sequence and its identity |
| `tss_index` | Zero-based TSS position for positives only, filled only where publication and release agree on the window |
| `strict_dna`, `invalid_symbols` | Whether the sequence is only A/C/G/T, and the other symbols present |
| `case_normalized` | Whether uppercasing changed the sequence |
| `length_matches_expected` | Comparison with the declared release length, or empty if none is declared |
| `duplicate_of` | First `record_id` with the same sequence and label in the collection, or empty |
| `cross_label_collision` | Whether the same sequence occurs with both labels in the collection |

### Validation

A collection passes only when:

1. the number of records per `source_class` equals the declared release count
   exactly; and
2. where `legacy_inputs` are declared, the multiset of sequences per class equals
   the one parsed from the corresponding `data/raw/` copy.

Publication counts, length mismatches, non-ACGT symbols, duplicates, and
cross-label collisions are reported but do not fail validation, because they are
properties of the released data that later builds must handle explicitly.

`canonical_manifest.json` records the config SHA-256, the SHA-256 of every input
(checked against the acquisition manifest before parsing) and output, and the
validation report. It is written atomically after each collection; an unchanged
collection is skipped on rerun.

## Reference files

Genomes (UCSC 2bit, Promotech FASTA), coordinate files (EPDnew and Promotech
BED, Promotech CSV), supplementary tables, the CDBProm DDS matrix, and code files
are acquired and hashed but not canonicalized. They are inputs for later
coordinate reconstruction.

## Commands

```bash
PYTHONPATH=src python scripts/acquire_sources.py            # plan only
PYTHONPATH=src python scripts/acquire_sources.py --execute
PYTHONPATH=src python scripts/canonicalize_sources.py
```

Provenance records, lineage evidence, and failure recovery are covered by
`specs/data_provenance_policy.md` and `docs/data_pipeline_operations.md`.
