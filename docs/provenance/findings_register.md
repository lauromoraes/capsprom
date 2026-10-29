# Findings Register

Findings about data origin and quality, each with one epistemic status as
defined in `specs/data_provenance_policy.md` §6:

- **Fact**: reproducible from the named record or command.
- **Hypothesis**: plausible explanation, not verified.
- **Limitation**: known gap in what the evidence supports.

IDs are stable. A status change is a new dated row that references the old ID;
existing rows are not rewritten. Data version abbreviations:
`acq-v1` = `configs/source_acquisition_v1.yaml` (SHA-256 `8e08e614…`),
`can-v1` = `configs/source_canonicalization_v1.yaml` (SHA-256 `eb5460a0…`).
Records cited as `prov/…` are in `manifests/provenance/source_acquisition_v1/`.

## Acquisition and sources

| ID | Date | Status | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-001 | 2026-10-28 | Fact | All 210 declared upstream files of `acq-v1` were acquired and re-verified by SHA-256; every GitHub blob reproduced the Git blob SHA-1 of its pinned commit and every declared upstream or project digest matched. | `prov/acquisition_manifest.json` (`files`, `runs[0]`) |
| F-002 | 2026-10-28 | Limitation | 46 files have no independent digest (41 BDGP, 2 Bhandari Drive archives, `epd128.seq` and the EPD README, and the Europe PMC Leptospira archive, which is generated per request). Their integrity rests on trust-on-first-use, plus legacy parity (F-010) where a legacy copy exists. | `prov/acquisition_manifest.json` (`verified_against: []`) |
| F-003 | 2026-10-28 | Fact | `aw.iimas.unam.mx` (CDBProm) omits its GlobalSign intermediate certificate; the intermediate was pinned by SHA-256 from its AIA URL and TLS verification stayed enabled. | `configs/source_acquisition_v1.yaml` (`tls_intermediate`) |
| F-004 | 2026-10-28 | Fact | Upstream dates reported by sources differ from acquisition dates; for example CNNProm's pinned commit is dated 2016-12-24, and EPD `epd128.seq` reports `Last-Modified` 2016-07-20, both acquired on 2026-10-27. | `prov/source_release_metadata.json`, `prov/acquisition_manifest.json` |
| F-005 | 2026-10-28 | Limitation | BDGP, Europe PMC, NCBI efetch, and two journal supplement hosts report no `Last-Modified` (or reject `HEAD`), so their upstream version dates are unknown. | `prov/source_release_metadata.json` |
| F-006 | 2026-10-28 | Limitation | The first acquisition run (2026-10-27T23:40Z–2026-10-28T00:22Z UTC) predates run records; its command and code state are documented retrospectively (log R-002), not machine-recorded. | `docs/provenance/research_log.md` R-002 |

## Release content

| ID | Date | Status | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-010 | 2026-10-28 | Fact | All 64 canonical collections pass: per-class counts equal the declared release counts, and every collection with a `data/raw/` counterpart has an identical per-class sequence multiset. | `prov/canonical_manifest.json` |
| F-011 | 2026-10-28 | Fact | The legacy EPD export `data/raw/EDP/edp_all.fa` is corrupted: entry `EP11051` contains server error text, and 10 release-128 entries are absent. Release 128 replaces it in `can-v1`. | `docs/source_acquisition_v1_report.md` |
| F-012 | 2026-10-28 | Fact | iPro-MP releases 342 records (171 sequences, 17 species) that share a sequence with the opposite label; 57 of those sequences span the published train/test split. | `data/canonical/source_canonicalization_v1/ipro-mp-*.csv.gz` (`cross_label_collision`) |
| F-013 | 2026-10-28 | Fact | GraphPro E. coli has 2,690 cross-label collision records (1,345 sequences). | canonical table `graphpro-ecol` |
| F-014 | 2026-10-28 | Fact | Bhandari Human and nominal Plant positives contain 43% and 30% exact within-class duplicates. | canonical tables `bhandari-human`, `bhandari-nominal-plant` |
| F-015 | 2026-10-28 | Hypothesis | The Bhandari duplication reflects that the publication's deduplication step was not applied to the distributed files. | Not verified against the authors' code. |
| F-016 | 2026-10-28 | Fact | The file distributed as Bhandari "Plant" has 106,520 records with `mm10` headers, against 41,671 `araTha1` promoters in the paper. | `docs/dataset_reconstruction_sources.md` |
| F-017 | 2026-10-28 | Hypothesis | The Bhandari "Plant" file is a mislabelled mouse promoter set. | Header assembly only; sequence-to-genome mapping not performed. |
| F-018 | 2026-10-28 | Fact | CDBProm positives are 1,001 nt and negatives 100 nt, while the paper states a -60..+1 window; the TSS position inside the 1,001 nt window is undocumented. | `docs/dataset_reconstruction_sources.md` |
| F-019 | 2026-10-28 | Fact | Promotech `CPNEUMONIAE/positive.fasta` contains one record of length 1. | canonical table `promotech-cpneumoniae` |

## Lineage of experimental datasets

| ID | Date | Status | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-020 | 2026-10-28 | Fact | Replaying the regenerated-v3 build from `acq-v1` reproduces the train and test CSVs of all 18 confirmatory datasets (11 CDBProm, 7 CNNProm) and of 7 of the 8 GraphPro datasets byte for byte. | `prov/regenerated_v3_replay.json` |
| F-021 | 2026-10-28 | Fact | For GraphPro `Cpne`, the replayed partition differs while the pooled rows are identical. The split seed is derived from the dataset name, which was corrected from `clostridium_phytofermentans` to `chlamydophila_pneumoniae` after v3 was built. | `prov/regenerated_v3_replay.json` (`pooled_rows_match`); `capsprom.data.dataset_builders._dataset_rng` |
| F-022 | 2026-10-28 | Fact | The legacy intermediate FASTA files under `data/interim/fasta/` hold the same records as the replay, but are wrapped at 60 columns instead of 80. Their SHA-256 values in the v3 filtering manifest therefore identify the legacy formatting, not the content. | `prov/regenerated_v3_replay.json` (`interim_fasta_*`) |
| F-023 | 2026-10-28 | Fact | 287 of 298 local classical run summaries, and 25 of 26 dataset hashes in the basic CapsProm campaign plan, reference only replay-verified datasets. The unlinked ones are Bhandari human runs, exploratory smoke runs, and GraphPro `Cpne`. | `prov/experiment_dataset_links.json` |
| F-024 | 2026-10-28 | Limitation | Experiment records outside the local `outputs/` (remote campaign hosts, the MLflow database) were not scanned. | `docs/provenance/dataset_lineage.md` |
| F-025 | 2026-10-28 | Fact | Of 190 files in `data/raw/`, 92 are byte-identical to an acquired file, archive member, or decompressed archive, 33 are sequence-equivalent, and 65 are not reproduced by `acq-v1`. | `prov/legacy_raw_inventory.json` |
| F-026 | 2026-10-28 | Fact | No acquisition date exists for 126 legacy files. 44 CDBProm RefSeq genome files carry `retrieved_utc` 2026-10-27T22:50:59Z in an untracked legacy manifest, and 20 files have only an upper bound from the commit that first recorded their hash. | `prov/legacy_raw_inventory.json` (`acquisition_date`) |
| F-027 | 2026-10-28 | Limitation | The 11 CDBProm RefSeq genomes, two Bacillus DOCX supplements, two E. coli pAA XLS supplements, and the physicochemical reference tables are used by earlier audits but are not part of `acq-v1`. They remain linked only by legacy records. | `prov/legacy_raw_inventory.json` |
| F-028 | 2026-10-28 | Fact | The legacy CNNProm copies were renamed and reformatted (CRLF line endings, unwrapped sequences) relative to the pinned repository, with identical sequences per class. | `prov/legacy_raw_inventory.json`; `cmp` against `cnnprom/*.fa` |
| F-029 | 2026-10-28 | Hypothesis | The CNNProm reformatting was introduced by a manual copy step on Windows. | Not verifiable; no record of the copy exists. |
| F-030 | 2026-10-28 | Fact | Supersedes the counts of F-025 and F-026 after log R-010: of 189 files in `data/raw/`, 92 are byte-identical, 33 sequence-equivalent, and 64 not reproduced by `acq-v1`; no acquisition date exists for 125 legacy files (44 recorded, 20 upper bound unchanged). | `prov/legacy_raw_inventory.json` (observed 2026-10-28T22:05:11Z) |
