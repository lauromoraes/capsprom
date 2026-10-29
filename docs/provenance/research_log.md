# Data Research Log

Dated, append-only log of data procedures, decisions, problems, and
verifications (`specs/data_provenance_policy.md` §6). Times are UTC. Each entry
names the data version, the code state, and the records it produced. Findings
are referenced by their ID in `docs/provenance/findings_register.md`.

Code state notation: a commit hash, or `uncommitted on <base commit>` plus the
SHA-256 of the module that ran, when the change was not yet committed.

---

## R-001 · 2026-10-27 · Source inventory and publication comparison

- **Procedure.** Listed the datasets distributed by every evaluated study, then
  compared each publication's stated counts, windows, and sources with its
  released files and with `data/raw/`.
- **Decision.** Use upstream repositories, not `data/raw/`, as the basis for
  future datasets, because several releases disagree with their publications and
  `data/raw/` has no acquisition record.
- **Records.** `docs/dataset_reconstruction_sources.md`.
- **Code state.** Documentation only.
- **Findings.** F-016, F-018.

## R-002 · 2026-10-27 to 2026-10-28 · Acquisition v1 (retrospective entry)

- **Data version.** `configs/source_acquisition_v1.yaml`, SHA-256
  `8e08e61424534884d63bacc3742c7f13c115be1b1922ffb6016f501a17eb9d32`.
- **Scope decision (user).** Active sources (Bhandari, CDBProm, CNNProm,
  GraphPro), iPro-MP, EPD and BDGP, plus primary references (Promotech, EPDnew
  BED, UCSC genomes). The output goes into a new versioned directory; `data/raw/`
  stays intact.
- **Commands.**
  `PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --execute`, invoked
  more than once and resuming each time. `hg38.2bit` (835 MB) finished last, in a
  detached background invocation. How the files split across invocations was not
  recorded (F-006).
- **Timing.** The first and last per-file `acquired_at` are
  2026-10-27T23:40:08+00:00 and 2026-10-28T00:22:43+00:00.
- **Problem.** The first attempt failed with `CERTIFICATE_VERIFY_FAILED` for
  `aw.iimas.unam.mx`. A `tls_intermediate` pin was added to the config before any
  manifest was kept. The six files of that attempt were deleted together with its
  manifest, because the config hash changed (F-003).
- **Code state.** Uncommitted on `6bb5e4e`. Run records did not exist yet, so the
  tool versions of this run were not recorded (F-006).
- **Verification.** Every declared digest matched, and every GitHub blob matched
  its Git blob SHA-1 (F-001).
- **Records.** `data/acquired/source_acquisition_v1/acquisition_manifest.json`;
  report `docs/source_acquisition_v1_report.md`.

## R-003 · 2026-10-28 · Canonicalization v1

- **Data version.** `configs/source_canonicalization_v1.yaml`, SHA-256
  `eb5460a0c3322f508576ea8b10d6a741296e36238ea75e0a1326363264f89991`.
- **Command.** `PYTHONPATH=src .venv/bin/python scripts/canonicalize_sources.py`.
- **Decision.** Cleaning is limited to removing whitespace and uppercasing.
  Duplicates, collisions, length mismatches, and non-ACGT symbols are flagged,
  never removed, so later builds must treat them explicitly and visibly.
- **Verification.** All 64 collections pass (F-010).
- **Findings.** F-011 to F-015, F-017, F-019.
- **Records.** `data/canonical/source_canonicalization_v1/canonical_manifest.json`.

## R-004 · 2026-10-28 · Run records and re-verification

- **Procedure.** Extended `capsprom.data.acquisition`. Each executed run now
  appends a `runs[]` entry: start and end time, status, command, source filter,
  Python, platform, code commit and clean flag, module SHA-256, and user agent.
  Each newly downloaded file now records its `Last-Modified`, `ETag`,
  `Content-Length`, and `Content-Type` response headers.
- **Command.** `PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --execute`
  (detached, log `data/acquired/source_acquisition_v1/logs/reverify_20261028.log`).
- **Result.** Run 2026-10-28T20:39:32Z–20:40:59Z completed with 210 of 210 files
  `skipped_verified` and nothing downloaded. Code state: uncommitted on
  `6bb5e4e`, `acquisition.py` SHA-256 `a8e71e40…`.
- **Decision.** Re-verify instead of re-downloading. The files had already been
  verified, and a fresh download would replace acquisition timestamps that are
  evidence.
- **Limitation.** Files downloaded before this change have no recorded response
  headers. Their upstream dates come from R-005 instead.

## R-005 · 2026-10-28 · Upstream release metadata

- **Command.** `PYTHONPATH=src .venv/bin/python scripts/record_provenance.py source-metadata`.
- **Procedure.** Recorded the author and committer dates of every pinned GitHub
  commit, and sent a `HEAD` request for every URL source, observed at
  2026-10-28T20:42:04Z.
- **Records.** `manifests/provenance/source_acquisition_v1/source_release_metadata.json`.
- **Findings.** F-004, F-005.

## R-006 · 2026-10-28 · Legacy `data/raw/` inventory

- **Command.** `PYTHONPATH=src .venv/bin/python scripts/record_provenance.py legacy-inventory`.
- **Problem.** The first attempt raised `KeyError: 'source_class'`, because the
  iPro-MP legacy inputs derive classes from headers. Fixed by treating them as
  equivalent only when all classes match, then re-run.
- **Decision.** Accept only two kinds of date evidence: a dated record written at
  retrieval (`retrieved_utc`), and the first commit that recorded a file's hash.
  The second is reported as an upper bound (`no_later_than`). File modification
  times are never used. The inventory was re-run with these rules
  (observed 2026-10-28T20:49:25Z).
- **Records.** `manifests/provenance/source_acquisition_v1/legacy_raw_inventory.json`.
- **Results.** Of 190 files, 92 are byte-identical, 33 sequence-equivalent, and
  65 not reproduced. Dates: 126 unknown, 44 recorded, 20 upper bound
  (F-025 to F-028).

## R-007 · 2026-10-28 · Replay of the regenerated-v3 build from acquired files

- **Command.** `PYTHONPATH=src .venv/bin/python scripts/record_provenance.py replay-v3`.
- **Purpose.** Establish whether the 26 regenerated-v3 datasets, including the
  18 confirmatory datasets, are reproduced from the reference acquisition without
  changing any experiment.
- **Problem.** The first replay reported every intermediate FASTA as different.
  Inspection showed identical headers and sequences: the legacy files wrap at 60
  columns and the current writer at 80. GraphPro `Cpne` had also been renamed
  from `clostridium_phytofermentans` to `chlamydophila_pneumoniae` after v3 was
  built. The replay now compares FASTA by record, reports byte equality
  separately, and maps the rename explicitly.
- **Records.** `manifests/provenance/source_acquisition_v1/regenerated_v3_replay.json`
  (final replay observed 2026-10-28T20:50:06Z), with staging under ignored
  `data/interim/provenance_replay_regenerated_v3/`.
- **Results.** The train and test CSVs of 25 of the 26 datasets, including all 18
  confirmatory ones, are byte-identical. For GraphPro `Cpne`, the pooled rows are
  identical and only the partition differs (F-020 to F-022).
- **Decision.** No experiment is re-run. The confirmatory datasets are already
  reproduced from the reference collection, so their results stand with
  established lineage.

## R-008 · 2026-10-28 · Experiment records linked to datasets

- **Command.** `PYTHONPATH=src .venv/bin/python scripts/record_provenance.py experiment-links`.
- **Procedure.** Collected the dataset hashes that local experiment records store
  (`*_dataset_sha256`, `train_sha256`, `test_sha256`) and matched them against the
  replay-verified outputs of R-007.
- **Records.** `manifests/provenance/source_acquisition_v1/experiment_dataset_links.json`.
- **Results.** 287 of 298 run summaries are fully linked. The basic CapsProm
  campaign plan has 25 of 26 hashes linked. The unlinked records use builds that
  have not been replayed (F-023, F-024).

## R-009 · 2026-10-28 · Policy and documentation

- **Procedure.** Wrote the normative policy (`specs/data_provenance_policy.md`),
  the operations guide (`docs/data_pipeline_operations.md`), this log, the
  findings register, the lineage document, and the thesis section
  `docs/thesis/data_acquisition_provenance.tex`, all from the records above. The
  thesis built without undefined citations or references.
- **Code state.** Uncommitted on `6bb5e4e`. `make check` passed.

## R-010 · 2026-10-28 · Removal of an out-of-scope legacy directory

- **Procedure.** At the user's request, deleted one legacy `data/raw/`
  directory that held a single README (559 bytes, SHA-256 `a86373ec…`) and no
  sequence data. No acquisition config, canonical collection, processed dataset,
  split, cache, experiment record, test, or thesis citation referenced it. Its
  rows were removed from the current-state documents
  (`docs/dataset_reconstruction_sources.md`, `docs/provenance/dataset_lineage.md`,
  `docs/source_acquisition_v1_report.md`).
- **Command.** `PYTHONPATH=src .venv/bin/python scripts/record_provenance.py legacy-inventory`
  (observed 2026-10-28T22:05:11Z).
- **Verification.** The regenerated inventory equals the previous one with the
  removed file's entry and summary group dropped; every other entry, the config
  hashes, and the acquisition index are unchanged.
- **Records.** `manifests/provenance/source_acquisition_v1/legacy_raw_inventory.json`
  (SHA-256 `1de0c06d…`).
- **Results.** 189 files: 92 byte-identical, 33 sequence-equivalent, 64 not
  reproduced. Dates: 125 unknown, 44 recorded, 20 upper bound (F-030).
- **Not changed.** No dataset, partition, or experiment result depended on the
  file, so nothing was regenerated or invalidated. The off-machine backup on
  `bioserver04` (`local-archive-v1`) still holds a copy.
- **Code state.** Uncommitted on `6bb5e4e`.

## R-011 · 2026-10-27 to 2026-10-28 · CDBProm reference genomes v1

- **Procedure.** Downloaded the 11 NCBI assemblies declared in
  `configs/control_coordinate_feasibility_inventory_v1.yaml` (FASTA, GFF3,
  assembly report) and ran an exact, both-strand search of every CDBProm
  1,001 bp sequence (read-only on the raw files). Anabaena YBS01
  (GCF_009498015.1) mapped 0/2,517 positives and Salmonella strain 94
  (GCF_031197025.1) 834/981. Candidate strains were tested; only Nostoc sp.
  PCC 7120 (GCF_000009705.1) and S. Typhimurium SL1344 (GCF_000210855.2)
  mapped every sequence.
- **Decision (user).** Replace the two assemblies in the reference directory.
  The rejected accessions stay recorded in the manifest's `replaced` block.
- **Verification.** The FASTA SHA-256 of both new downloads equals the copies
  used for the full mapping.
- **Records.** `data/raw/references/cdbprom_genomes_v1/manifest.json`
  (SHA-256 `8d19ef4e…`).
- **Not done.** The publication's own accession list was not checked; no
  reference-genome config exists yet. The inventory config still lists three
  wrong accessions (CP034058.1, CP133487.1, AL939104.1).
- **Code state.** Scratch scripts outside the repository; uncommitted on `6bb5e4e`.

## R-012 · 2026-10-29 · Off-machine copy of the R-010 file

- **Verification.** Read-only check of `bioserver04` and `bioserver03`. The
  `bioserver04` `local-archive-v1` archives (`data`, `mlruns`, `outputs`,
  `mlflow.db`) were removed on 2026-10-28 with the user's authorization, so the
  copy noted in R-010 no longer exists. Neither host, nor the `capsprom-v4-*`
  snapshots, holds the file; only the two `local-archive-v1` manifests list
  its path and hash.
- **Code state.** Documentation only; uncommitted on `6bb5e4e`.

## R-013 · 2026-10-29 · Remote manifest lines removed

- **Procedure.** At the user's request, removed the single line for the R-010
  file (`data/raw/DeeProPre/README`, SHA-256 `a86373ec…`) from
  `bioserver04:~/backups/capsprom/local-archive-v1/manifest.sha256`
  (5,920 → 5,919 lines, SHA-256 `31a50153…`) and
  `manifest.sha256.pre-feature-removal-20261027` (6,536 → 6,535 lines,
  SHA-256 `2b787834…`), and from the local mirror
  `tmp/storage_archive_v1/manifest.sha256`. Each edit was checked to drop
  exactly one line; file modes and modification times were preserved.
- **Verification.** No remaining line in either remote manifest names the file.
  The 2026-10-28 `s3.log` on `bioserver04` still records a failed lookup of its
  path and was not edited.
- **Code state.** Documentation only; uncommitted on `6bb5e4e`.

## R-014 · 2026-10-29 · Provenance work committed

- **Procedure.** Committed the acquisition, canonicalization, and provenance
  code, configs, specs, documentation, and manifests recorded in R-001 to R-013
  as `44ad351` ("Acquire, canonicalize, and record provenance of source data"),
  on top of `99ebe13`, and pushed it to `origin` on branch
  `codex/estruturar-projeto-de-doutorado`. `data/acquired/` and
  `data/canonical/` remain untracked.
- **Verification.** `make check` passed before committing (ruff clean, 202
  tests). The `module_sha256` recorded in the acquisition manifest run record
  (`a8e71e40…`) equals the SHA-256 of `src/capsprom/data/acquisition.py` in
  `44ad351`. Committed SHA-256 values of the other modules:
  `canonical_sources.py` `0f3d1210…`, `provenance.py` `d7361f10…`,
  `scripts/record_provenance.py` `a1638824…`; no run record stores these, so
  their equality with the code that produced earlier records is not verified.
- **Effect on earlier entries.** Entries that say `uncommitted on 6bb5e4e` are
  not rewritten. For acquisition runs the code state they describe is `44ad351`;
  for the other modules it is `44ad351` only as far as the files were not edited
  after those runs, which no record establishes.
- **Code state.** `44ad351`.

## R-015 · 2026-10-29 · Reference identification and coordinate mapping protocol

- **Procedure.** Inspected the existing provenance records, data modules, and
  the first `original_header` per class of all 64 canonical collections
  (read-only), to design how references are identified and sequences located.
  Official conventions were checked against the UCSC coordinate blog, the SAM
  specification, and the Bowtie 2 manual.
- **Decision.** Location and label validation are separate. Declared
  coordinates are verified before any search. Every accepted candidate locus is
  kept, and records carry one of five statuses. Normalized coordinates are
  0-based half-open with named conversion rules. No mapping was run.
- **Data version.** `can-v1` (SHA-256 `eb5460a0…`).
- **Records.** `specs/reference_coordinate_mapping_protocol.md`,
  `docs/coordinate_mapping_gap_inventory.md`.
- **Not done.** The coordinate conventions of the Bhandari, Promotech 40-nt,
  and GraphPro headers are hypotheses until their pilots run. No aligner is
  installed.
- **Code state.** Documentation only; uncommitted on `aa7d437`.

## R-016 · 2026-10-29 · Length deviations, strand balance, and length-exclusion rule

- **Procedure.** Read-only counts over the canonical tables: lengths, strands,
  and exact reverse-complement pairs of Bhandari Human and Yeast positives, and
  non-100-nt CDBProm negatives. Reviewed how existing builders handle
  off-length records.
- **Results.** 33 short Bhandari windows, all on alternate contigs or at
  chromosome ends (F-031, F-032). Strands are balanced, with 1 and 3
  reverse-complement pairs (F-033). 51 CDBProm negatives are exactly 99 nt
  (F-034, F-035). Legacy builders drop or truncate off-length records without a
  per-reason count (F-036).
- **Decision.** Off-length records are excluded, never reshaped. The rule is
  declared per dataset, from the release declaration rather than the modal
  length, and every exclusion is counted with its reason
  (`specs/dataset_integrity_audit.md`, "Length exclusion"). Existing build
  outputs are not changed; the rule applies to new build versions.
- **Data version.** `can-v1` (SHA-256 `eb5460a0…`).
- **Code state.** Documentation only; scratch scripts outside the repository;
  uncommitted on `aa7d437`.

## R-017 · 2026-10-29 · Complete scan of length deviations

- **Procedure.** Read-only scan of `length_matches_expected` in all 64
  canonical collections. The off-length records not covered by R-016 were
  inspected by header, and the six short Bhandari random-genomic negatives were
  compared with whole scaffolds read from the acquired `hg38.2bit` through
  `capsprom.data.twobit.TwoBitGenome`.
- **Problem.** The known-deviation table written in R-016 came from a partial
  analysis (Bhandari Human and Yeast, CDBProm) and omitted 13 records in three
  collections.
- **Results.** 98 off-length records in 16 collections (F-040). The added
  cases: 5 nominal-Plant windows truncated on mm10 unplaced contigs (F-037);
  6 random-genomic negatives that equal entire hg38 unplaced scaffolds (F-038);
  2 GraphPro *L. interrogans* records of 82 nt with no documented reason
  (F-039).
- **Decision.** Completed the table in `specs/dataset_integrity_audit.md` and
  marked it as the complete list for `can-v1`. The rule itself is unchanged.
- **Data version.** `can-v1` (SHA-256 `eb5460a0…`); `hg38.2bit` from `acq-v1`.
- **Code state.** Scratch scripts outside the repository, on `af28ec9`.
