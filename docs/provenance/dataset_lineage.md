# Dataset Lineage

How each experimental dataset traces back to identified upstream files, and how
strong that evidence is. The evidence classes are defined in
`specs/data_provenance_policy.md` §4. Records are in
`manifests/provenance/source_acquisition_v1/`; observation times are inside each
record.

## Chain for the confirmatory datasets

```text
upstream release (pinned commit / URL + digest)            acq-v1 acquisition_manifest.json
  └─ data/acquired/source_acquisition_v1/<source>/<file>   byte replay ▼
       └─ legacy builders (fasta_builders, crop -60..+20, group-safe split, seed 42)
            └─ data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/*.csv
                 └─ run_summary.json / plan_state.json     train/test dataset SHA-256
```

## Regenerated-v3 replay

`record_provenance.py replay-v3` places the acquired files under their legacy
names, as mapped by the canonicalization contract, and runs the same builders,
crop windows, and seed as `scripts/rebuild_real_negative_datasets.py`.
Record: `regenerated_v3_replay.json`.

| Datasets | Train/test CSV | Intermediate FASTA | Pooled rows |
| --- | --- | --- | --- |
| 11 CDBProm + 7 CNNProm (all 18 confirmatory) | byte-identical | same records; line wrapping differs (60 vs 80 columns) | identical |
| 7 GraphPro (excluded from confirmatory use) | byte-identical | same records | identical |
| GraphPro `clostridium_phytofermentans` → `chlamydophila_pneumoniae` | different partition | same records | identical |

The single mismatch is explained by the code, not by the data. The builder
derives each dataset's random stream from its name (`_dataset_rng`), and the
later correction of the `Cpne` organism name changes that stream. Train and test
together hold exactly the same rows.

**Conclusion.** The 18 confirmatory datasets are reproduced byte for byte from
`source_acquisition_v1`. Their lineage is established by byte replay, with no
dependence on the undated `data/raw/` copies.

## Experiment records

`record_provenance.py experiment-links` scans every local JSON record under
`outputs/` for stored dataset hashes (`*_dataset_sha256`, `train_sha256`,
`test_sha256`). Record: `experiment_dataset_links.json`.

| Records | Count | Linked by replay |
| --- | ---: | --- |
| Classical run summaries (`outputs/runs/*/run_summary.json`) | 298 | 287 fully linked |
| Basic CapsProm campaign plan (`outputs/capsprom_basic_canonical_v1/plan_state.json`) | 1 | 25 of 26 dataset hashes; the remaining one is GraphPro `Cpne` |
| GraphPro reconstructed-split audit | 1 | 0 of 12 (reconstruction outputs, not regenerated-v3) |

The 11 unlinked run summaries are the Bhandari human MVP, full, and
leakage-controlled runs, and the exploratory real-negative smoke runs. They use
other builds (`intra_strict_dna`, `bhandari_human_shuffle_v1`, and earlier
`intra` CSVs) that have not been replayed.

## Legacy `data/raw/` inventory

`record_provenance.py legacy-inventory` hashes all 189 files.
Record: `legacy_raw_inventory.json`.

| Group | Byte-identical | Sequence-equivalent | Not reproduced | Notes |
| --- | ---: | ---: | ---: | --- |
| `Bhandari_etal` | 6 | 0 | 1 | `.gz` archives and their decompressed `.fa` match the Drive files; README not reproduced |
| `CDBProm` | 23 | 0 | 1 | all TXT files and `training_data.csv` match the archive or the repository; README not reproduced |
| `CNNProm` | 0 | 15 | 1 | renamed files with CRLF line endings and unwrapped sequences; same sequences per class |
| `GraphPro` | 0 | 16 | 3 | positive and negative files are sequence-equivalent; the two `cTest.txt` training logs differ from the repository copies; README not reproduced |
| `iPro-MP` | 47 | 0 | 4 | benchmark files byte-identical; README and copied code not reproduced |
| `Fuitfly` | 1 | 2 | 0 | `Drosophila_promoter_all_1941.fa` matches BDGP byte for byte; `drosophila.fa` and `human.fa` are sequence-equivalent to BDGP collections |
| `EDP` | 0 | 0 | 2 | `edp_all.fa` is a corrupted export (F-011), replaced by release 128 |
| `Nova pasta (2)` | 1 | 0 | 0 | a duplicate of the CDBProm `training_sequences.zip` |
| `Nova pasta` | 0 | 0 | 1 | `predictions_ecoli.zip` (633 MB), not a source release |
| `references` | 14 | 0 | 51 | EPDnew BEDs, Promotech BEDs, and three primary-TSS supplements match; 11 CDBProm RefSeq genomes, two Bacillus DOCX, two E. coli XLS, and the physicochemical tables are not in `acq-v1` |

### Acquisition dates of legacy files

| Status | Files | Basis |
| --- | ---: | --- |
| `unknown` | 125 | No dated record exists. File modification times were not used. |
| `recorded` | 44 | `retrieved_utc` 2026-10-27T22:50:59+00:00 in the untracked `data/raw/references/cdbprom_genomes_v1/manifest.json` (NCBI Datasets v2). |
| `no_later_than` | 20 | The file's SHA-256 first appears in a committed config or document; the commit date is an upper bound, not the acquisition date. |

## What remains unlinked

See the "Lineage" rows of `docs/provenance/findings_register.md` and the next
steps in `docs/source_acquisition_v1_report.md`.
