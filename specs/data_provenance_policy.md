# Data Provenance Policy

This policy governs how CapsProm obtains, preserves, derives, and documents
data. It complements `specs/source_acquisition_protocol.md` (how files are
acquired and canonicalized) and `specs/dataset_integrity_audit.md` (how derived
datasets are checked).

## 1. Reference collection

- The reference collection for all future experimental datasets is
  **`source_acquisition_v1`** (`configs/source_acquisition_v1.yaml`, output
  `data/acquired/source_acquisition_v1/`) together with its canonical tables
  **`source_canonicalization_v1`** (`configs/source_canonicalization_v1.yaml`,
  output `data/canonical/source_canonicalization_v1/`).
- Its identity is the pair of config SHA-256 values recorded in
  `acquisition_manifest.json` and `canonical_manifest.json`. A committed copy of
  both manifests lives in `manifests/provenance/source_acquisition_v1/`.
- `data/raw/` is legacy. It is preserved unchanged because completed
  experiments were derived from it, but it is not a reference collection.

## 2. What every acquisition records

| Requirement | Where it is recorded |
| --- | --- |
| Repository or host, URL | `acquisition_manifest.json` → `files.<key>.url`; config `repository`, `landing_page` |
| Access identifier | Full Git commit (`commit`), Google Drive file ID (in the URL), release number (`release`), assembly name (UCSC path) |
| Version or release | Config `release`/`commit`; upstream-reported dates in `source_release_metadata.json` |
| Acquisition date and time with time zone | `files.<key>.acquired_at` (ISO 8601, UTC offset) per file; `runs[].started_at`/`finished_at` per run |
| Files obtained and checksums | `files.<key>`: `size_bytes`, `sha256`, `md5`, `git_blob_sha1`, `expected`, `verified_against` |
| Upstream publication or update date | `source_release_metadata.json`: pinned commit author/committer dates; HTTP `Last-Modified`/`ETag`, with `observed_at` |
| Commands, parameters, tools | `runs[].command`, `runs[].only_sources`, `runs[].tool` (Python, platform, code commit, clean flag, module SHA-256, user agent) |

Acquisition date and source date are never merged: `acquired_at` is when the
project copied a file; commit dates and `Last-Modified` describe the upstream
copy as the source reports it. Files without such metadata keep it empty.

Runs created before run records existed are documented retrospectively in
`docs/provenance/research_log.md`, labelled as such.

## 3. Preservation

- Acquired files are never edited in place. Cleaning happens only in
  canonicalization, which writes new files.
- A changed source, URL, commit, digest, or cleaning rule requires a new
  versioned config and a new output directory (`source_acquisition_v2`, and so
  on). The code refuses to resume a manifest whose config hash differs.
- A new acquisition never replaces `v1`, and an experiment never mixes inputs
  from two acquisitions unless its own config names both.

## 4. Lineage of experimental datasets

Every experimental dataset must be traceable to acquired files:

1. **Builds from the reference collection.** A dataset build config names the
   canonical collection IDs and the canonical manifest SHA-256 it reads, and the
   build report records, per output, the input `record_id`s or their hash, plus
   each transformation, filter, exclusion, and correction with row counts before
   and after. `record_id` locates every row in an acquired file and record
   index.
2. **Legacy builds.** Datasets already built from `data/raw/` are linked to the
   reference collection by evidence, in this order of strength:
   - *byte replay*: the legacy builder, fed the acquired files under their legacy
     names, reproduces the dataset's recorded SHA-256 values;
   - *byte identity*: the legacy input file equals an acquired file or archive
     member;
   - *sequence equivalence*: the per-class sequence multiset equals a validated
     canonical collection;
   - *unverified*: none of the above. Such datasets cannot support confirmatory
     claims until linked.

The evidence for existing datasets is in `docs/provenance/dataset_lineage.md`.

Future builds also declare their data condition (released-filtered or
reconstructed) and class every intervention as filtering, metadata correction,
or reconstruction, under `specs/dataset_condition_policy.md`.

## 5. Legacy files and unknown dates

- Every legacy file is inventoried by SHA-256 and classified by the evidence
  above (`manifests/provenance/source_acquisition_v1/legacy_raw_inventory.json`).
- A legacy acquisition date is recorded only when a dated record exists (a log,
  a commit, a dated note). Otherwise it is recorded as **unknown**. File
  modification times, archive timestamps, and directory listings are not
  evidence of acquisition date.

## 6. Recording process and findings

- `docs/provenance/research_log.md` is a dated, append-only log of procedures,
  decisions with their justification, problems, and verifications. Each entry
  names the data version (config or manifest SHA-256), the code commit (or
  "uncommitted" plus module SHA-256), and the experiment or run identifiers it
  concerns.
- `docs/provenance/findings_register.md` lists findings with a stable ID and one
  epistemic status:
  - **Fact**: reproducible from a named record or command.
  - **Hypothesis**: a plausible explanation that has not been verified.
  - **Limitation**: a known gap or constraint on what the evidence supports.
  A finding changes status only by a new dated entry; earlier text is not
  rewritten.
- Conversation history is never the only record of a decision or finding.

## 7. Technical and academic documentation

Both draw on the same records and must not disagree with them:

- Technical documentation (`specs/`, `docs/data_pipeline_operations.md`,
  `docs/source_acquisition_v1_report.md`) covers operation, architecture,
  configuration, commands, validation, failure recovery, and reproduction.
- Academic documentation (`docs/thesis/`) covers aims, methodological
  rationale, selection and treatment criteria, results, interpretation, and
  limitations, with references. It cites findings by their meaning rather than by
  transcribing logs or commands, and every number it reports must exist in a
  committed record.
