# Source Acquisition v1 Report

Run date: 2026-10-27. Protocol: `specs/source_acquisition_protocol.md`.
Contracts: `configs/source_acquisition_v1.yaml` and
`configs/source_canonicalization_v1.yaml`.

## Acquisition

210 upstream files were declared. All 210 were downloaded into
`data/acquired/source_acquisition_v1/` and recorded in
`acquisition_manifest.json`.

| Source | Files | Verified against a declared digest | Size (MB) |
| --- | ---: | ---: | ---: |
| `bhandari-drive` | 3 | 1 | 36.8 |
| `bhandari-github` | 3 | 3 | 0.6 |
| `cdbprom-website` | 1 | 1 | 4.8 |
| `cdbprom-github` | 4 | 4 | 17.2 |
| `cnnprom` | 16 | 16 | 38.9 |
| `graphpro` | 19 | 19 | 5.1 |
| `ipro-mp` | 47 | 47 | 40.6 |
| `epd` (release 128) | 3 | 1 | 3.1 |
| `bdgp` | 41 | 0 | 5.8 |
| `promotech` | 61 | 61 | 27.5 |
| `epdnew` | 5 | 5 | 3.4 |
| `primary-tss-supplements` | 4 | 3 | 14.6 |
| `ucsc-genomes` | 3 | 3 | 1,553.2 |

Every GitHub blob reproduced the Git blob SHA-1 listed at its pinned commit.
Every previously recorded project digest (UCSC md5, EPDnew BEDs, primary TSS
supplements, CDBProm archive, Bhandari yeast archive) was reproduced. Files
without a declared digest (BDGP, two Bhandari archives, EPD 128, the Leptospira
supplementary archive) were checked through legacy parity below.

Two acquisition details:

- `aw.iimas.unam.mx` omits its GlobalSign intermediate certificate. The
  intermediate is fetched from its AIA URL and pinned by SHA-256; the chain is
  still verified to the system root.
- Europe PMC builds the Leptospira supplementary archive on every request, so
  the archive hash is not stable upstream. Its `Table4.XLSX` member reproduces
  the SHA-256 recorded in `configs/graphpro_primary_tss_source_comparison_v1.yaml`.

## Canonicalization

All 64 collections pass validation: per-class record counts equal the declared
release counts, and every collection with a legacy `data/raw/` copy has an
identical per-class sequence multiset. The canonical tables occupy 83 MB.

| Source | Collections | Positives | Negatives | Length mismatches | Non-ACGT | Duplicates | Cross-label collision records |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Bhandari | 4 | 174,191 | 593 | 44 | 139 | 58,801 | 0 |
| CDBProm | 11 | 15,656 | 15,656 | 51 | 10 | 223 | 0 |
| CNNProm | 8 | 47,317 | 74,421 | 0 | 3 | 752 | 0 |
| GraphPro | 8 | 15,935 | 16,121 | 2 | 3 | 17 | 2,692 |
| iPro-MP | 23 | 107,286 | 214,572 | 0 | 8 | 2 | 342 |
| EPD 128 | 1 | 4,806 | 0 | 0 | 278 | 13 | 0 |
| BDGP | 3 | 2,762 | 10,844 | 0 | 249 | 2 | 0 |
| Promotech 40-nt | 6 | 12,016 | 11,711 | 1 | 14 | 192 | 2 |

These flags describe the releases and are not corrected at this stage.

## Findings

- **Legacy parity.** Fresh downloads reproduce the sequence content of every
  legacy `data/raw/` copy that has a declared counterpart, including the nominal
  Bhandari Plant file (still 106,520 `mm10` records).
- **Legacy EPD export is corrupted.** `data/raw/EDP/edp_all.fa` matches the
  -250..+50 crop of release 128 for 4,795 of its 4,796 entries. Entry `EP11051`
  is 335 nt and begins with the server error text `CLOSE: INVALID FILE UNIT 14
  (FILENAME)`. Ten release-128 entries are absent from the export. Release 128
  replaces it.
- **iPro-MP label collisions.** 342 records (171 sequences) in 17 species share
  a sequence with a record of the other label (positive versus CDS or intergenic
  negative). 57 of those sequences span the published train/test split. This
  was not visible in the earlier count-only audit.
- **GraphPro E. coli.** 2,690 collision records (1,345 sequences in both class
  files) confirm the known released-label problem.
- **Duplicates.** Bhandari Human and nominal Plant are 43% and 30% exact
  duplicates within the positive class, which is consistent with the publication's
  deduplication step not being applied to the release.
- **Promotech `CPNEUMONIAE/positive.fasta`** contains one record of length 1.

## Provenance follow-up (2026-10-28)

- A re-verification run (no downloads) re-hashed all 210 files and is the first
  entry in the manifest's `runs[]`. The first acquisition predates run records
  and is documented in `docs/provenance/research_log.md` (R-002).
- Upstream commit dates and HTTP `Last-Modified` values are recorded separately
  from acquisition times in
  `manifests/provenance/source_acquisition_v1/source_release_metadata.json`.
- Replaying the regenerated-v3 build from these files reproduces the train and
  test CSVs of all 18 confirmatory datasets byte for byte
  (`docs/provenance/dataset_lineage.md`).

## Not done

- No new dataset was built, split, or used for training, and all experiment
  gates are unchanged. The existing confirmatory datasets are linked to this
  acquisition by replay, not rebuilt.
- CDBProm and GraphPro TSS positions remain undocumented, so `tss_index` is empty
  for them by design.
- The 11 CDBProm RefSeq genomes (in `data/raw/references/cdbprom_genomes_v1/`,
  with an untracked retrieval record), the iPro-MP accessions, the GraphPro
  Bacillus DOCX and E. coli pAA XLS supplements, and the physicochemical
  reference tables are not part of `acq-v1`. They need a pinned
  `source_acquisition_v2`.
