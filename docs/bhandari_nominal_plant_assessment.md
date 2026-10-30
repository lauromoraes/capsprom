# Bhandari "Plant" Data: Provenance, Identification, and Use

Technical record of the investigation into the dataset that Bhandari et al.
(2021) call "Plant", and the rules for its later use. It applies
`specs/dataset_condition_policy.md`. Findings are cited by ID from
`docs/provenance/findings_register.md`; procedures are logs R-022 to R-025 of
`docs/provenance/research_log.md`. The academic account is in
`docs/thesis/data_acquisition_provenance.tex`.

No dataset, partition, or execution gate was changed by this investigation, and
no model was trained.

## 1. Names and identifiers

Three things share the name "Plant" and must not be confused.

| Object | Historical designation (kept verbatim) | Project identifier | Verified organism |
| --- | --- | --- | --- |
| Drive file `Raw Data/Plant_promoters.gz` (2021-01-21) | `Plant_promoters`; "A. thaliana" in the publication | canonical collection `bhandari-nominal-plant` (`can-v1`) | *Mus musculus*, `mm10` (F-063, F-073) |
| Repository file `Promoter_ArabidopsisThaliana.csv` (2020-04-23 to 2021-01-21), label `Plant_Promoter` | "A. thaliana", `araTha1` in the publication | canonical collection `bhandari-history-arabidopsis` (`bh-can-v1`), built from `bh-hist-v1` | *Arabidopsis thaliana*: 41,594 records in TAIR10.1, the other 77 in mitochondrion Y08501.2 (F-066, F-074) |
| The publication's plant column (Table 2, Fig. 3) | "Arabidopsis thaliana" | none | not attributable to a file with certainty (F-071) |

Historical names are never changed: collection IDs, file names, and labels stay
as released. Derived datasets carry `source_designation`, `verified_organism`,
and `designation_conflict` as separate fields (policy §4). The planned
experimental identifiers are in §5.

## 2. Sources and versions

| Abbreviation | Contract | What it holds | Integrity |
| --- | --- | --- | --- |
| `acq-v1` | `configs/source_acquisition_v1.yaml` | Drive `Plant_promoters.gz` (SHA-256 `49438378…`), repository at `31d88cd` (2022-10-12) incl. `README.md`, `Update`; UCSC `mm10.2bit`, `hg38.2bit`, `sacCer3.2bit` | Drive: trust on first use (F-002); GitHub: Git blob SHA-1 |
| `can-v1` | `configs/source_canonicalization_v1.yaml` | canonical tables `bhandari-human`, `-yeast`, `-nominal-plant` | per-class counts and legacy parity (F-010) |
| `ref-acq-v1`–`v3` | `configs/reference_acquisition_v1.yaml` … `v3` | UCSC RefSeq tables; NCBI annotation releases 109 (human) and 108 (mouse) | upstream MD5 |
| `bh-hist-v1` | `configs/bhandari_history_acquisition_v1.yaml` | repository at `c1c97ee` (2021-01-14): the three historical CSVs, `Code.ipynb`, `README.md` | Git blob SHA-1 |
| `ref-acq-v4` | `configs/reference_acquisition_v4.yaml` | **failed**: the GenArk `md5sum.txt` lists a stale digest for `chromAlias.txt`; kept as a record | — |
| `ref-acq-v5` | `configs/reference_acquisition_v5.yaml` | **invalid**: a config-generation error gave its `chrom.sizes` entry the assembly-report URL; kept as a record, never used | — |
| `ref-acq-v6` | `configs/reference_acquisition_v6.yaml` | UCSC GenArk TAIR10.1 (GCF_000001735.4): 2bit, chrom sizes, assembly report, `ncbiRefSeq` GTF (2025-06-09) | hub MD5 |
| `ref-acq-v7` | `configs/reference_acquisition_v7.yaml` | earlier mitochondrial genome Y08501.2 (NC_001284.2, suppressed 2018) | trust on first use (efetch) |
| `bh-can-v1` | `configs/bhandari_history_canonicalization_v1.yaml` | canonical tables `bhandari-history-arabidopsis`, `-human`, `-yeast` (P-6) | release counts; byte-for-byte rebuild of each source file (F-075) |
| `ref-acq-v8` | `configs/reference_acquisition_v8.yaml` | NCBI RefSeq GFF of GCF_000001735.3 (TAIR10, 2018-04-02) and GCF_000001735.4 (TAIR10.1, 2023-06-16) | upstream MD5 |
| `ref-acq-v9` | `configs/reference_acquisition_v9.yaml` | Ensembl Plants release 31 TAIR10 gene models (GTF, 2017-07-18) | BSD sum checked against Ensembl `CHECKSUMS` |

Publication: Bhandari, Khare, Walambe, Kotecha, *PeerJ Comput. Sci.* 7:e365
(2021), doi:10.7717/peerj-cs.365; arXiv:2105.07659 v1, read for F-059 (the
PeerJ page refused automated access). Repository:
<https://github.com/nikitabhandari-dl/Dataset>.

## 3. Evidence by status

### Declared by the source (not verified by declaration alone)

- About 41,671 *A. thaliana* sequences from UCSC `araTha1`; −700..+300 windows
  from the Table Browser "RefSeq Genes"; 35,000 "randomly selected" after
  cleaning; 1:1 shuffled negatives; stratified 90/10 split with 10% of training
  for validation (F-059).
- The Drive folder as the data location (README since 2021-01-14, F-064); the
  file name `Plant_promoters`.

### Verified

| Claim | Evidence | Record |
| --- | --- | --- |
| The Drive "Plant" file is mouse | all headers `mm10` on mouse-only chromosome names (F-058); 45 sequences recreated from `mm10` (F-037, F-045); all 106,520 sequences recreated exactly from `mm10` at their header coordinates (F-073); 46,817 TSS equal the named mouse transcript start (F-055) | `prov/bhandari_range_pilot.json`, `prov/bhandari_tss_status.json`, `prov/bhandari_recreation.json` |
| The repository held an *A. thaliana* file with the published count | commit history (F-064) | GitHub API; `bh-hist-v1` |
| That file is *A. thaliana* | 41,594/41,671 sequences found exactly in TAIR10.1, on all seven replicons (F-066); the other 77 exactly in the earlier mitochondrion Y08501.2 (F-074); mean GC 35.3% (F-065) | `manifests/provenance/bhandari_history_acquisition_v1/history_comparison.json` |
| Its windows are TSS-anchored on the TAIR10 annotation | index 700 is a TAIR10 transcript 5' end for 41,539 of 41,591 evaluated windows; the other 52 are mitochondrial or mitochondrion-like (F-077). Against later RefSeq annotations: 22,970 (2025), 22,980 (2023), 22,879 (2018) exact (F-076) | `manifests/provenance/bhandari_arabidopsis_tss_v1/tss_classification.json` |
| The historical canonical tables are lossless | each source file rebuilt byte for byte from its canonical rows; contiguous record IDs; valid hashes (F-075) | `manifests/provenance/bhandari_history_canonicalization_v1/canonical_verification.json` |
| TAIR10 has the published count | 41,671 TAIR10 transcripts in Ensembl Plants 31 (F-077) | same TSS record |
| Human and Yeast are unchanged between repository and Drive | equal sequence multisets (F-065) | same |
| The two "Plant" files are disjoint | no shared sequence (F-065) | same |
| The released pipeline differs from the text | `Code.ipynb`: first-N selection, `k_let = 1`, no seed (F-070); `Update`: no subsampling (F-060) | acquired files |
| `araTha1` is not served by UCSC today | HTTP 404, API error (F-069) | log R-023 |

### Hypotheses

- F-072: the Drive "Plant" file was a wrong upload on 2021-01-21, and the
  published plant results come from the repository file.
- F-067 was confirmed (F-074): the 77 records not in TAIR10.1 are on the
  earlier mitochondrial sequence Y08501.2.
- F-078: one window per TAIR10 transcript; within-file duplicates are isoforms
  sharing a TSS; RefSeq mismatches come from later 5' extensions.
- F-079: the 17 multi-locus chromosome-2 windows are mitochondrial windows
  that also match the chromosome-2 mitochondrial insertion.

### Open questions

- Whether the published *A. thaliana* results were computed on the repository
  file (no saved output exists; F-071).
- Whether `araTha1` was ever a UCSC assembly, and which annotation it carried
  (F-069).
- The TSS of the 52 mitochondrial or mitochondrion-like *A. thaliana* windows
  (F-077), and of the 59,692 untestable mouse windows (F-056).
- Whether each window maps to one specific TAIR10 transcript (F-078).

## 4. Reproduction

All commands run from the repository root in the WSL environment
(`docs/development_environment.md`). The two records are deterministic; only
`observed_at` changes between runs.

```bash
PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --config configs/bhandari_history_acquisition_v1.yaml --execute
PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --config configs/reference_acquisition_v6.yaml --execute
PYTHONPATH=src .venv/bin/python scripts/record_provenance.py bhandari-history
PYTHONPATH=src .venv/bin/python scripts/record_provenance.py bhandari-recreation
PYTHONPATH=src .venv/bin/python scripts/canonicalize_sources.py --config configs/bhandari_history_canonicalization_v1.yaml
PYTHONPATH=src .venv/bin/python scripts/record_provenance.py bhandari-history-canonical
PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --config configs/reference_acquisition_v8.yaml --execute
PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --config configs/reference_acquisition_v9.yaml --execute
PYTHONPATH=src .venv/bin/python scripts/record_provenance.py arabidopsis-tss
```

`arabidopsis-tss` reads the loci written by `bhandari-history`, so it runs
after it. The Ensembl GTF has no digest that the tool can check; verify it with
`sum -r Arabidopsis_thaliana.TAIR10.31.gtf.gz`, which must print `02936 7710`.

| Step | Code | Parameters | Output |
| --- | --- | --- | --- |
| History comparison and *A. thaliana* location | `capsprom.data.provenance.bhandari_history_record`, `locate_exact_sequences` | exact full-length match on both strands; 32-mer anchor at the first ACGT-only offset; N matches only N | `manifests/provenance/bhandari_history_acquisition_v1/history_comparison.json` (counts, hashes); loci in ignored `data/interim/bhandari_history/arabidopsis_loci.json` |
| TSS check (*A. thaliana*) | `_transcript_starts` | 1-based TSS = start + 701 on `+`, start + 300 on `−` (1,000-nt windows only) against GTF `transcript` rows | same record |
| P-6 canonicalization (historical condition) | `capsprom.data.canonical_sources` (`label_csv` format) | one record per row in file order; uppercase and whitespace removal only; label text kept in `original_header` and required to equal `source_label` | `data/canonical/bhandari_history_canonicalization_v1/*.csv.gz` and `canonical_manifest.json` (snapshot committed) |
| P-6 verification | `verify_label_csv_canonical` | rebuild `label,sequence` + CRLF and compare bytes with the acquired file; IDs, indexes, SHA-1; comparison with the Drive table by multiset and order | `manifests/provenance/bhandari_history_canonicalization_v1/canonical_verification.json` |
| TSS classification (reconstructed condition) | `classify_window_tss`, `transcript_intervals` | 1,000-nt located windows only; window TSS = locus start + 701 (`+`) or + 300 (`−`); annotated TSS = 5' end of `transcript`, `mRNA`, `lnc_RNA`, `ncRNA`, `tRNA`, `rRNA`, `snoRNA`, `snRNA`, `miRNA`, `primary_transcript`, `antisense_RNA` features on the same contig and strand; nearest locus for multi-locus records; classes `exact`, `within_10`, `within_100`, `within_500`, `inside_transcript_far`, `outside_transcript_far`, `no_transcript_on_strand`; Ensembl contig names mapped through the GCF_000001735.3 assembly report | `manifests/provenance/bhandari_arabidopsis_tss_v1/tss_classification.json`; per-record classes and signed distances in ignored `data/interim/bhandari_history/arabidopsis_tss_evidence.csv` (SHA-256 in the record) |
| Full recreation of the Drive files (P-1) | `capsprom.data.provenance.recreate_ucsc_ranges` | `range=chr:a-b` read 1-based closed (F-041), reverse complement on `strand=-`, case-insensitive comparison | `manifests/provenance/source_acquisition_v1/bhandari_recreation.json` (record IDs only) |

Tests: `tests/test_provenance.py` (`test_recreate_ucsc_ranges_*`,
`test_locate_exact_sequences_*`, `test_verify_label_csv_canonical_*`,
`test_classify_window_tss_*`) and `tests/test_source_acquisition.py`
(`test_label_csv_*`, `test_real_history_canonical_config_*`), on synthetic
inputs.

Long runs use a persistent wrapper started with `nohup setsid`, which writes the
commit, the SHA-256 of the two modules, and each step's start time to
`data/interim/bhandari_history/logs/run_<UTC>.log`, and its PID to the matching
`.pid` file. To follow a run:

```bash
tail -f data/interim/bhandari_history/logs/run_<UTC>.log
```

A run is complete when the log ends with `finished`; `failed <step>` marks an
error. Each record is written atomically, so a failed run leaves the previous
record intact. The run of record started at 2026-10-29T23:22:16Z and finished
at 23:29:20Z (`run_20261029T232216Z.log`, PID file beside it), on commit
`3cc3618` with the two modules uncommitted; their SHA-256 values are in the log.

## 5. Decisions and use

### Historical condition (P-6, released data)

The canonical collection `bhandari-history-arabidopsis` is the input of every
released-condition use of the *A. thaliana* file. Its contract fixes:

| Element | Rule |
| --- | --- |
| Inputs | `bhandari-github-history/Promoter_ArabidopsisThaliana.csv` of `bh-hist-v1`, SHA-256 `9dd8df09…`, checked against the acquisition manifest before every build |
| Stable identifier | `bhandari-history-arabidopsis:bhandari-github-history/Promoter_ArabidopsisThaliana.csv:<row, 7 digits, 0-based>`; the row number is the line number of the acquired file minus one |
| Allowed transformations | whitespace removal and uppercasing (none occurred); nothing else |
| Kept as released | every record, its order, its sequence (including the 27 with symbols outside ACGT and the 3 shorter than 1,000 nt), its label text `Plant_Promoter` |
| Flags, not filters | `duplicate_of`, `strict_dna`, `invalid_symbols`, `length_matches_expected`; filters are declared by each later build and counted there |
| Metadata | organism *Arabidopsis thaliana*, as declared by the source and verified (F-066, F-074): no correction is needed. `tss_index = 700` is the publication's declaration; its verification is reconstructed-condition evidence (F-077) and is not written into the table |
| Not allowed | replacing a sequence or a window by one extracted from TAIR10 or TAIR10.1, re-centring, re-orienting, merging with the Drive files |
| Acceptance | release count 41,671; every row has the declared label; rows rebuilt as `label,sequence` + CRLF reproduce the acquired bytes; IDs contiguous; SHA-1 valid. All passed (F-075) |

Replay contract decisions (`orig-pub-v1`, not yet frozen):

| Element | Decision |
| --- | --- |
| Selection | random selection of the per-class sample, as the publication states, with a declared seed; the notebook's first-N selection (F-070) is not used, because file order is genomic order and would bias the sample by chromosome |
| Software | the project's current stack (Python 3.13, current PyTorch/scikit-learn); legacy Keras code is reimplemented, not run, so every result is at best `qualified` |
| Kept from the published procedure | length filter (1,000 nt), exact deduplication after concatenating promoters and shuffles, 1:1 mononucleotide shuffles (`k_let = 1`), 4-mer tokens, 81/9/10 split, the published CNN and LSTM architectures |
| Corrected and declared as deviations (F-080) | tokenizer fitted on the training partition only; validation partition passed to training so early stopping works; stratified split; evaluation on the test partition only (the extra human file is unreleased) |
| Reported, not corrected, in `pub` | the per-position `Dense` layers of the CNN, as published, with the corrected `Flatten` order as a declared variant |
| Leakage measurement | for each seed, count test records with an exact duplicate, a reverse complement, a >= 500 bp genomic overlap (F-082), or their shuffled partner (F-083) in training; reported beside the metrics, without changing the split |
| Independence | the contract uses only the canonical table (F-075); it does not depend on the TSS classes, on F-078 or F-079, or on R-1 to R-5, which concern the reconstructed condition only. The 77 records on the earlier mitochondrion and the 52 outside nuclear transcript starts stay in the data, because the published procedure keeps them |
| Still to fix before freezing | number of seeds and what they vary; sample size per class (the publication's "35,000" is not the 37,957 unique records, F-081); the published values and tolerance that define a successful reproduction |

Filters a published-protocol replay may declare, each counted per class and per
partition: records not of length 1,000 (3; the authors' code drops them,
F-070), exact duplicates after concatenation with the shuffles (the authors'
code does this, F-070), and records with symbols outside ACGT (27; not done by
the authors, so a replay that removes them is `qualified`).

### Reconstructed condition (separate decision)

Re-extracting windows is not needed to reproduce the baseline and is not part
of P-6. If an *A. thaliana* reconstruction is wanted later, the evidence shows
that the windows are already anchored on TAIR10 transcript starts (F-077);
the requirements are in §7 (R-1 to R-5).

### Uses

| Use | Identifier | Condition / protocol | Requirements | Comparability with the publication |
| --- | --- | --- | --- | --- |
| Replay of the published pipeline on the *A. thaliana* repository file | `bhandari-history-arabidopsis.orig-pub-v1` | released / published | canonical collection `bhandari-history-arabidopsis` (done, F-075); decisions in the table above (random selection, current stack, F-080 deviations declared) | `qualified`: seed and shuffle stream unknown, notebook and text disagree |
| Mouse benchmark from the Drive file | `bhandari-nominal-plant.orig-common-v1` | released / common | filters by rule (duplicates F-014, short windows F-037); P-4 before cross-source use | not comparable (another organism) |
| Replay of the published pipeline on the Drive file | `bhandari-nominal-plant.orig-pub-v1` | released / published | as above | `not_comparable` to the *A. thaliana* column; useful only as a diagnostic |
| *A. thaliana* benchmark, project protocol | `bhandari-history-arabidopsis.orig-common-v1` | released / common | canonical collection; filters by rule; the 77 records on the earlier mitochondrion (F-074) kept or filtered by a declared rule | within-project only |
| *A. thaliana* reconstruction | `bhandari-arabidopsis_thaliana-reconstructed-v1` | reconstructed | R-1 to R-5 of §7; project negative rule | within-project only |
| Mouse reconstruction | `bhandari-mus_musculus-reconstructed-v1` | reconstructed | windows from `mm10` for the TSS-verified records (F-055) | within-project only |

Rules that follow from the evidence:

- The Drive file is never used or reported as a plant dataset. Its
  reinterpretation as mouse is a metadata correction (policy §2), recorded
  beside the original designation.
- The repository file is a released file of the same study, not a
  reconstruction: it is used unchanged, under its own acquisition, and never
  merged with the Drive release.
- In cross-species experiments, organism groupings use the verified organism.
  A published pair "trained on *A. thaliana*" is reproduced only with the
  repository file.
- Reproducing a published number shows that the computation can be repeated;
  it does not establish the reliability of conclusions drawn from it (§6).

## 6. Contribution to the thesis

What this work supports, and what it does not, assessed against the evidence.

**Methodological contribution (supported).** A procedure for establishing the
identity of a released benchmark from independent evidence rather than from its
name: (i) separating what a source declares from what can be verified; (ii)
checking organism and assembly by exact recreation from declared coordinates,
and by exact genome search when no coordinates exist; (iii) checking the window
anchor against transcript annotations of identified releases; (iv) searching
the repository history for earlier releases; and (v) classing every resulting
change as filtering, metadata correction, or reconstruction, with a stated
comparability. Its value is shown by a concrete outcome: the file distributed
under the plant name is mouse, and the plant set described by the paper was
found in the repository history. Its generality is not yet shown; it has been
applied in full to one source and in part to GraphPro.

**Data curation (supported, not a methodological contribution by itself).** The
acquisition contracts, hashes, canonical tables, coordinate and TSS records,
the identification of the historical file, and the condition and identifier
rules. These make the experiments traceable; their merit is completeness and
correctness, not novelty.

**Requires validation before it can be claimed.**

- That the published *A. thaliana* results come from the repository file
  (F-071, F-072). Without it, a qualified reproduction of the plant column is
  possible, but not a confirmation of the published value.
- That identity errors change experimental conclusions. This needs the planned
  comparison of the same models on the released, filtered, and reconstructed
  conditions; until it runs, the effect of the "Plant" error on model rankings
  is unknown.
- That the procedure generalizes: it must be applied to the other sources and
  its outcomes reported, including where it finds nothing.

**Reproducibility versus reliability.** The published pipeline can be replayed,
and its yeast notebook even ships outputs; that tests repeatability. The
reliability of conclusions depends on data identity (now settled for both
files), negative construction (synthetic shuffles, a known weakness), selection
details (F-070), and split leakage (F-014). A faithful replay therefore still
yields conclusions about the benchmark, not necessarily about promoter biology.

## 7. Pending evidence

| ID | Evidence | Unblocks | State |
| --- | --- | --- | --- |
| P-1 | Recreation of all 106,520 Drive "Plant" records (and all Human and Yeast records) from their header coordinates | final metadata correction; any `bhandari-nominal-plant` build | **done**: 174,191/174,191 identical (F-073) |
| P-2 | An author statement, PeerJ correction, or saved *A. thaliana* run output | F-071, F-072 | partly resolved by the repository history; no statement found |
| P-3 | Historical status of UCSC `araTha1` and its annotation | F-069; TSS check with a contemporary annotation | open (Internet Archive offline on 2026-10-29) |
| P-4 | Exact and near-duplicate overlap of the mouse file with CNNProm Mouse and GraphPro Mouse | cross-source use of the mouse file | open |
| P-5 | Annotation for the untested TSS (F-056, F-068) | larger reconstructions | open |
| P-6 | Canonical collection for `bh-hist-v1` under a new canonicalization contract | any build from the repository file | **done**: `bh-can-v1`, all acceptance criteria passed (F-075) |
| P-7 | The 77 unlocated *A. thaliana* records against the earlier mitochondrial sequence | F-067 | **done**: 77/77 exact in Y08501.2 (F-074) |
| P-9 | Genomic-overlap and pair-leakage counts per seed for the `orig-pub` split (F-082, F-083) | interpretation of any `orig-pub` metric | open; counts without a split are in F-081, F-082 |
| P-8 | Restore the text of `configs/reference_acquisition_v7.yaml` (overwritten by another session, log R-025) so that its SHA-256 equals the manifest's `d9d38d57…` | integrity of `ref-acq-v7` | **done**: restored by the session that wrote it; SHA-256 equals the manifest (`d9d38d57…`) |

Requirements for a future *A. thaliana* reconstruction (not started):

| ID | Requirement |
| --- | --- |
| R-1 | A versioned TAIR10 sequence frame: the 2bit of TAIR10.1 (`ref-acq-v6`) for nuclear and chloroplast windows, and Y08501.2 (`ref-acq-v7`) for the mitochondrion, whose two versions differ (F-074) |
| R-2 | TSS from a declared annotation version: TAIR10 (Ensembl Plants 31, `ref-acq-v9`) reproduces the windows (F-077); re-centring on the 2025 RefSeq TSS would move the 18,621 windows not at one of its starts, mostly upstream (F-076), and must be a separate, declared variant |
| R-3 | One-to-one assignment of windows to TAIR10 transcripts, and a rule for isoforms sharing a TSS (F-078) |
| R-4 | A rule for the 17 chromosome-2 windows with several loci and the 35 untested mitochondrial ones (F-077, F-079) |
| R-5 | A per-record ledger against the historical canonical table: identical, changed, added, or absent, with the reason |

## 8. Current state of legacy artifacts

The legacy `intra` and `intra_strict_dna` CSVs built from the Drive file
(`bhandari-eukaryotic-Plant_promoters-*`) were used only by exploratory EDA
outputs; no classical or CapsProm run references them. They stay preserved,
outside every eligible scope, under their historical names.
