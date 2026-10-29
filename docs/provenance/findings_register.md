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
| F-031 | 2026-10-29 | Fact | 30 Bhandari Human records (lengths 302 to 921 nt) and 3 Yeast records (352, 732, 884 nt) are shorter than 1,000 nt. All 30 Human records lie on hg38 alternate contigs (`*_alt`); 2 of the 3 Yeast names carry a negative coordinate (`chrVI_-647`, `chrXV_-115`). In all 33, `range` length counted 1-based closed equals the sequence length. | canonical tables `bhandari-human`, `bhandari-yeast` (`length`, `original_header`); log R-016 |
| F-032 | 2026-10-29 | Hypothesis | The 33 short Bhandari windows were truncated at a contig or chromosome end, so their TSS is not at index 700 and may lie outside the window. | Inferred from F-031; not mapped to the genome. |
| F-033 | 2026-10-29 | Fact | Bhandari positives are 50.9% (Human 31,400 `+`, 30,146 `-`) and 50.4% (Yeast 3,088 `+`, 3,037 `-`) forward-strand; every sequence is in transcript orientation per its `strand` header. Exact reverse-complement pairs among unique sequences: Human 1, Yeast 3; palindromes: 0. | canonical tables; log R-016 |
| F-034 | 2026-10-29 | Fact | 51 CDBProm negatives are exactly 99 nt (Synechocistis 9, S. Typhimurium 7, Anabaena 6, P. aeruginosa 6, M. tuberculosis 5, S. coelicolor 5, H. pylori 4, B. amyloliquefaciens 3, C. glutamicum 3, K. pneumoniae 3, C. pneumoniae 0); no other length deviates. | canonical tables `cdbprom-*`; log R-016 |
| F-035 | 2026-10-29 | Hypothesis | The 99-nt CDBProm negatives come from an off-by-one in the authors' sampling (an inclusive upper bound for the window start, such as Python `random.randint`, with a 100-nt slice), which shortens the window drawn at the last start. About 39 of 15,656 would be expected with a ~400-position range; 51 were observed. Testable by mapping: such negatives should end at the sampling-region boundary. | Sampling code not released; F-034. |
| F-036 | 2026-10-29 | Fact | Legacy builders drop or reshape off-length records without a per-reason count: `keep_most_common_length` silently drops non-modal records (CDBProm, Bhandari FASTA builds), and `normalize_to_min_length` truncates every GraphPro record to the minimum observed length (its target is the minimum, so padding never applies). The leakage-controlled Bhandari build excludes non-1,000-nt records and reports only `raw_records` and `retained_source_records`. | `src/capsprom/data/sequences.py`, `fasta_builders.py`, `leakage_controlled.py:57` |
| F-037 | 2026-10-29 | Fact | 5 Bhandari nominal-Plant records (306, 306, 334, 344, 801 nt) lie on mm10 unplaced or `_random` contigs; two start at position 1 with negative coordinates in their names (`-655`, `-693`), and each `range` length counted 1-based closed equals the sequence length. | canonical table `bhandari-nominal-plant`; log R-017 |
| F-038 | 2026-10-29 | Fact | The 6 Bhandari Human random-genomic negatives shorter than 1,000 nt (970, 971, 981, 990, 993, 998) are each identical, forward strand, to an entire hg38 unplaced scaffold (`chrUn_KI270539v1`, `KI270392v1`, `KI270423v1`, `KI270385v1`, `KI270312v1`, `KI270394v1`) in the acquired `hg38.2bit`. | log R-017 |
| F-039 | 2026-10-29 | Fact | GraphPro *L. interrogans* has one positive and one negative of 82 nt; all other records are 81 nt. The legacy builder truncated both to 81 nt (F-036). The reason for the extra base is undocumented. | canonical table `graphpro-lint`; log R-017 |
| F-040 | 2026-10-29 | Fact | A scan of all 64 `can-v1` collections finds length deviations only in the 16 collections covered by the table in `specs/dataset_integrity_audit.md` ("Length exclusion"): 98 records in total (Bhandari 44, CDBProm 51, GraphPro 2, Promotech 1). The first version of that table, from log R-016, omitted F-037 to F-039. | `length_matches_expected` in every canonical table; log R-017 |
| F-041 | 2026-10-29 | Fact | Bhandari `range=chr:a-b` headers are 1-based closed: extracting `[a-1, b)` from the declared UCSC assembly, reverse-complemented when `strand=-`, reproduces the sequence for all 158 records checked (a pilot of the first 20 records per strand by `sequence_sha1` rank in Human/hg38, Yeast/sacCer3, and nominal Plant/mm10, plus all 38 short records). The 0-based half-open reading matches none. | `manifests/provenance/source_acquisition_v1/bhandari_range_pilot.json`; log R-018 |
| F-042 | 2026-10-29 | Fact | In all 120 pilot records, the coordinate in the record name equals `a` on `+` and `a + 300` on `-`, so it is the 1-based start of the 700-nt upstream region on the transcript's strand. | same record |
| F-043 | 2026-10-29 | Hypothesis | Index 700 (0-based) of each full Bhandari window is the first transcribed base of the named RefSeq transcript, as the Table Browser "upstream by 700" region plus a 300-nt 3' pad would produce. Consistent with F-042; not yet compared with the transcript annotation. | F-042 |
| F-044 | 2026-10-29 | Fact | Supersedes the "may lie outside" part of F-032: all 38 short Bhandari windows (Human 30, Yeast 3, nominal Plant 5) lost only upstream bases at a contig or chromosome end; their downstream side is intact. Under F-043 the TSS lies inside every one, at index 1 to 620 instead of 700. | `bhandari_range_pilot.json`; log R-018 |
| F-045 | 2026-10-29 | Fact | All 40 pilot records of the file distributed as Bhandari "Plant" are recreated exactly from mm10 at their header coordinates. This locates those sequences in the mouse assembly; it does not establish why the publication describes *A. thaliana* (F-016, F-017). | `bhandari_range_pilot.json` |
| F-046 | 2026-10-29 | Fact | The regenerated-v3 CDBProm negative FASTA files hold exactly the canonical negatives minus the 99-nt records in each of the 11 organisms (51 in total), so the legacy modal-length step removed precisely the F-034 records and no other. | `data/interim/fasta/nonprom-cdbprom-*` record counts versus canonical tables; log R-018 |

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
