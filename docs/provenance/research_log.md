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

## R-018 · 2026-10-29 · Generated deviation record, Bhandari range pilot, CDBProm drop check

- **Procedure.**
  1. Added `record_provenance.py length-deviations`, which writes
     `length_deviations.json` (record IDs and lengths only), and a test that
     fails when the spec's known-deviation table and the record disagree in
     either direction. The table's first column now lists collection IDs.
  2. Ran the B1 pilot of `specs/reference_coordinate_mapping_protocol.md` on
     Bhandari: the first 20 full-length records per strand by `sequence_sha1`
     rank in Human, Yeast, and nominal Plant, plus all 38 short records,
     extracted from the acquired UCSC 2bit files under both the 1-based closed
     and 0-based half-open readings.
  3. Compared the record counts of the regenerated-v3 CDBProm negative FASTA
     files with the canonical negatives.
- **Results.** 98 deviations in 16 collections, equal to the spec table. The
  1-based closed reading reproduces all 158 records, and the other reading none
  (F-041). The name coordinate is the start of the upstream region (F-042);
  TSS at index 700 remains a hypothesis (F-043). Short windows lost only
  upstream bases (F-044). Nominal-Plant pilot records come from mm10 (F-045).
  The v3 build dropped exactly the 51 short CDBProm negatives (F-046).
- **Data version.** `can-v1` (SHA-256 `eb5460a0…`); 2bit files from `acq-v1`.
- **Records.** `manifests/provenance/source_acquisition_v1/length_deviations.json`,
  `bhandari_range_pilot.json`.
- **Code state.** Deviation record: uncommitted on `bed443f`, committed with
  this entry. Pilot: scratch script outside the repository, SHA-256
  `1b7892d707ac9c40…`.

## R-019 · 2026-10-29 · Reference acquisition v1 and Bhandari TSS comparison

- **Procedure.**
  1. Created `configs/reference_acquisition_v1.yaml` (SHA-256 `cd6e3ac6…`)
     for the UCSC RefSeq transcript tables (genePred, with their SQL schema)
     of hg38 `ncbiRefSeqCurated`, sacCer3 `ncbiRefSeq`, and mm10
     `ncbiRefSeq`, the tracks named in the Bhandari headers. Ran
     `PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --config configs/reference_acquisition_v1.yaml --execute`;
     6 files downloaded and recorded, no declared digest (trust on first use).
     `source_acquisition_v1` was not changed.
  2. For every Bhandari Human, Yeast, and nominal-Plant record, derived the
     window TSS from the name coordinate (F-042) and compared it with the
     transcript start of the same `accession.version` on the same chromosome
     and strand.
- **Results.** Where the version is annotated, the TSS equals the transcript
  start in all Yeast records and in all but 4 Human and 2 nominal-Plant ones
  (F-047). Most Human and nominal-Plant records name versions that the current
  tables no longer hold (F-048), so their TSS stays unverified (F-050). Table
  dates in F-049; mitochondrial protein accessions in F-051.
- **Data version.** `can-v1` (SHA-256 `eb5460a0…`); `ref-acq-v1` (SHA-256
  `cd6e3ac6…`).
- **Records.** `manifests/provenance/reference_acquisition_v1/acquisition_manifest.json`,
  `manifests/provenance/source_acquisition_v1/bhandari_tss_refseq_comparison.json`.
- **Code state.** Acquisition with the committed `capsprom.data.acquisition`
  at `42628b8`; comparison by a scratch script outside the repository,
  SHA-256 `ac75e333dba3f5b7…`.

## R-020 · 2026-10-29 · Dated NCBI RefSeq releases and Bhandari TSS status

- **Procedure.**
  1. Created `configs/reference_acquisition_v2.yaml` (SHA-256 `5faffcbc…`),
     choosing by a date rule fixed before comparison: the latest NCBI annotation
     release of each declared assembly before the 2021-01-21 Drive archive
     (Human 109.20201120, mouse GRCm38 108.20200622). Acquired with published
     MD5 digests.
  2. The comparison refuted the rule (F-052). As an identification step, scanned
     every GRCh38 release 109.* listed on the NCBI FTP and both GRCm38 releases,
     downloaded to a scratch directory with MD5 checked, counting exact
     `accession.version` matches only (F-053).
  3. Created `configs/reference_acquisition_v3.yaml` (SHA-256 `a64e93bb…`) for
     the releases the scan identified (Human 109, mouse 108) and acquired them.
  4. Compared the window TSS with every acquired source and consolidated one
     status per record (F-055, F-056).
- **Decision.** The failed date rule stays recorded in `ref-acq-v2`; it is not
  edited. Release identification by version matches uses source metadata only.
  All candidates are reported.
- **Results.** TSS at index 700 holds for 58,816 of 61,546 Human records,
  46,817 of 106,520 nominal-Plant records, and all 6,125 Yeast records.
  6 records contradict it and 20 name a version found only at another locus.
  The rest are untestable with the releases available.
- **Data version.** `can-v1`; `ref-acq-v1`, `ref-acq-v2`, `ref-acq-v3`.
- **Records.** `manifests/provenance/reference_acquisition_v2/`, `…_v3/`;
  `manifests/provenance/source_acquisition_v1/bhandari_refseq_release_scan.json`,
  `bhandari_tss_ncbi_ar_dated_rule.json`, `bhandari_tss_ncbi_ar_identified.json`,
  `bhandari_tss_status.json`.
- **Code state.** Acquisition with the committed `capsprom.data.acquisition` at
  `c6bd1e0`. Scratch scripts outside the repository: release comparison
  `f0bf9f4c…`, version scan `2455b6ab…`, consolidation `0caa9cf5…`.

## R-021 · 2026-10-29 · Domain-specific sequence windows

- **Decision (user).** Eukaryotic datasets use 251 nt windows (-200..+50) and
  prokaryotic datasets 81 nt windows (-60..+20). Archaea count as prokaryotes.
- **Procedure.** Read the released lengths of every `can-v1` collection from
  `prov/canonical_manifest.json` and listed where code and specs fix 81 nt.
  Wrote `specs/sequence_window_policy.md` with the windows, the allowed
  derivations, the non-promoter rule, and the feasibility of each collection.
  Updated the dataset contract (`specs/project_spec.md`) and the 81 nt
  passages of the feature, GraphPro reconstruction, CapsProm, and MVP specs.
  Wrote `docs/legacy_data_archive_plan.md`; nothing was archived or deleted.
- **Results.** CNNProm eukaryotes are 251 nt natively; Bhandari (TSS index 700)
  and EPD 128 (index 499) can be cropped; GraphPro Human/Mouse, BDGP, CDBProm,
  and Promotech need further evidence. The regenerated-v3 builds crop CNNProm
  eukaryotes from 251 to 81 nt (F-057).
- **Data version.** `can-v1`; no new data.
- **Code state.** Documentation only, uncommitted on `d681bb6`.
- **Findings.** F-057.

## R-022 · 2026-10-29 · Data conditions and the Bhandari nominal Plant file

- **Procedure.**
  1. Defined two data conditions (released-filtered `orig`, reconstructed
     `recon`), the order in which an intervention is classed as
     reconstruction, metadata correction, or filtering, and the separate
     identifiers and ledgers each condition needs
     (`specs/dataset_condition_policy.md`).
  2. Read arXiv:2105.07659 v1 (PDF SHA-256
     `0a60e28b1a72d7429b347cac5a14b1d49cf9218aff1c5fc7d87a360dbabcb35c`,
     fetched 2026-10-29) for the plant-set description and the reported
     results (F-059). The PeerJ article page returned HTTP 403 and was not
     read.
  3. Read the acquired repository file `bhandari-github/Update` (F-060).
  4. Counted header chromosome names and mean GC content in the canonical
     Bhandari tables (F-058).
- **Decision.** `bhandari-nominal-plant` keeps its collection ID and file name.
  It may be used in the `orig` condition only with the explicit metadata
  correction *Mus musculus* `mm10`, and in the `recon` condition only as a
  mouse reconstruction; never as a plant set. Its published-protocol replay is
  `not_comparable` to the published *A. thaliana* results. Justification and
  pending evidence: `docs/bhandari_nominal_plant_assessment.md`. No dataset,
  partition, config, or gate was changed, and no training ran.
- **Data version.** `acq-v1`, `can-v1`.
- **Records.** `docs/bhandari_nominal_plant_assessment.md`.
- **Code state.** Documentation on `d681bb6`. Counts by a scratch script
  outside the repository, SHA-256 `5abbc8efc4afc03c…`, run with the project
  virtual environment.
- **Findings.** F-058 to F-063.

## R-023 · 2026-10-29 · Bhandari repository history, *A. thaliana* identification, full recreation

- **Procedure.**
  1. Listed the commit history of `nikitabhandari-dl/Dataset` through the
     GitHub API (P-2). Found three CSVs, deleted on 2021-01-21 (F-064).
  2. Created `configs/bhandari_history_acquisition_v1.yaml` for commit
     `c1c97ee`, the last tree holding them, and acquired 5 files (blob SHA-1
     verified; log `data/acquired/bhandari_history_acquisition_v1/logs/run_20261029T230848Z.log`).
  3. Checked UCSC for `araTha1` (P-3): HTTP 404 and API error (F-069); the
     Internet Archive CDX service was offline.
  4. Acquired the UCSC GenArk TAIR10.1 reference. `ref-acq-v4` failed on a
     stale hub digest for `chromAlias.txt`; `ref-acq-v5` was generated with an
     error (its `chrom.sizes` entry took the assembly-report URL) and is
     invalid; `ref-acq-v6` succeeded with 4 files. v4 and v5 are kept unchanged
     as records.
  5. Added `record_provenance.py bhandari-history` (history comparison, exact
     genome location, TSS check) and `bhandari-recreation` (P-1: every Drive
     Human, Yeast, and nominal-Plant record against its header coordinates),
     with tests on synthetic genomes. Ran both in one persistent `nohup setsid`
     job; log `data/interim/bhandari_history/logs/run_20261029T232216Z.log`.
- **Decision.** The historical repository file is a released file of the
  study, used unchanged under its own acquisition and never merged with the
  Drive release; the Drive file keeps its role as a mouse dataset. The
  notebook's first-N selection, which contradicts the text, is a declared
  assumption of any published-protocol replay.
- **Results.** F-064 to F-072. P-1: see the addendum below (F-073).
- **Data version.** `acq-v1`, `can-v1`, `bh-hist-v1`
  (`configs/bhandari_history_acquisition_v1.yaml`), `ref-acq-v6`.
- **Records.** `manifests/provenance/bhandari_history_acquisition_v1/history_comparison.json`,
  `manifests/provenance/source_acquisition_v1/bhandari_recreation.json`,
  acquisition manifests under `manifests/provenance/` (snapshots).
- **Code state.** Uncommitted on `3cc3618`; module SHA-256
  `f21bc01445c1bcbb…` (`provenance.py`) and `d10c2b4d79e8b574…`
  (`record_provenance.py`), as logged by the run.
- **Addendum (P-1).** The job finished at 2026-10-29T23:29:20Z with exit code
  0. Every Drive record is recreated exactly from its coordinates: Human
  61,546, Yeast 6,125, nominal Plant 106,520 (F-073).

## R-024 · 2026-10-29 · Test of F-067 against the earlier mitochondrial genome

- **Procedure.** Identified the earlier *A. thaliana* mitochondrial sequence
  with NCBI esummary (Y08501.2, 366,924 bp; NC_001284.2 suppressed, replaced by
  NC_037304.1). Acquired it under `configs/reference_acquisition_v7.yaml`
  (efetch FASTA, no upstream digest). Searched the 77 unlocated records
  (F-066) exactly on both strands, treating the genome as circular; as a
  control, searched the 36 records located on NC_037304.1.
- **Results.** 77/77 found exactly (26 `+`, 51 `-`); control 36/36 (F-074).
- **Data version.** `bh-hist-v1`, `ref-acq-v6`, `ref-acq-v7`.
- **Code state.** Scratch script outside the repository, SHA-256
  `7e5af12907e2335f…`, run with the project environment on `3cc3618`.
- **Findings.** F-074 (supersedes F-067).

## R-025 · 2026-10-29 · P-6 canonicalization of the historical files; *A. thaliana* TSS classification

- **Procedure (historical condition).**
  1. Added the `label_csv` input format to `capsprom.data.canonical_sources`:
     two-field `label,sequence` rows in which every label must equal the
     declared `source_label` (a header row or another class fails the build).
  2. Created `configs/bhandari_history_canonicalization_v1.yaml` for the three
     historical CSVs of `bh-hist-v1` and ran
     `scripts/canonicalize_sources.py --config configs/bhandari_history_canonicalization_v1.yaml`:
     3 built, all `pass`.
  3. Added `record_provenance.py bhandari-history-canonical`
     (`verify_label_csv_canonical`), which rebuilds each source file from its
     canonical rows and checks IDs, hashes, labels, and the comparison with the
     Drive tables (F-075).
- **Procedure (reconstructed condition, separate artifacts).**
  4. Created `configs/reference_acquisition_v8.yaml` (NCBI GCF_000001735.3 and
     .4 GFF) and `configs/reference_acquisition_v9.yaml` (Ensembl Plants 31
     TAIR10 GTF; BSD sum checked by hand against Ensembl `CHECKSUMS`).
  5. Added `record_provenance.py arabidopsis-tss` (`classify_window_tss`): per
     record, signed distance from the window TSS to the nearest annotated
     transcript 5' end in each of four annotations (F-076, F-077).
- **Incident.** While creating step 4, this session first wrote its config to
  `configs/reference_acquisition_v7.yaml`, which another session had already
  created and used (R-024). The other session's acquisition and manifest were
  not modified (the run against the wrong config failed before writing), but
  its untracked config text was overwritten. It was asked to restore it; until
  then `ref-acq-v7` has a manifest without its config.
- **Decision.** The canonical tables keep every historical record, sequence, and
  label as released; the TAIR10 coordinates and TSS classes are evidence of
  the reconstructed condition and are stored apart from them. No window is
  judged incorrect from a mismatch with a later annotation.
- **Data version.** `bh-hist-v1`; `bh-can-v1`
  (`configs/bhandari_history_canonicalization_v1.yaml`); `ref-acq-v6`, `v8`,
  `v9`.
- **Records.** `manifests/provenance/bhandari_history_canonicalization_v1/`
  (`canonical_manifest.json`, `canonical_verification.json`),
  `manifests/provenance/bhandari_arabidopsis_tss_v1/tss_classification.json`,
  acquisition manifest snapshots for `ref-acq-v8` and `v9`.
- **Code state.** Uncommitted on `3cc3618`; SHA-256 `54e7035d6269cc7e…` (`provenance.py`), `00ee52d9832d4500…` (`canonical_sources.py`), `4c9f914f8f7b2b62…` (`record_provenance.py`).
- **Findings.** F-075 to F-079.
- **Addendum (incident).** The session that wrote `ref-acq-v7` restored its
  config byte for byte; its SHA-256 equals the manifest's `config_sha256`
  (`d9d38d578e7c5c0c…`), checked here with `sha256sum`.

## R-026 · 2026-10-29 · Review of `Code.ipynb` and duplicate structure before the replay contract

- **Commit.** The data-condition and P-6 work was committed as `6e4922c`;
  files of other sessions (substitution sensitivity, pipeline figure) were left
  unstaged.
- **Review.** Every cell of `Code.ipynb` was read; defects and their effect on
  the published numbers are in F-080 and F-083. The legacy code is treated as a
  description of the published procedure, not as a correct implementation.
- **Counts.** Exact duplicates under the notebook's filters (F-081) and genomic
  overlap of the unique windows (F-082) were computed from the canonical
  collection and the `bhandari-history` loci with scratch scripts; nothing was
  written under `data/` and no dataset or partition was built.
- **Decisions by the researcher.** Random selection (not first-N) in the
  project's experiments; the current software stack for any replay, including
  legacy code. Recorded in `docs/bhandari_nominal_plant_assessment.md` §5.
- **Findings.** F-080 to F-083.
- **Addendum (2026-10-30, decisions by the researcher).** 10 seeds; 35,000
  records per class in `orig-pub`, all unique records in `orig-common` and
  cross-source work; a value is reproduced when it lies within the 10-seed
  range; leakage is measured at the length the model sees, after cropping.

## R-027 · 2026-10-30 · Alignment audit of train/test overlap; CNNProm negative construction

- **Question.** Does dependence beyond exact identity cross the regenerated-v3
  train/test split? Raised while deciding partition and inference policy.
- **Tool.** MMseqs2 static release `mmseqs-linux-avx2.tar.gz` (SHA-256
  `bd9b0234da5949ad…`, version `8cc5ce367b5638c4…`), downloaded with the
  researcher's authorisation from the official GitHub release and run in WSL
  Ubuntu 24.04. Not installed in the project environment.
- **Procedure.** For all 26 v3 pairs: `easy-search` test vs train,
  `--search-type 3 --strand 2 -k 11 -c 0.8 --cov-mode 0 --max-seqs 1000`, at
  `--min-seq-id` 0.80/0.90/0.95, plus `easy-cluster` of train+test. Scratch
  script SHA-256 `d01d6960d95b70b4…`; results JSON `a8671d48f6eb2523…`. Neither
  is kept in the repository. Follow-up scratch scripts mapped hits to raw
  CNNProm headers, coordinates, and clones, and counted Alu consensus 15-mers.
- **Corrections during the run.** Default k-mer size exceeded WSL memory; `-k 11`
  and `--split-memory-limit 3G` were used. `--search-type` is not accepted
  by `easy-cluster`.
- **Scope note.** 81-nt v3 windows, not the 251-nt eukaryotic window of the
  sequence window policy. Exploratory; nothing written under `data/`.
- **Findings.** F-084 to F-089. Thesis discussion:
  `docs/cnnprom_overlap_leakage_finding.md`. Pipeline stage defined in
  `specs/homology_grouping_protocol.md` and `configs/homology_grouping_v1.yaml`
  (design, not executed).
- **Addendum (2026-10-30, Hamming recall check).** Exact Hamming neighbours
  (≤8 and ≤16) were recomputed with the pigeonhole scheme of
  `near_duplicate_audit.py` and compared with the MMseqs2 hits; `-k 9` was
  run on the three pairs with misses. Finding F-090.

## R-028 · 2026-10-31 · Bacterial reference acquisition and exact-search pilot

- **Scope (researcher's choice).** Eligible bacterial collections first: 11
  CDBProm and CNNProm *E. coli* and *B. subtilis*. NCBI downloads authorised by
  the researcher.
- **Acquisition.** `configs/reference_acquisition_v10.yaml` (FASTA, GFF3,
  assembly report per assembly; MD5 from each directory's `md5checksums.txt`)
  run with `scripts/acquire_sources.py --execute`: 39/39 files verified.
  Manifest snapshot in `manifests/provenance/reference_acquisition_v10/`.
- **Code.** `src/capsprom/data/exact_mapping.py` (FASTA reader, complete
  both-strand exact matcher with overlapping and palindromic hits, round-trip
  extraction) with synthetic tests in `tests/test_exact_mapping.py`. IUPAC
  compatibility, record/locus persistence, manifest and resumption (plan steps
  3–4) are not implemented yet.
- **Pilot.** Scratch script (SHA-256 `5c96dbe6bf5522bf…`) mapped every canonical
  record of the 13 collections; summary SHA-256 `ab4a311a2daf5fb2…`. Outputs
  stayed in the scratch directory; nothing was written under `data/coordinates/`.
- **Findings.** F-091 to F-095.
- **Next.** Persisted mapping v1 (record and locus tables, manifest), then
  NC_000913.2 and RegulonDB 9.0 to test F-095, and B3 characterisation of the
  CDBProm unmapped records.

## R-029 · 2026-10-31 · Strain tests, NC_000913.2, and persisted mapping v1

- **Acquisition.** `configs/reference_acquisition_v11.yaml` (config SHA-256
  `1cd5ed86b6cca7e7…`): six earlier or alternative strain assemblies and
  NC_000913.2 via efetch; 7/7 files verified. Manifest snapshot SHA-256
  `1a5956f8eebe981b…`.
- **Tests.** Exploratory scratch scripts. Unmapped CDBProm records were first
  aligned with MMseqs2 to their `v10` assembly (most are full length with ≤5
  differences), then searched exactly in the `v11` assemblies. All CNNProm
  *E. coli* records were mapped to NC_000913.2.
- **Code.** `exact_mapping.py` gains IUPAC-compatible reference matching
  (H. pylori and P. aeruginosa `v10` assemblies contain 42 and 60 non-ACGT
  bases). New `coordinate_mapping.py` and `scripts/map_coordinates.py` write
  record and locus tables, a manifest after each shard, and `runs[]`
  (failed runs included since the fix). `/data/coordinates/` was added to
  `.gitignore`, as the protocol requires.
- **Run.** `scripts/map_coordinates.py --config configs/reference_coordinate_mapping_v1.yaml`
  in two runs (the first stopped at non-ACGT records); outputs under
  `data/coordinates/reference_coordinate_mapping_v1/`, manifest snapshot
  committed.
- **Findings.** F-096 to F-100.
- **Open decision.** Whether a `v2` mapping uses the earlier sequences of F-096
  and NC_000913.2 as the references of record.
- **Addendum (2026-10-31, mapping v2, researcher's decision).**
  `configs/reference_coordinate_mapping_v2.yaml` re-references five CDBProm
  collections to the F-096 sequences and CNNProm *E. coli* to NC_000913.2, with
  assembly evidence `verified` conditional on no unmapped strict-DNA record.
  The runner gained an explicit `reference_file` for non-assembly FASTA. One
  completed run, 13/13 shards, 0 unmapped. Finding F-101. v1 stays as recorded.
  Still open for acceptance: B1, B3, the sample audit, and the R-011 replacement
  evidence of Anabaena, S. Typhimurium and S. coelicolor.

## R-030 · 2026-11-01 · CDBProm declared accessions

- **Procedure.** Read Table 1 of the CDBProm publication (doi:10.1093/nargab/lqae018)
  and queried NCBI esummary for CP034058.1, CP133487.1, AL939104.1, AL645882.2,
  NC_003888.3 and CP002927.1. Metadata only; nothing downloaded or mapped.
- **Findings.** F-102 to F-104. This closes the "publication's accession list
  not checked" item of R-011.
- **Implication.** A mapping v3 could set *S. coelicolor* to `declared` (same
  genome as the declared segment) and *Anabaena* and S. Typhimurium to
  `conflicting`. Under the current status rule, *S. coelicolor* records would
  become `verified`; the other two stay `inconsistent` with an added reason.
  Done in R-031.

## R-031 · 2026-11-01 · Coordinate mapping v3

- **Procedure.** Created `configs/reference_coordinate_mapping_v3.yaml` from v2
  with the R-030 evidence levels (*S. coelicolor* `declared`; *Anabaena* and
  S. Typhimurium `conflicting`). `record_status` now gives `conflicting`
  evidence the reason `assembly_conflicting` instead of `assembly_mismatch`.
  Ran `scripts/map_coordinates.py` in WSL; manifest snapshot in
  `manifests/provenance/reference_coordinate_mapping_v3/`. `make check`: 222 passed.
- **Findings.** F-105. v1 and v2 stay as recorded.
- **Still open.** B1, B3 and the stratified sample audit.

## R-032 · 2026-11-01 · Overlap of iPro-MP data with the eligible test sets

- **Question.** Can iPro-MP's released weights or data be used against the 18
  eligible test sets without leakage? Raised while defining baseline fidelity
  and fairness.
- **Procedure.** Every strict-DNA iPro-MP record of `source_canonicalization_v1`
  (train and test, 23 species) against each eligible regenerated-v3 test CSV,
  both strands: exact identity, Hamming ≤8 (pigeonhole, nine 9-nt blocks), and
  any shared exact 40-nt substring. Python 3 in WSL; scratch script SHA-256
  `91e2af42b89f33d6…`, results JSON `dcbd9275441150bf…`, not kept in the
  repository. MMseqs2 was not used: the R-027 binary was not retained.
- **Findings.** F-106, F-107.
- **Addendum (2026-11-01, MMseqs2 and GUE).** With the researcher's
  authorisation, re-downloaded the MMseqs2 static release (SHA-256
  `bd9b0234da5949ad…`, identical to R-027) and the official GUE archive from
  the DNABERT-2 README Google Drive link (`GUE.zip`, SHA-256
  `581ba5a69843769f…`), both in WSL `~/dl/`, outside the repository. `easy-search`
  of the 30,121 eligible test records against 321,850 iPro-MP records
  (`-c 0.8 --cov-mode 0`) and against 118,392 GUE `prom_300_all` and
  `prom_core_all` records (`-c 0.8 --cov-mode 2`, since GUE windows are 300 and
  70 nt), with `--search-type 3 --strand 2 -k 11 --min-seq-id 0.8`. Scratch
  script `mm_overlap.sh`; hit tables SHA-256 `01dab3ecd4749f94…` (iPro-MP) and
  `635df7d68e420d66…` (GUE). Findings F-108, F-109; hypotheses F-110 to
  F-113. Thesis discussion: `docs/external_resource_leakage_finding.md`.

## R-033 · 2026-11-01 · Alignment-based dependence between eligible datasets

- **Question.** Does the exact-overlap rule of
  `configs/dataset_dependency_manifest_v2.yaml` miss dependence between
  datasets? Raised by F-108, which showed shared promoters across sources.
- **Procedure.** All train and test records of the 18 eligible v3 datasets in
  one FASTA, MMseqs2 `easy-search` all-vs-all with the R-032 tool and F-084
  settings (`-c 0.8 --cov-mode 0 --min-seq-id 0.8`); same-dataset hits dropped.
  Scratch script `mm_cross.sh`; hit table SHA-256 `dda11bbfbca06e11…`, not kept.
- **Findings.** F-114.
- **Implication.** A v3 manifest would join *K. pneumoniae* to
  `enteric-cross-source` and CDBProm *B. amyloliquefaciens* to CNNProm
  *B. subtilis*, reducing 14 clusters to 12. Not done: the cluster rule is a
  statistical-protocol decision for the researcher.
- **Addendum (2026-11-01).** At the researcher's request, created
  `configs/dataset_dependency_manifest_v3.yaml` with 12 clusters (rule: exact
  or alignment overlap, more than 10 records per pair). v2 is unchanged and
  still bound by `evaluation_protocol_v3.yaml`. Figure:
  `docs/thesis/figures/dependency_clusters.{py,svg,pdf,png}`. Added
  `su2025ipro` to `references.bib` from PubMed 41083998
  (doi:10.1186/s13059-025-03819-9).

## R-034 · 2026-11-01 · Eligibility documentation and four-study figure

- **Question.** Which criteria actually decide dataset eligibility, in which
  data condition, and which of them are verified, defined only, or pending?
- **Procedure.** Consolidated the integrity spec, the condition policy, the
  eligibility manifest, the source label semantics audit, the GraphPro
  reconstruction reports, the homology grouping protocol, and the builder code
  (`dataset_builders.py`) into `docs/dataset_eligibility.md`. No rule was added
  and no data changed.
- **Gaps recorded.** Condition labels are not yet applied to any build; there
  is no recorded accession check for the 18 eligible datasets; the length
  exclusion and similarity grouping are defined but not applied; the CDBProm
  TSS index is unverified (F-018); reconstruction gates R1 and R7 are open.
- **Figure.** `docs/thesis/figures/dependency_clusters_studies.{py,svg,pdf,png}`
  shows the eligible clusters, the eight excluded GraphPro datasets, and the
  iPro-MP and GUE overlap with the eligible test sets (F-108, F-109, F-114).

## R-035 · 2026-11-01 · TSS classes of GraphPro bacterial positives and control exclusion

- **Question.** Which dRNA-seq TSS classes do the Promotech positives contain,
  and does the control exclusion cover every known TSS?
- **Procedure.** `scripts/inventory_graphpro_tss_classes.py` joins every row
  of the five acquired Promotech BEDs to its primary table (one-based position
  = BED start + 1, same strand) and counts classes; it checks the existing
  reconstructed-v2 controls against the complete primary tables with a 100-nt
  margin. Output `outputs/reports/graphpro_tss_class_inventory_v1/summary.json`
  (SHA-256 `878c8933ff9e5ea2b9b7752ec0b4beb17abaa71c09f0061bd15ed3b092d615db`).
  Bacillus and Rhodobacter were not inventoried (no primary table). No model
  outcome was used and no dataset changed.
- **Findings.** F-115, F-116, F-117.
- **Implication.** The v2 *L. interrogans* controls are not valid genomic
  non-promoter controls under the specification and must not be reused; v2 is
  kept as provenance. `reconstruct_genomic_controls` now requires an explicit
  exclusion set, refuses one that omits a positive, and re-verifies every
  accepted control (`find_control_exclusion_violations`); rejected candidates
  are replaced by the next permutation candidate, as before. The class policy
  is recorded in `specs/graphpro_dataset_reconstruction.md`; the choice of
  positive classes per organism (default P+S) awaits the researcher's
  confirmation before a successor build contract.

## R-036 · 2026-11-01 · Control exclusion radius for the 251-nt eukaryotic window

- **Question.** Is the 100-nt TSS exclusion radius sufficient for genomic
  controls once eukaryotic windows are 251 nt (-200..+50, R-021)?
- **Finding.** No. The exclusion is symmetric and strand-agnostic. A control
  that starts 101 nt from a TSS can share up to 100 nt with that TSS's
  -200..-101 promoter region, so the same sequence would carry opposite
  labels. At 81 nt (U = 60) the 100-nt radius is sufficient.
- **Decision (project owner).** Redefine the radius per domain as
  `r = U + m`, where `U` is the upstream length of the domain window and `m`
  a margin for TSS imprecision: 40 nt for prokaryotes (r = 100, unchanged)
  and 50 nt for eukaryotes (r = 250), wider because broad eukaryotic
  promoters spread initiation around the representative TSS. Recorded in
  `specs/graphpro_dataset_reconstruction.md`. Existing contracts are
  immutable and remain valid for their 81-nt windows; a 251-nt Human/Mouse
  successor must freeze `r = 250`. No data or model outcome was used.

## R-037 · 2026-11-01 · Resumption of the reconstructed GraphPro line

- **Decision (project owner).** Reverse the deferral of
  `configs/graphpro_deferral_policy_v1.yaml` for the reconstructed condition.
  The successor `configs/graphpro_deferral_policy_v2.yaml` opens audit,
  reconstruction, control, and split gates; training and confirmatory use stay
  closed until per-organism eligibility is approved.
- **Scope.** Cje, Cpne, Lint, Human, Mouse; Bacillus (no coordinate-level
  primary supplement yet) and Rhodobacter (GSE117537 has 4,045 rows, not
  5,374) resume with explicit blockers. E. coli is pending: its TSS rows
  belong to plasmid pAA (`NC_018666.1`, 248 unique TSS); the owner decides
  between exclusion and an exploratory pAA identity.
- **Requirements.** Homology grouping v1 with genomic-overlap edges; the
  bacterial split v1 (Hamming ≤ 8) is not reused. Human/Mouse are rebuilt at
  -200..+50 (251 nt) with r = 250 (R-036). Released GraphPro files stay
  exploratory provenance; no artifact is deleted or relabeled.

## R-038 · 2026-11-02 · CDS-derived negative-control contract

- **Decision (project owner).** Freeze the design of the `cds_derived`
  condition in `specs/cds_negative_control_protocol.md` and
  `configs/cds_negative_control_v1.yaml`. Scope: prokaryotic reconstructed
  datasets only (Cje, Cpne, Lint; Bacillus and Rhodobacter after their source
  gates). RefSeq GFF of the TSS assembly; eligible CDS are at least 201 nt,
  non-pseudo, exact, single-segment. Controls are 81 nt on the CDS sense
  strand, same replicon, uniform frame cycle 0/1/2, at least 60 nt from start
  and stop, outside 100 nt of any TSS on either strand, not touching another
  CDS or RNA, GC within four bases, paired 1:1. The TSS exclusion set is the
  complete primary table, all classes (R-035); positives, classes, and groups
  come from the genomic successor build, never from reconstructed v2.
- **Sampling and failures.** Seed 20261102, 100,000 random probes, then a
  deterministic exhaustive scan. A positive without a viable control leaves
  the CDS panel only.
- **Inference.** Within-panel paired bootstrap. Whenever the CDS and genomic
  panels hold different positives, cross-panel comparison uses only their
  intersection, fixed before model evaluation.
- No data, reference, or model outcome was used; all execution gates are
  false.

## R-039 · 2026-11-02 · Positive TSS classes of the reconstructed bacteria

- **Decision (project owner).** A bacterial positive is a TSS whose class set
  contains primary (P) or secondary (S), whatever other classes it holds.
  Positives come from the verified primary table, not only the Promotech BED.
  *C. jejuni*: 855 of 1,905 (internal-, antisense-, and orphan-only TSSs
  excluded). *C. pneumoniae*: 571 (530 P plus 41 S omitted by Promotech).
  *L. interrogans*: 2,791, primary at 30 °C or 37 °C. Bacillus and
  Rhodobacter wait for their primary tables; pAA waits for its identity
  decision. Counts from the R-035 inventory (summary SHA-256
  `878c8933ff9e5ea2b9b7752ec0b4beb17abaa71c09f0061bd15ed3b092d615db`).
- **Consequence.** Every successor build contract declares these sets before
  any build; full class sets stay in the pair ledgers for stratification. An
  all-classes variant is not predeclared now (owner decision); it may be
  added as a separate identity only before any confirmatory result. No data
  or model outcome was used.

## R-040 · 2026-11-02 · Exclusion of GraphPro E. coli and pAA

- **Decision (project owner).** Exclude GraphPro E. coli from the
  reconstructed line and build no pAA (`NC_018666.1`) identity, exploratory or
  confirmatory. Reasons: the Promotech rows are the 248 TSSs of plasmid pAA of
  *E. coli* O104:H4, not of the E. coli genome; only 51 are gene-associated
  (P or S, R-039), too few for a test panel. Space for controls was not the
  reason (F-117).
- **Records.** `configs/graphpro_deferral_policy_v2.yaml` marks `ecol` as
  excluded. The nominal MG1655 reconstruction, the pAA source audit, and the
  released files remain provenance; nothing is deleted or relabeled.

## R-041 · 2026-11-02 · CDS annotation acquisition and feasibility inventory

- **Decision (project owner).** Open reference acquisition and a model-free
  feasibility inventory for the CDS-derived condition. Successor contract
  `configs/cds_negative_control_v2.yaml` changes only those two gates;
  generation, split, training, and test gates stay false.
- **Acquisition.** `configs/reference_acquisition_v12.yaml`: RefSeq GFF3,
  genomic FASTA, and assembly report of GCF_000009085.1 (*C. jejuni*,
  NC_002163.1), GCF_000008745.1 (*C. pneumoniae*, NC_000922.1; annotation
  RS_2024_11_20), and GCF_900236655.1 (*L. interrogans*, NZ_LT962963.1;
  annotation RS_2026_02_15). On 2026-11-02 NCBI esummary reported each
  accession.version live and not replaced. `scripts/acquire_sources.py
  --execute`: 9/9 files verified against the NCBI MD5 digests. Manifest
  snapshot in `manifests/provenance/reference_acquisition_v12/`. Each RefSeq
  sequence is byte-identical to the Promotech FASTA that carries the TSS
  coordinates, so no coordinate conversion is needed.
- **Code.** `src/capsprom/data/cds_controls.py` (GFF reader, CDS eligibility
  with pseudo-by-parent and Note frameshift rules, admissible-window
  enumeration with end margins, both-strand TSS radius, and CDS/RNA overlap)
  with synthetic tests in `tests/test_cds_controls.py`;
  `scripts/inventory_cds_control_feasibility.py`. Output
  `outputs/reports/cds_control_feasibility_v1/summary.json` (SHA-256
  `5c299b3839fac8a0e573534130719878244127cf389a7de03679f28e7dabfde7`). No
  control was sampled; exact-identity and selected-control exclusions are not
  applied by an inventory.
- **Findings.** F-118, F-119.
- **Open decision.** The *L. interrogans* positive set of R-039 (2,791) rests
  on the F-115 description, which F-118 corrects. Applying the R-039 rule (P or
  S) to both temperature sheets gives 9,516 positives; primary at either
  temperature gives 4,572; the Promotech set is primary at 30 °C only (2,791).
  The successor build contract waits for the owner's choice. The inventory is
  feasible under every variant.

## R-042 · 2026-11-02 · *L. interrogans* positive set

- **Decision (project owner).** The *L. interrogans* positives are the TSSs
  classed primary or secondary in the 30 °C sheet (`TSS-30_all`) of the
  primary table: 5,143 position–strand pairs. This applies the R-039 rule
  within one experimental condition and replaces the 2,791 stated in R-039,
  which rested on the F-115 description corrected by F-118. The control
  exclusion set stays the complete table, both temperatures and all classes
  (45,562 pairs). Chosen without data beyond the class counts and without any
  model outcome.
- **Inventory.** `scripts/inventory_cds_control_feasibility.py` now reads the
  *L. interrogans* positives from that sheet and writes
  `outputs/reports/cds_control_feasibility_v2/summary.json` (SHA-256
  `d351fdd5d5a28e5e93f60ea310832e2fd3ccaf5c554ee087969a4752f1d26ed5`); v1
  stays as the record of R-041. *L. interrogans*: 19 of 5,143 positive windows
  are not strict DNA or out of bounds; none of the remaining 5,124 lacks an
  in-frame candidate (minimum 60). *C. jejuni* and *C. pneumoniae* are
  unchanged (F-119).
- **Next.** Freeze the genomic successor build contracts for Cje (855),
  Cpne (571), and Lint (5,143).

## R-043 · 2026-11-02 · Genomic successor build contract for the reconstructed bacteria

- **Decision (project owner).** Freeze `configs/graphpro_reconstruction_v3.yaml`
  for *C. jejuni* (855 positives), *C. pneumoniae* (571), and
  *L. interrogans* (5,143). Positives come from the verified primary tables
  under the P-or-S rule (R-039, R-042); the Promotech BED only corroborates.
  The reference is the RefSeq FASTA of `ref-acq-v12`, byte-identical to the
  Promotech FASTA (R-041). One same-strand genomic control per positive, GC
  within four bases, outside 100 nt of every primary-table TSS on both
  strands (R-035, R-036), not matching an active external positive. Sampling
  seed 20261021, as in v2 (owner's choice); after 100,000 random probes a
  deterministic exhaustive replicon scan selects by reservoir sampling (owner's
  choice), as in the CDS contract and EPD v5. Pairs are indivisible;
  partitioning follows homology grouping v1 with genomic-overlap edges, test
  fraction 0.20, seed 42, five inner folds.
- **Scope.** v3 reuses no v2 sequence, control, or split. Bacillus and
  Rhodobacter stay blocked; E. coli is excluded (R-040); Human and Mouse get a
  separate 251-nt successor.
- **Gates.** Every execution gate is false. Opening extraction and control
  generation is a separate decision; confirmatory use also needs evaluation
  protocol v4 to adopt homology grouping, whose MMseqs2 stage is not yet
  implemented. No data or model outcome was used.

## R-044 · 2026-11-02 · Implementation of the homology-grouping stage

- **Code.** `src/capsprom/data/homology_grouping.py` implements
  `specs/homology_grouping_protocol.md` §3: unit edges (indivisible pairs),
  MMseqs2 `easy-search` alignment edges with thresholds re-applied and a hard
  failure when a query reaches `max_seqs`, exact strand-invariant Hamming
  edges at `floor(0.20 × L)` (pigeonhole index), and genomic-overlap edges on
  the same contig. Groups are connected components; the report counts edges by
  source and source combination, mixed-label groups, the largest group, and
  the oversize flag (> 20%). Partitioning shuffles whole groups with seed 42,
  adds a group to test when it lowers the summed per-class deviation from the
  20% targets, and assigns stratified group 5-fold inner folds (seed 42);
  cross-partition edges are counted and must be zero. Settings load from
  `configs/homology_grouping_v1.yaml`.
- **Tool.** The MMseqs2 binary of R-027 in WSL (`mmseqs-linux-avx2.tar.gz`
  SHA-256 `bd9b0234…`, version `8cc5ce367b5638c4…`, binary SHA-256
  `b7ef6e0e33df5dd4…`); each run records the binary hash, version, and full
  command line.
- **Tests.** `tests/test_homology_grouping.py`: synthetic fixtures for every
  edge source, the hit cap, components, oversize, class-targeted partition,
  zero cross-partition edges, and determinism. An integration test runs the
  real binary when `CAPSPROM_MMSEQS` is set; it recovered a 10-nt shifted copy
  and a reverse-complement copy and joined no unrelated window.
- **Not done.** No dataset was grouped. The stage binds confirmatory data only
  through evaluation protocol v4, and the v3 builder that feeds it is not yet
  implemented. No data or model outcome was used.

## R-045 · 2026-11-02 · Builder for graphpro-reconstructed-v3

- **Contract amendment before first use.** The external-positive rule of
  `configs/graphpro_reconstruction_v3.yaml` now names the source of the active
  positive sequences as in the EPD v5 builder:
  `configs/dataset_dependency_manifest_v3.yaml` (SHA-256 `70a24063…`, 18
  datasets) and the regenerated-v3 strict-DNA processed root. No state, output,
  or run of v3 existed; contract SHA-256 is now `b18a00ad…`.
- **Code.** `src/capsprom/data/primary_tss_tables.py` holds the primary-table
  readers, moved from the R-035 script (its summary and the CDS inventory v2
  summary reproduce byte-for-byte: `878c8933…`, `d351fdd5…`).
  `src/capsprom/data/bacterial_reconstruction.py` selects P-or-S loci in stable
  order, builds the complete-table exclusion set, and generates same-strand
  controls with GC count within four, random probes then the shared EPD
  exhaustive scan with reservoir sampling, external-positive rejection, and
  independent re-verification; a positive without any admissible control is
  recorded as a failure. `scripts/build_graphpro_reconstruction_v3.py` plans
  by default (hash checks, declared versus observed counts, window screening;
  writes nothing) and, with `--execute`, runs only the gated stages and writes
  each dataset once, atomically, under `data/interim/graphpro_reconstructed_v3/`.
- **Tests.** `tests/test_bacterial_reconstruction.py`: class selection and
  order, exclusion of non-positive TSS classes on both strands, strand and GC
  rules, non-overlap, determinism, exhaustive fallback, recorded failure,
  external-positive rejection, refusal of an incomplete known set, grouping
  coordinates.
- **Plan run.** Observed counts equal the declared ones (855/1,905; 571/571;
  5,143/45,562). Screening rejects 1 *C. pneumoniae* and 19 *L. interrogans*
  windows, as in F-119. `--execute` refuses while the gates are closed; nothing
  was written and no control was generated. No model outcome was used.

## R-046 · 2026-11-02 · Execution of graphpro-reconstructed-v3

- **Decision (project owner).** Open extraction, control generation,
  grouping, and split for v3. `configs/graphpro_reconstruction_v3_execution_v1.yaml`
  (SHA-256 `83da8e0b…`) extends the v3 contract by hash (`b18a00ad…`), changes
  only the gates, and pins the MMseqs2 binary of R-027 (`b7ef6e0e…`), which the
  script verifies. Training and confirmatory use stay closed.
- **Run.** `scripts/build_graphpro_reconstruction_v3.py --execute` in WSL; the
  script now resolves hash-bound `extends`. Outputs under
  `data/interim/graphpro_reconstructed_v3/` (not committed); build manifest,
  pair ledger, group table, and MMseqs2 hit table SHA-256 prefixes:

  | Dataset | Pairs | Manifest | Pair ledger | Group table | Hits |
  | --- | ---: | --- | --- | --- | --- |
  | *C. jejuni* | 849 | `2ca8f3d3…` | `cab3ce1c…` | `32e3108e…` | `3718c19f…` |
  | *C. pneumoniae* | 570 | `3e73b6b3…` | `17727d0f…` | `f22f0555…` | `ce5aef23…` |
  | *L. interrogans* | 5,123 | `8ec1a64b…` | `f5c659a5…` | `03aa0b93…` | `e34ece9f…` |

- **Results.** No control failure and no exhaustive fallback. The
  post-generation filter removed 6 (*C. jejuni*) and 1 (*L. interrogans*)
  pairs whose positive window repeats another positive. An independent scratch
  audit of the written files found 0 controls within 100 nt of any
  primary-table TSS, every GC difference within four bases, every control on
  its positive's strand, no duplicate strand-invariant identity, no pair split
  across partitions, and 0 cross-partition edges. Test sets are 20% of each
  class (170/170, 114/114, 1,025/1,025 pairs). Mean control-minus-positive GC
  count: +1.88, +1.57, and +0.01. Finding F-120 concerns the
  *L. interrogans* grouping.
- No model was trained and no test outcome exists.

## R-047 · 2026-11-03 · Null and annotation diagnostics for F-120

- **Question.** Is the 1,154-record *L. interrogans* group of F-120 produced
  by base composition, and which sequences carry its alignment edges?
  Descriptive diagnostics only; no contract, build, or split changed.
- **Null test.** Every v3 record of the three bacteria was shuffled per
  sequence, once preserving mononucleotide and once (first-order Markov)
  dinucleotide composition, seed 20261103, and searched with the R-046 MMseqs2
  binary and settings. Scratch script SHA-256 `5cb5af48388962fb…`; result
  `95bbce5343d8bb9f…`.
- **Annotation.** The group records were intersected with the
  `ref-acq-v12` RefSeq GFF (CDS products, RNAs, mobile and repeat features)
  and compared with the remaining records; shared 20-mers were counted.
  Scratch script `ac05001793996404…`; result `bb3f442b1af17078…`. Not kept in the repository.
- **Finding.** F-121. The group is not a composition artifact, so a
  composition-calibrated threshold would not change it; homology grouping v1
  is kept unchanged.

## R-048 · 2026-11-03 · Frozen repeat-linked strata for reconstructed bacteria

- **Decision (project owner).** Predeclare a secondary stratified report
  before any model result: `configs/graphpro_reconstruction_v3_repeat_strata_v1.yaml`
  (SHA-256 `3b4b6805…`). A record is `repeat_linked` when it has a non-self
  MMseqs2 hit at the homology-grouping thresholds in its dataset's v3 hit
  table (hashes pinned). The primary outcome is unchanged; strata are never
  used for selection.
- **Counts read while freezing.** Repeat-linked records are mostly positives
  across each dataset (*L. interrogans* 869 of 1,270; *C. jejuni* 173 of 179;
  *C. pneumoniae* 32 of 32), whereas controls dominate the largest
  *L. interrogans* group (F-121). This corrects the earlier reading that
  controls are more often repeat-linked overall. Because the test
  repeat-linked strata are almost all positive (159/15, 33/0, 14/0), the
  frozen metric is sensitivity per stratum and its paired-bootstrap contrast;
  specificity and MCC are reported only where a stratum holds at least 30
  negatives. The counts were read only to choose defined metrics.
- **Output.** `scripts/assign_repeat_strata_v3.py` wrote
  `data/interim/graphpro_reconstructed_v3_repeat_strata_v1/` (not committed;
  summary SHA-256 `bf3fb32f…`). No build or split changed.

## R-049 · 2026-11-03 · CDS-derived control panels on graphpro-reconstructed-v3

- **Decision (project owner).** Build the CDS panel from the v3 genomic
  build. `configs/cds_negative_control_v3.yaml` (SHA-256 `b280eed0…`) extends
  v2 by hash, pins the three v3 build manifests and the MMseqs2 binary, and
  opens control generation and split inheritance; training and test
  evaluation stay closed.
- **Code.** `sample_cds_controls` in `src/capsprom/data/cds_controls.py`
  (frame cycle, GC caliper, random probes then a full frame scan with
  reservoir sampling, non-overlap with v3 controls and selected CDS controls,
  strand-invariant identity exclusion of v3 records and active external
  positives) with fixture tests; `scripts/build_cds_controls_v3.py` (v3
  partitions and groups inherited, homology edges of CDS controls against all
  v3 records, cross-partition drops, test intersection, diagnostics). Outputs
  under `data/interim/graphpro_reconstructed_v3_cds_v1/` (not committed);
  manifests `7e42d499…` (Cje), `49f8d494…` (Cpne), `ded18af1…` (Lint).
- **Results.** *C. jejuni*: 827 of 849 pairs (19 failures, median positive GC
  6 of 81; 3 cross-partition drops), test intersection 164 of 170.
  *C. pneumoniae*: 536 of 570 (34 failures, median GC 11), intersection 110 of
  114. Frame proportions are uniform; controls are 1.7–2.3 G/C bases richer
  than their positives on average. *L. interrogans*: 1,421 of 5,123 (3,679
  failures), intersection 278 of 1,025 (finding F-123).
- **Status.** The *L. interrogans* CDS panel is not usable: its failures
  follow sampling order, which is genomic position, so the retained positives
  are positionally biased. It is kept as provenance. The *C. jejuni* and
  *C. pneumoniae* panels behave as the protocol foresees. No model was trained.

## R-050 · 2026-11-03 · *L. interrogans* excluded from the CDS condition

- **Decision (project owner).** Remove *L. interrogans* from the CDS-derived
  condition (F-123). `configs/cds_negative_control_v4.yaml` extends v3 by hash,
  restricts the scope to *C. jejuni* and *C. pneumoniae*, pins their v3-built
  panels (manifests `7e42d499…`, `49f8d494…`) as the valid ones, and closes
  generation; nothing is rebuilt. The *L. interrogans* CDS panel stays as
  provenance only; its genomic panel is unaffected. No model outcome existed.

## R-051 · 2026-11-03 · Distribution and dependency audit of the v3 panels

- **Procedure.** `scripts/audit_graphpro_v3_distribution_dependency.py` with
  `configs/graphpro_v3_distribution_dependency_audit_v1.yaml` (SHA-256
  `e48a530d…`; v3 and CDS manifests, dependency manifest v3, and MMseqs2
  binary pinned). Per panel: GC and positional composition (all and test),
  two-sided Mann–Whitney and KS on GC with Holm across the five panels.
  Dependency: exact strand-invariant sharing and an all-versus-all MMseqs2
  search (homology-grouping settings) of the three v3 genomic datasets against
  each other and the 18 eligible datasets, with the manifest-v3 join rule
  (more than 10 records with a cross-dataset neighbour). Outputs in
  `outputs/reports/graphpro_v3_distribution_dependency_v1/` (manifest
  `220f7ce7…`; not committed). Descriptive; no model output read.
- **Findings.** F-124, F-125.
- **Open decisions.** A dependency manifest v4 that adds the v3 datasets
  (Cpne in `cdbprom-chlamydophila`, Cje and Lint as own clusters) is part of
  the eligibility gate; the residual GC gap of F-124 needs a reporting or
  construction decision before confirmatory use.

## R-052 · 2026-11-03 · Residual GC gap reported as a limitation

- **Decision (project owner).** Keep the v3 genomic and CDS panels unchanged
  and report the F-124 GC gap as a limitation, instead of rebuilding with a
  narrower caliper (which would drop AT-extreme *C. jejuni* promoters).
- **Reference baseline.** `configs/graphpro_v3_gc_only_reference_v1.yaml`
  freezes a one-feature GC logistic regression, fitted on training only, whose
  test MCC is reported beside every model on the five panels with a paired
  bootstrap on shared test indices. It is descriptive and never used for
  selection. Its gates are closed until model training opens. No model
  outcome existed.

## R-053 · 2026-11-03 · Dependency manifest v4

- **Decision (project owner).** Create `configs/dataset_dependency_manifest_v4.yaml`
  from v3 by the unchanged manifest-v3 rule and F-125: the 18 eligible
  datasets keep their 12 clusters; *C. pneumoniae* v3 joins
  `cdbprom-chlamydophila`; *C. jejuni* and *L. interrogans* v3 form
  `graphpro-v3-campylobacter` and `graphpro-v3-leptospira` (21 datasets, 14
  clusters). The three v3 datasets are marked
  `candidate_pending_eligibility`; listing them assigns clusters only, and
  their CDS panels share their cluster. v3 stays bound by its existing users.
  A test checks that no eligible cluster changed and that the counts agree.

## R-054 · 2026-11-03 · Evaluation protocol v4 (design)

- **Decision (project owner).** Freeze `configs/evaluation_protocol_v4.yaml`
  as the successor of v3, design-locked with confirmatory ranking closed.
  Owner choices: (1) every dataset, including the 18 eligible ones, is
  repartitioned by homology grouping v1 (partitions, inner folds, and the
  bootstrap unit become homology groups); the record-level v3 partition is a
  predeclared sensitivity reported side by side; (2) domain windows apply,
  81 nt for prokaryotes and 251 nt for eukaryotes, so the five CNNProm
  eukaryotic datasets must be rebuilt at 251 nt before execution; (3) datasets
  enter only through an eligibility manifest, so the three GraphPro v3
  candidates join after their per-organism approval.
- **Bindings.** Dependency manifest v4 and homology grouping v1 by SHA-256;
  secondary reports (repeat strata, GC-only reference, CDS condition v4) for
  the reconstructed bacteria. New gates `grouped_domain_window_builds_complete`
  and `group_bootstrap_fixture_validated` are false. All other inference rules
  are unchanged from v3. v3 remains the active protocol of existing results,
  which stay exploratory. No data or model outcome was used.

## R-055 · 2026-11-03 · Homology-grouped domain-window builds of the 18 eligible datasets

- **Decision (project owner).** Build the evaluation-protocol-v4 partitions.
  `configs/grouped_domain_window_build_v1.yaml` (SHA-256 `58581a27…`) pins every
  source file, the v4 protocol, homology grouping v1, and the MMseqs2 binary.
  The 13 prokaryotic datasets pool their v3 filtered 81-nt records (train and
  test) unchanged, so the record-level v3 partition remains a like-for-like
  sensitivity. The 5 CNNProm eukaryotic datasets are rebuilt from their
  canonical collections (identified by matching every v3 crop to positions
  140–221 of one collection) at the native 251-nt window, through the v3
  filter stages (`src/capsprom/data/grouped_builds.py`, fixture-tested).
  Edges are MMseqs2 alignment and exact Hamming at ⌊0.20 L⌋ (16 and 50);
  genomic overlap is not applied in the `orig` condition. Test fraction 0.20,
  seed 42, five stratified group folds.
- **Run.** `scripts/build_grouped_domain_window_v1.py` in WSL (resumable,
  atomic per dataset); outputs under
  `data/processed/assembled_datasets/grouped_domain_window_v1/` (not
  committed; concatenated build manifests SHA-256 `e84435186b8663fe…`).
- **Audit.** An independent scratch audit of every `records.csv` (hash checked
  against its manifest) found 0 groups split across partitions, 20% test
  fractions per class, only domain-window lengths, and no duplicate sequence.
  No group exceeded the 20% review limit. Finding F-126.
- The v4 gate `grouped_domain_window_builds_complete` is satisfied; it will be
  set in an execution successor of the protocol, not by editing v4.

## R-056 · 2026-11-03 · Group-bootstrap fixture

- **Code.** `paired_stratified_bootstrap_mcc` in
  `src/capsprom/statistical_comparison.py` gains an optional `groups` vector.
  With it, whole groups (homology groups under evaluation protocol v4) are
  resampled with replacement, as many as there are groups, with shared indices
  for every model and seed; a draw lacking either class is redrawn. The result
  states its `bootstrap_unit`. Without `groups` the record-within-class
  behaviour is unchanged.
- **Fixture.** `tests/test_statistical_comparison.py`: 20 groups of 10
  identical records with perfectly correlated errors give the same point effect
  (0.40) but a 95% interval of [0.261, 0.540] at record level and
  [−0.038, 0.861] at group level, so record resampling understates uncertainty
  when records are dependent; also reproducibility, singleton groups, and
  input validation.
- The v4 gate `group_bootstrap_fixture_validated` is satisfied; like the build
  gate, it is set in an execution successor of the protocol. No data or model
  outcome was used.

## R-057 · 2026-11-03 · Manual review sample for the GraphPro v3 candidates

- **Decision (project owner).** Prepare eligibility gate 7.
  `configs/graphpro_v3_manual_review_v1.yaml` freezes 20 pairs per organism
  (10 per strand, lowest SHA-256 rank of the pair id) and five checks:
  positive in the primary table with P or S class, positive and control
  sequences against NCBI, control TSS margin, and CDS-control placement.
  `scripts/prepare_graphpro_v3_manual_review.py` wrote
  `docs/provenance/manual_review_graphpro_v3/review_sheet.csv` (60 rows,
  SHA-256 `5c414932…`), with instructions in the same folder. All partitions
  are represented. The review itself is the owner's and is pending; no
  eligibility changed.

## R-058 · 2026-11-03 · Manual review of the GraphPro v3 candidates

- **Review (project owner).** The filled sheet was returned on 2026-11-03 and
  replaces the blank one at
  `docs/provenance/manual_review_graphpro_v3/review_sheet.csv` (SHA-256
  `a72b0e80…`). Its 18 data columns are identical to the frozen sheet
  (`5c414932…`, R-057); only the five check columns were filled.
- **Result.** Every applicable check is `yes` in all 60 rows; no
  `reviewer_notes` were needed.

  | Organism | Rows | A–D | E (CDS control) | Result |
  | --- | ---: | --- | --- | --- |
  | *C. jejuni* | 20 | 20 yes | 18 yes, 2 n/a (no CDS control) | pass |
  | *C. pneumoniae* | 20 | 20 yes | 20 yes | pass |
  | *L. interrogans* | 20 | 20 yes | 20 n/a (no CDS panel) | pass |

- Eligibility gate 7 (manual sample audit) passes for the three organisms. No
  record was relabeled and no other gate changed.

## R-059 · 2026-11-03 · Project seed policy

- **Decision (project owner).** Fix the project seeds before the definitive
  runs. `specs/seed_policy.md` (commit `e16ed94`) gives each seed one role:
  the ten run seeds `13 … 293`, partition seed 42, one dated sampling seed per
  data procedure, and one dated resampling seed per evaluation protocol
  (`20260715` in evaluation protocol v4).
- **Reserve block.** Ten further run seeds (`337, 379, 421, 463, 509, 547, 593,
  631, 673, 719`, all prime) are predeclared. They are used only as a whole
  block, activated by a new versioned protocol before any test access, for a
  reason independent of test results.
- **Rationale.** The SD of seed means in the completed ten-seed tranches
  (0.006–0.008 MCC) gives a standard error of about 0.002–0.0026, enough for
  dataset-level estimates. With zero failures the one-sided 95% upper bound
  on a collapse rate is 0.259 with ten seeds and 0.139 with twenty, which is
  why the reserve exists.
- **Open requirement.** Training runners must record device, driver, and
  library versions in their MLflow runs before the definitive runs; only
  `src/capsprom/feasibility.py` does so today. No contract, partition, gate,
  or outcome was used or changed.

## R-060 · 2026-11-04 · Synthetic shuffle out of scope for definitive runs

- **Decision (project owner).** The `synthetic_shuffle` panel of
  `specs/negative_control_protocol.md` is not planned for the definitive runs.
  It stays defined in the protocol and in
  `configs/negative_control_evaluation_v1.yaml`, which is unchanged, so earlier
  references remain traceable.
- **Exceptions.** Workflows whose source design is a shuffle keep it: the
  Bhandari Human leakage-controlled shuffle condition and the Bhandari
  `orig-pub` replays. Shuffles used as audit tools, such as the
  composition check of F-121, are unaffected.
- **Rationale.** The panel was already optional and outside the initial
  evaluation matrix; generating shuffles is cheap, but each extra panel adds
  training and evaluation over models, seeds, and datasets. The GC-only
  reference (R-052) covers the composition baseline of the definitive
  comparison. Reinstating the panel requires a new versioned decision before
  any test access. No data, contract, partition, gate, or outcome was used or
  changed.

## R-061 · 2026-11-04 · Mapping v3 acceptance audit and CDBProm/CNNProm control feasibility

- **Procedure.** `scripts/audit_mapping_acceptance.py` with
  `configs/reference_coordinate_mapping_v3_acceptance_v1.yaml` (SHA-256
  `e6ce37be…`) reads the persisted v3 record and locus tables, recounts
  criteria 1-2, applies Stage B1 to CNNProm *E. coli* (F-098 rule) and an
  exploratory probe to CNNProm *B. subtilis* negatives, counts B3 input, and
  freezes a manual-audit sample. Summary
  `manifests/provenance/reference_coordinate_mapping_v3/acceptance_v1.json`;
  sheet `docs/provenance/manual_review_mapping_v3/review_sheet.csv` (83 rows,
  SHA-256 `ad8942ca…`). Source-only inventory of TSS exclusion sources in
  `docs/cdbprom_cnnprom_genomic_control_feasibility.md`. No model output read;
  nothing remapped, generated, or partitioned.
- **Findings.** F-127 to F-130.
- **Open decisions (project owner).** Criterion 7 (R-011 counts do not exist,
  F-093); the manual sample review (criterion 8); whether CNNProm *E. coli*
  becomes the genomic-control pilot.

## R-062 · 2026-11-04 · Mapping criterion 7, RegulonDB TSS acquisition, and E. coli control capacity

- **Decisions (project owner).** (1) Criterion 7 of the mapping protocol is
  tested against the per-category counts of the R-028 exact-search pilot
  (F-092) in place of the unavailable R-011 counts (F-093). (2) The complete
  *E. coli* TSS exclusion set is the union of all 16 RegulonDB
  high-throughput TSS datasets (source REGULONDB) and the curated PromoterSet.
- **Criterion 7.** Mapping v1 uses the same references as R-028. Pilot versus
  v1: single locus 36,185 vs 36,185; several 159 vs 160; none 180 vs 179
  (169 unmapped + 10 not evaluated). One record moves from none to several.
  v1 added IUPAC-compatible matching after the pilot: one *H. pylori* negative
  gains an IUPAC locus beside its exact one, and four *P. aeruginosa* records
  map only through IUPAC loci. The pilot outputs stayed in scratch, so the
  one-record accounting cannot be reconstructed exactly. Finding F-131.
- **Acquisition.** `scripts/acquire_regulondb_tss.py` with
  `configs/regulondb_tss_acquisition_v1.yaml`: 94 GraphQL responses stored byte
  for byte with query and SHA-256 under ignored
  `data/acquired/regulondb_tss_acquisition_v1/`; manifest in
  `manifests/provenance/regulondb_tss_acquisition_v1/`. RegulonDB release 14.0
  (PromoterSet created 2026-02-25). No upstream digest exists (trust on first
  use); the RegulonDB licence forbids redistribution, so nothing raw is
  committed.
- **Capacity.** `scripts/inventory_ecoli_control_capacity.py` with
  `configs/ecoli_control_capacity_v1.yaml` (SHA-256 `8f032077…`); summary
  `manifests/provenance/ecoli_control_capacity_v1/capacity_summary.json`.
  Positives are placed on NC_000913.3 by exact search instead of a coordinate
  lift. Findings F-132, F-133. No control generated, no partition changed, no
  model output read.
- **Open.** Manual mapping sample (criterion 8); then a pilot contract for
  CNNProm *E. coli* genomic controls (seed, attempt ceiling, GC caliper).

## R-063 · 2026-11-04 · Manual sample review of mapping v3 (criterion 8)

- **Review (project owner).** The filled sheet was returned on 2026-11-04 at
  `docs/provenance/manual_review_mapping_v3/review_sheet.csv`. Its 83 rows and
  11 data columns are identical to the frozen sheet (`ad8942ca…`, R-061); only
  the check columns were filled. As returned (SHA-256 `a32b9011…`), every row
  read `yes` in both checks, including the 31 rows without a single locus.
- **Correction (project owner's instruction).** The README requires
  `check_locus_in_ncbi = n/a` for rows with no single locus, so it was set to
  `n/a` in the 27 `ambiguous` (`multiple_loci`) and 4 `not_evaluated`
  (`ambiguous_bases`) rows; no other cell changed. Final sheet SHA-256
  `725a39ec…`.
- **Result.** No `no` and no `reviewer_notes`.

  | Status | Rows | Locus in NCBI | Assembly matches source |
  | --- | ---: | --- | --- |
  | `verified` | 44 | 44 yes | 44 yes |
  | `inconsistent` (`assembly_conflicting`) | 8 | 8 yes | 8 yes (documented substitute, F-104) |
  | `ambiguous` (`multiple_loci`) | 27 | 27 n/a | 27 yes |
  | `not_evaluated` (`ambiguous_bases`) | 4 | 4 n/a | 4 yes |

- Criterion 8 of `specs/reference_coordinate_mapping_protocol.md` passes for
  mapping v3. Its locus check covers the 52 single-locus rows only. No record,
  status, or gate changed; the remaining acceptance items of F-100 are
  unaffected by this review.

## R-064 · 2026-11-04 · CNNProm E. coli genomic-control pilot contract (design)

- **Decision (project owner).** Draft
  `configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml` for the
  `genomic_gc_matched` condition of CNNProm *E. coli*
  (`cnnprom-ecoli-sigma70.recon-genomic-v1`), the pilot named in R-062.
  Positives are placed on NC_000913.3 by exact search; the exclusion set is
  the RegulonDB union (F-132) plus every locus of every positive, r = 100 on
  both strands; GC caliper 4; one same-strand control per positive.
- **Problem positives.** A scratch identification found five: rrsAp2 (2 loci,
  both union TSSs) and gltIp1 (11 loci, one the PromoterSet gltIp1 TSS); serWp
  and rplUp 1 nt from a union TSS; araCp 18 nt from the current RegulonDB
  araCp TSS. The contract resolves multiple loci by union promoter name and
  header coordinate and classes TSS support as exact, near (±2 nt), shifted,
  or none, each with a declared action. No label is changed and no window is
  recropped. The cases must be reproduced by versioned code before freezing.
- **Accepted proposals.** Sampling seed 20261104; controls overlapping native
  CNNProm negatives are rejected; the residual GC gap is reported with the
  GC-only reference (R-052); near tolerance 2 nt; shifted records stay in
  both panels and are excluded from positional analyses.
- All execution gates except `open_decisions_resolved` remain false. No
  control generated, no partition changed, no model output read.

## R-065 · 2026-11-04 · CNNProm E. coli pilot builder and reproduction of the five cases

- **Code.** `src/capsprom/data/ecoli_genomic_pilot.py` implements the positive
  policy of `configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml`: RegulonDB
  union, exact placement on NC_000913.3, multi-locus resolution by PromoterSet
  name and header coordinate, and TSS-support classes (signed distance
  `reference − record` in transcription direction, negative = upstream).
  Native CNNProm negatives are placed on every exact NC_000913.3 locus and
  become blocked intervals. `scripts/build_cnnprom_ecoli_genomic_pilot.py`
  verifies the genome and every RegulonDB response hash, places the
  positives, checks the contract's observed cases, and writes the placement
  summary (committed) and ledger (ignored, SHA-256 `916ebb1d…`); `--execute`
  refuses while `contract_frozen` or `builder_fixture_tested` is false.
- **Fixtures.** `tests/test_ecoli_genomic_pilot.py` mirrors the five
  situations on a synthetic genome (resolved and unresolved multi-locus,
  near on both strands, shifted, none), the exclusion of every positive locus,
  out-of-range RegulonDB rows, and native-negative placement.
- **Contract edits (draft, before freezing).** `multiple_loci` gains the
  header offset rule left implicit in R-064 (offset of the nearest
  single-locus, strand-agreeing positive) and `header_agreement_tolerance_nt:
  2`; `negative_policy` gains `regulondb_acquisition`.
- **Result.** All five cases reproduce (F-134). No control generated, no
  partition changed, no model output read; all gates are unchanged.
- **Open before freezing.** `external_active_positive_identity` names
  dependency manifest v4 but not its SHA-256, dataset count, or the processed
  root of the active datasets; the builder refuses to generate until they are
  declared. Grouping and split are not yet implemented for this pilot.

## R-066 · 2026-11-04 · Nearest-GC-first control selection for the E. coli pilot

- **Decision (project owner).** Taken in a forked session and relayed to this
  one; the owner's words: "Adote as recomendações: * predeclarar o 'GC mais
  próximo primeiro', com ±4 como teto; * manter a referência só-GC de
  qualquer forma; * medir a diferença residual como diagnóstico." This
  supersedes R-064's `residual_gc_gap` choice.
- **Rule.** Among windows that pass every exclusion rule (unchanged), the
  control is the one with the smallest absolute G/C count difference to its
  positive; four bases stay a hard ceiling. Within one distance, candidates are
  tried in a permutation seeded by the sampling seed and the positive locus;
  positives are processed in stable source order. The v3 bacterial panels
  accept the first candidate within the caliper, so the two rules' GC gaps are
  not compared as one. Rationale: F-124 (asymmetric density inside the caliper
  for AT-rich positives) and F-133 (about 26 free slots per positive).
- **Code.** `admissible_windows` indexes every start that passes the static
  rules (strict DNA, the both-strand TSS radius, native-negative blocks) by GC
  count; `select_nearest_gc_controls` applies the dynamic rules (overlap with
  selected controls, strand-invariant identity with positives, external
  positives, and selected controls). The builder re-verifies every control
  with `find_control_exclusion_violations` and `blocked_violations`. The shared
  `reconstruct_bacterial_controls` is not changed. Fixtures: brute-force
  equality of the admissible index, minimal-distance choice, ceiling,
  determinism and seed dependence, forbidden identities, failure, and blocked
  re-verification.
- **Contract.** `negative_policy.control_selection` replaces the probe and
  exhaustive-scan fields; `residual_gc_gap` becomes a diagnostic and the
  GC-only reference stays beside every model. Draft SHA-256 `98369f01…`.
  Plan mode re-run: the five cases still reproduce. No control generated; all
  gates unchanged.

## R-067 · 2026-11-04 · Closing the three open points of the E. coli pilot contract

- **Decision (project owner).** The owner approved the three proposed
  solutions ("Sim, implementar"); they are recorded under
  `resolved_decisions` of `configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml`.
- **External active-positive identity.** The scope is all 21 datasets of
  dependency manifest v4 (SHA-256 `e46826c6…`): the 18 eligible datasets from
  their `grouped_domain_window_v1/<dataset>/records.csv` (label 1, the records
  evaluation protocol v4 uses) and the three graphpro-reconstructed-v3
  candidates, which have no grouped build, from their v3 `pair_ledger.csv`
  (`positive_sequence`). Every file is hash-pinned in the contract; the
  builder aborts if the declared sources differ from the manifest. Only 81-nt
  positives can match, so the 251-nt eukaryotic positives are read and cannot
  match. 22,765 distinct 81-nt sequences are read.
- **Grouping and split.** Each source record (positives and negatives) is
  matched to the native grouped build `cnnprom-prokaryotic-Ecoli` by
  (label, sequence); the builder aborts unless the match is one to one. It is:
  3,839 records, positives 168 test and 671 train. Each control inherits its
  positive's group and partition label (test or train fold). Under
  `--execute`, homology grouping v1 (MMseqs2 binary pinned, alignment, Hamming,
  and genomic-overlap edges; coordinates for controls and single-locus
  positives only) runs on every native record plus every control, and a
  control with an edge to another partition label is dropped with its pair and
  written to `cross_partition_drops.csv`, as in `scripts/build_cds_controls_v3.py`.
  The native split is never recomputed. The build writes `test_intersection.csv`.
- **Real-data validation.** Plan mode now runs a static capacity check before
  any control exists: 1,525,588 admissible windows (3,064,926 removed by the
  TSS radius, 51,058 by native-negative blocks); all 839 genomic-panel
  positives have an admissible window at GC distance 0; no admissible window
  equals an active external positive (the two genome windows equal to
  CDBProm *S. Typhimurium* positives are not admissible). The check ignores
  competition between positives; real failures will appear in
  `control_failures.csv` of the immutable build.
- **Code.** `ecoli_genomic_pilot.py` gains `read_active_positives`,
  `native_assignments`, `cross_partition_links`, `nearest_gc_capacity`, and
  `forbidden_admissible_windows`, each with fixtures. Contract draft SHA-256
  `c9294b63…`; the five observed cases still reproduce.
- **State.** No control generated, no partition changed, no model output read.
  `contract_frozen` and `builder_fixture_tested` stay false until the owner
  freezes the contract.

## R-068 · 2026-11-05 · CNNProm E. coli genomic pilot contract frozen

- **Decision (project owner).** Freeze `configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml`
  in place rather than in a v2 successor: no state file or build exists for
  it, and no other contract or spec cites its draft hashes (checked with
  `git grep`; only R-066/R-067 and the regenerated placement summary do).
  The spec's "successor contract" is the pilot contract after the
  feasibility inventory, which v1 is.
- **Edits.** `version: 1.0.0`, `status: frozen_before_any_model_result`,
  `contract_frozen` and `builder_fixture_tested` set to true (fixtures in
  `tests/test_ecoli_genomic_pilot.py`, R-065 to R-067), and
  `observed_cases_status` now cites the versioned reproduction. No scientific
  parameter changed. Frozen SHA-256 `f68676e9ae036c0452176a6628d4cd42f426a49c7fc820d61acbd4673f77be76`.
- **Plan mode re-run.** The placement summary is regenerated against the
  frozen hash; the five cases still reproduce.
- **State.** No control generated yet; any further change needs a new
  versioned contract.

## R-069 · 2026-11-05 · CNNProm E. coli genomic pilot control build

- **Run.** `scripts/build_cnnprom_ecoli_genomic_pilot.py --execute` under the
  frozen contract (SHA-256 `f68676e9…`) with the pinned MMseqs2 binary
  (`b7ef6e0e…`, version `8cc5ce36…`). Output, ignored by git:
  `data/interim/cnnprom_ecoli_genomic_pilot_v1/builds/cnnprom-ecoli-sigma70.recon-genomic-v1/`,
  `build_manifest.json` SHA-256 `31fda2c70c397285d23779e4f6f2cf56e64bb7685ed411a67cf8f5a566f2d89c`,
  `pair_ledger.csv` `9d604b2f…`.
- **Result (F-136).** 839 controls selected, none failed, all at GC distance
  0; independent re-verification found no TSS-radius or blocked-interval
  violation. The pair filter removed one positive-duplicate pair (rraBp1,
  whose window is the reverse complement of argIp's), leaving 838 pairs.
  Grouping edges: 1,007 alignment, 7 Hamming, 156 genomic overlap; 0
  cross-partition drops; 168 test and 670 train pairs; test intersection 168.
- **State.** Gate `controls_generated` is satisfied by this build; the
  contract is not edited (frozen). Next: distribution and dependency audit,
  then the manual sample audit. No model trained, no test outcome read.

## R-070 · 2026-11-05 · Distribution and dependency audit of the E. coli genomic pilot

- **Procedure.** `scripts/audit_graphpro_v3_distribution_dependency.py` (the
  R-051 audit, reused) with `configs/cnnprom_ecoli_genomic_pilot_audit_v1.yaml`
  (SHA-256 `4a87a468…`). Two generalizations, behaviour-preserving for the v3
  config: a ledger that already carries `partition` is read directly, and the
  comparison datasets can come from the hash-pinned sources of a frozen
  contract (here the 21 sources of the pilot contract `f68676e9…`, both
  labels). Overlaps are reported for every audited panel, not only
  `graphpro-` names. Output, ignored by git:
  `outputs/reports/cnnprom_ecoli_genomic_pilot_audit_v1/`, manifest
  `a36c6143…`. No model output read; no dataset changed.
- **Result (F-137).** GC distributions of positives and controls are
  identical; the largest positional total variation is 0.243 at the TSS base
  (+1), then −11 (0.220) and −7 (0.185), the −10 region; median over
  positions 0.050. Exact sharing: 838 positives with cnnprom-prokaryotic-Ecoli
  (expected) and 1 positive with CDBProm *S. Typhimurium*; no control shares
  an exact identity with any dataset. Alignment neighbours: 838 records with
  cnnprom-prokaryotic-Ecoli, 134 with *S. Typhimurium*, 79 with *K.
  pneumoniae*; 9 alignment edges are opposite-label (3, 4, 2). The pilot is
  proposed into `enteric-cross-source`, the cluster of its native dataset.
- **State.** Gate `distribution_and_dependency_audit` satisfied by this audit
  (recorded here; the frozen contract is not edited). Next: manual sample
  audit, then the eligibility manifest.

## R-071 · 2026-11-05 · Manual review sample of the E. coli genomic pilot

- **Sample.** `configs/cnnprom_ecoli_genomic_pilot_manual_review_v1.yaml`
  freezes 25 pairs of the pilot build (`31fda2c7…`): the five contract
  observed cases plus 20 random pairs (10 per strand, lowest SHA-256 rank of
  the record id). `scripts/prepare_cnnprom_ecoli_genomic_pilot_manual_review.py`
  wrote `docs/provenance/manual_review_ecoli_genomic_pilot/review_sheet.csv`
  (SHA-256 `e294e297…`), with instructions in the folder README; it refuses
  to overwrite the sheet. No check result or model output was read.
- **Checks.** A, positive TSS in RegulonDB by promoter id, name, strand, and
  declared support distance; B, positive sequence against NCBI; C, control
  sequence, strand, and G+C count against NCBI; D, no RegulonDB TSS within
  100 nt of the control. A direct RegulonDB promoter URL was tried and does
  not resolve, so the sheet gives the promoter id and the README points to
  the gene pages and the acquired PromoterSet.
- **State.** Review pending (owner).

## R-072 · 2026-11-05 · Manual review result of the E. coli genomic pilot

- **Review.** The owner reviewed the 25 frozen pairs of R-071 and reported
  checks A, B, C, and D as `yes` on every row. No `no` was reported, and no
  sample cell changed from the frozen sheet `e294e297…`.
- **Sheet correction.** The owner first entered one `yes` per row in
  `reviewer_notes` and left A to D empty. After the owner confirmed in chat
  that each `yes` covered all four checks, the values were moved to A to D
  and `reviewer_notes` was cleared. The filled sheet is
  `docs/provenance/manual_review_ecoli_genomic_pilot/review_sheet.csv`,
  SHA-256 `e4d3a269c515b0a03b2a2037905ea03a9538300cb5de07d3d67106a91bc7508b`.
- **Result.** 25 of 25 rows pass, so the panel passes under the README
  decision rule. This rests on the owner's review; the agent did not repeat
  the checks against RegulonDB or NCBI.
- **State.** Gate `manual_sample_audit` satisfied by this review (recorded
  here; the frozen contract is not edited). Next: the eligibility manifest.

## R-073 · 2026-11-05 · Eligibility manifest v2 draft for the E. coli genomic pilot

- **Draft.** `configs/dataset_eligibility_manifest_v2.yaml` extends v1 by
  hash with a development tier. Its only panel is
  `cnnprom-ecoli-sigma70.recon-genomic-v1`, for exploratory training only.
  The confirmatory scope stays at 18 datasets, and v1 is not edited.
- **Checks.** Read from the pair ledger: 838 pairs, 81 nt of A, C, G, and T;
  838 unique positives and 838 unique controls, also under reverse
  complement; no identity shared across labels; 797 homology groups, none
  across partitions; 168 test pairs and 670 training pairs. Every SHA-256
  pinned in the manifest was recomputed from the file.
- **Dependency.** The panel is declared in `enteric-cross-source` (F-137).
  Dependency manifest v4 stays unchanged; cluster-aggregated inference over
  this panel needs a successor.
- **State.** Draft. Gate `eligibility_manifest_approved` is not satisfied
  until the owner approves. No training contract, no model run.

## R-074 · 2026-11-05 · Eligibility manifest v2 approved

- **Decision (project owner).** Approve
  `configs/dataset_eligibility_manifest_v2.yaml` as drafted in R-073,
  SHA-256 `dacf13123686c11fb7c542f713f5b0e735891ef0aea4ee022acb4d81b4e57ed8`. Only the status, approval, and decision fields changed
  from the draft.
- **Effect.** `cnnprom-ecoli-sigma70.recon-genomic-v1` is eligible for
  exploratory training only. The confirmatory scope stays at the 18 datasets
  of v1, and `project_status.py` keeps pointing to v1.
- **State.** Gate `eligibility_manifest_approved` satisfied by this approval
  (recorded here; the frozen contract is not edited). All seven gates of the
  pilot contract are now satisfied. Training still needs its own versioned
  contract and authorization.

## R-075 · 2026-11-05 · Pilot training contract draft

- **Draft.** `configs/cnnprom_ecoli_pilot_training_v1.yaml` (SHA-256
  `01049588…`) and `specs/cnnprom_ecoli_pilot_training.md` define the question,
  hypotheses, panels, grouping, seeds, models, budget, metrics, and tracking of
  the pilot. Each section separates established, proposed, and pending
  decisions. Status: draft, pending owner approval. All execution gates that
  allow data materialization, training, final fits, or test access are false.
- **Integration.** `src/capsprom/data/pilot_panels.py` builds condition files
  from the native build and the pair ledger. `protocol.fold_manifest_root` lets
  the canonical plan use inherited group-safe folds in place of
  `write_fold_manifest`, which ignores homology groups; contracts without that
  key behave as before. `tests/test_pilot_panels.py` ran one CPU inner fold on a
  fixture. No real panel was materialized.
- **Open.** Nine items, including the negative-control design successor and the
  GraphPro Human/Mouse audit gate. No model run.

## R-076 · 2026-11-05 · Visual analysis of the E. coli pilot panels

- **Procedure.** `scripts/analyze_cnnprom_ecoli_panels.py` with
  `configs/cnnprom_ecoli_panel_analysis_v2.yaml` (`df702eab…`). Output, ignored
  by git: `outputs/reports/cnnprom_ecoli_panel_analysis_v2/`, manifest
  `6932984e…`. Report: `docs/reports/cnnprom_ecoli_panel_analysis_v2/README.md`.
  Sequence-content analyses read training folds only; the test partition enters
  count tables only. The contract hash was pinned before the first run.
- **Correction.** Version 1 used PCA starts, so all t-SNE seeds were identical
  and its seed check was empty. Version 2 uses random starts and adds the
  native-negative structure. Version 1 output stays as a record and is not used.
- **Result.** F-138 to F-141. The contract was not changed; proposals P10 to P14
  are listed in the report for owner decision.
- **State.** No model output read, no control modified, no dataset changed.

## R-077 · 2026-11-06 · Genomic-overlap regrouping of CNNProm E. coli

- **Decision (project owner).** Regroup native negatives by genomic overlap
  before training (F-139, proposal P10).
- **Check before the build.** Identifier and coordinate counts only, with test
  records included, which this decision required. 3,811 of 3,839 records have one
  exact locus on NC_000913.3, and 28 are multi-locus and keep sequence edges
  only, as the protocol states. Of 4,674 overlap edges, 1,192 crossed train and
  test in the version 1 partition, 41 of them between positives and 6 between a
  positive and a negative (F-142). The genomic panel shares those positive edges.
- **Method.** `configs/grouped_domain_window_build_v2.yaml` (SHA-256 `1ae9080f…`)
  applies the existing homology protocol with the genomic-overlap edge, using the
  same assignment rule and seeds. A repair that moved only linked records was
  measured and rejected: it would be a new partition rule chosen after seeing the
  data, and it would still move 71 positives.
- **Result.** `data/processed/assembled_datasets/grouped_domain_window_v2/`,
  manifest `192174e0…`, records `786452c2…`: 1,372 groups, largest 22 records,
  no oversized group, 0 cross-partition edges, no record removed. Test has 168
  positives and 600 negatives. 650 of 3,839 records keep their partition, and 34
  of the 168 former test positives stay in test.
- **Consequences.** The version 1 build stays as a record but must not be used for
  training. The pilot contract, build, audit, eligibility manifest v2, and draft
  training contract all pin version 1 and need successors. A count with stored
  hits shows 2 pilot pairs would be dropped for cross-partition links, before
  overlap edges. Most of the new test partition was training data in R-076, so
  that analysis must be rerun on the new training folds before it informs any
  decision. No model output exists, so no test outcome was seen.

## R-078 · 2026-11-06 · E. coli pilot rebuilt on grouped build v2

- **Decision (project owner).** Rebuild the pilot chain on build v2.
- **Contract.** `configs/cnnprom_ecoli_genomic_control_pilot_v2.yaml` (SHA-256
  `a0537ea8…`, frozen before any model result) changes only the native build and
  the dataset identity, now `cnnprom-ecoli-sigma70.recon-genomic-v2`.
- **Build.** Manifest `18f815a5…`, ledger `d59af431…`. 839 controls selected, 0
  failures, all at G+C distance 0, and the same filter removal as before. 2 pairs
  were dropped for cross-partition links, leaving 836 (168 test, 668 train).
- **Equivalence.** All 836 pairs have the same positive, control sequence, and
  coordinates as build v1, so only partitions and groups changed.
- **Audit.** `configs/cnnprom_ecoli_genomic_pilot_audit_v2.yaml` (`6af11ae4…`),
  manifest `f3cbf225…`, ignored output
  `outputs/reports/cnnprom_ecoli_genomic_pilot_audit_v2/`. No control shares an
  exact identity with any dataset; opposite-label alignment edges remain 9 (3, 4, 2)
  and the proposed cluster stays `enteric-cross-source`.
- **Manual review.** Not repeated. All 25 reviewed pairs have identical sequences in
  build v2, and checks A to D do not depend on partition, so the R-072 result
  carries over. The `partition` column of the sheet is historical.
- **State.** Gates of pilot v2 are satisfied by these entries, except the eligibility
  manifest. No model output read.

## R-079 · 2026-11-06 · Successor drafts and panel analysis v3

- **Drafts.** `configs/dataset_eligibility_manifest_v3.yaml` supersedes the approved
  v2, which pinned the leaky partition; it is pending owner approval.
  `configs/cnnprom_ecoli_pilot_training_v2.yaml` (`11c5267f…`) changes only data
  pins, counts, partitions, and open items, and still has every gate closed. Unlike
  v1 it was written after a visual analysis, and it says so.
- **Analysis.** `configs/cnnprom_ecoli_panel_analysis_v3.yaml` (`3fcbfb07…`) reruns
  the same method on the new training folds. Output, ignored by git:
  `outputs/reports/cnnprom_ecoli_panel_analysis_v3/`, manifest `440e35c5…`. Report:
  `docs/reports/cnnprom_ecoli_panel_analysis_v3/README.md`. The conclusions of
  R-076 hold; numbers changed slightly.
- **Residual.** F-143. The owner decides whether multi-locus records need more (P15).
- **State.** No model output read, no panel materialized, no training gate opened.

## R-080 · 2026-11-06 · Eligibility manifest v3 approved

- **Decision (project owner).** Approve `configs/dataset_eligibility_manifest_v3.yaml`
  as drafted in R-079, SHA-256 `9dd18eb8eec768cbadd099878e48ffc1e63a0966c578eda6eb96b783041b2c43`. Only the status, approval, and decision
  fields changed from the draft.
- **Effect.** `cnnprom-ecoli-sigma70.recon-genomic-v2` is eligible for exploratory
  training only. It replaces the approval of v2 (R-074), which pinned the leaky
  partition. The confirmatory scope stays at the 18 datasets of v1, and
  `project_status.py` keeps pointing to v1.
- **State.** Gate `eligibility_manifest_approved` of pilot v2 is satisfied by this
  approval (recorded here; the frozen contract is not edited). The draft training
  contract v2 names this manifest by path and takes its hash when the owner approves
  that contract. Training still needs that approval and a separate authorization.
