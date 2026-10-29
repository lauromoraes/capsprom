# Dataset Integrity Audit

## Purpose

Before a source-provided promoter/non-promoter dataset is admitted to baseline
or confirmatory experiments, its fixed train/test pair must pass a reproducible
sequence-integrity audit. The audit is independent of model configuration and
uses normalized uppercase DNA sequences as the identity key.

## Scope

The first batch audit covers the strict-DNA CDBProm, CNNProm, and GraphPro CSV
files under `data/processed/assembled_datasets/intra_strict_dna/`. Bhandari is
excluded because its promoter-only source and synthetic-negative correction are
specified separately.

## Pair Discovery

Files must follow the project naming convention and end in either `-train.csv`
or `-test.csv`. A dataset identity consists of source, domain, and dataset name.
Exactly one train and one test file must exist for each identity.

## Measurements

For each pair, record:

- train and test rows, class counts, unique sequences, and SHA-256 hashes;
- duplicate rows within each partition;
- sequences associated with conflicting labels within either partition;
- exact sequences shared between train and test;
- train and test rows belonging to shared sequences;
- shared sequences with conflicting labels;
- overlap counts separated by positive and negative label when labels agree.

## Eligibility Rules

Dataset construction must remove cross-label collisions before train/test
partitioning. After cropping and sequence normalization, let (C) be the set of
sequences observed with both labels. Every occurrence whose sequence belongs to
(C) is removed from both classes. Keeping one label would require an
unsupported relabeling decision and is therefore not permitted. A filtering
manifest must record the input, removed, and remaining row counts for every
dataset at cropping, collision removal, partitioning, and strict-DNA filtering.

A pair is `eligible` only when it contains both classes in both partitions and
has zero internal duplicate rows, zero label conflicts, and zero exact
train/test overlap. Otherwise it is classified as:

- `invalid`: the CSV contract, pairing contract, alphabet, length, or labels
  cannot be validated;
- `conflicting_labels`: one or more normalized sequences have inconsistent
  labels;
- `train_test_overlap`: exact sequences cross the partition boundary;
- `internal_duplicates`: duplicate rows occur within a partition but not across
  partitions.

The classifications are ordered by severity as listed above. A non-eligible
pair must not enter a confirmatory experiment until a source-aware correction
and a new immutable manifest are defined.

## Length exclusion

A record whose length differs from its dataset's declared window is excluded,
never cropped, padded, or truncated to fit, because its anchor (the TSS for
promoters, the sampling rule for negatives) is then unknown. The rule is
declared per dataset in its build config before any build or model result is
seen:

- `expected_length` per source class, taken from the release declaration in
  `configs/source_canonicalization_v1.yaml`, never from the modal length of the
  data;
- the action, always `exclude` in version 1;
- the documented reason for each known deviation, with its finding ID.

The filtering ledger records, per dataset and class, the input count, every
excluded `record_id` with its length and reason, and the output count. A
deviation without a documented reason is still excluded, but it is reported as
`undocumented_length` and requires a findings-register entry before the build
is accepted.

Known deviations:

| Collections | Class | Deviation | Reason | Findings |
| --- | --- | --- | --- | --- |
| `bhandari-human` | positive | 30 records, 302 to 921 nt | window truncated on hg38 alternate contigs | F-031, F-032 |
| `bhandari-yeast` | positive | 3 records, 352, 732, 884 nt | window truncated at a chromosome end | F-031, F-032 |
| `bhandari-nominal-plant` | positive | 5 records, 306 (2), 334, 344, 801 nt | window truncated on mm10 unplaced or random contigs | F-037 |
| `bhandari-human-random-genomic` | negative | 6 records, 970 to 998 nt | each is an entire hg38 unplaced scaffold shorter than 1,000 nt | F-038 |
| `cdbprom-anabaena-sp`, `cdbprom-bacillus-amyloliquefaciens`, `cdbprom-corynebacterium-glutamicum`, `cdbprom-helicobacter-pylori`, `cdbprom-klebisiella-pneumoniae`, `cdbprom-mycrobacterium-tuberculosis`, `cdbprom-pseudonomas-aeruginosa`, `cdbprom-salmonella-typhimurium`, `cdbprom-streptomyces-coelicolor`, `cdbprom-synechocistis` | negative | 51 records, 99 nt | probable off-by-one in the authors' sampling | F-034, F-035 |
| `graphpro-lint` | positive, negative | 1 + 1 records, 82 nt | undocumented | F-039 |
| `promotech-cpneumoniae` | positive | 1 record, 1 nt | undocumented | F-019 |

This table is the complete list for `can-v1` (log R-017). It is checked
against the generated record
`manifests/provenance/source_acquisition_v1/length_deviations.json`
(`record_provenance.py length-deviations`) by
`tests/test_provenance.py`: a deviating collection missing from the table,
or a table entry without a deviation, fails the test.

Existing builders that use `keep_most_common_length` or
`normalize_to_min_length` (F-036) do not meet this rule. Their outputs remain
valid provenance for completed experiments. A new build version applies the
rule above, and its ledger must reproduce the counts in this table.

## Artifacts

The build command writes JSON and CSV filtering manifests plus a build report.
The batch audit then writes a machine-readable JSON report, a flat CSV summary,
and a Markdown report with the criteria, aggregate counts, and one row per
dataset. The report records a deterministic audit identifier derived from the
input file hashes and audit settings.
