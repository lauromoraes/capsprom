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
