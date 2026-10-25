# Project Specification

## Objective

Build a reproducible doctoral research codebase for promoter region prediction
using capsule networks, with rigorous experiment tracking, statistical
evaluation, and thesis-oriented documentation.

## Dataset Contract

Current confirmatory source-negative scope is restricted to the 18 CDBProm and
CNNProm identities selected by
`configs/dataset_eligibility_manifest_v1.yaml` from the canonical CSV files in
`data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/`. The
original `intra/`, legacy `intra_strict_dna/`, regenerated v1, and regenerated
v2 files are preserved for provenance and preprocessing audit. Bhandari remains
a separately declared shuffle-control workflow. Generated project information
must not treat legacy files as active confirmatory datasets.

The fixed CDBProm, CNNProm, and GraphPro strict-DNA partitions are development
inputs only until corrected group-safe versions are generated. The batch audit
identified internal exact duplicates and train/test overlap in all 26 pairs,
with label conflicts in four pairs. These sources retain their original
non-promoter examples; their correction must not introduce synthetic negatives.
Regeneration after correcting append-mode cropped FASTA writes reduces combined
test-row overlap from 98.09% to 2.17% and makes 9 pairs strictly eligible. The
mandatory post-crop collision filter then removes all 1,348 conflicting
sequences from both classes (2,696 rows), produces zero label conflicts, and
makes 10 pairs strictly eligible before deduplication. The canonical v3 build
then removes 301 positive and 759 negative same-label duplicate rows, applies
the strict-DNA filter, and creates deterministic unique-sequence group splits.
All 26 pairs pass the final exact-identity audit, but exact cleanliness is not
sufficient evidence that source labels have the intended biological meaning.
All eight GraphPro pairs are excluded from confirmatory inference. Five
bacterial folders have class labels perfectly confounded with FASTA strand,
GraphPro E. coli contains 1,345 raw records in both classes, and 535 GraphPro
Bacillus negatives match canonical windows of CDBProm positive regions. The
legacy `Cpne` mapping to Clostridium phytofermentans was also incorrect;
accession NC_000922.1 and the raw headers identify Chlamydophila pneumoniae.
Historical GraphPro artifacts remain exploratory provenance and must not be
silently relabeled or reused by the revised confirmatory contract.

Primary-source comparison further established that the 278-row Promotech
`ECOLI.bed` is an ordered copy of the pAA plasmid TSS supplement from PMID
27748404. Its declared `NC_000913.3` contig is incorrect: all published 51-nt
windows match `NC_018666.1`. Therefore, every reconstructed candidate, control,
split, distribution statistic, and dependency result derived by applying these
coordinates to MG1655 is invalidated. The source BED is preserved unchanged;
future reconstruction uses a new pAA-specific identity and fresh hashes.

The Bhandari human promoter dataset is an explicit exception. Its legacy split
contains extensive exact-sequence duplication and train/test overlap. Current
Bhandari human experiments must use
`data/processed/leakage_controlled/bhandari_human_shuffle_v1/`, whose positive
windows are deduplicated before one deterministic shuffled negative is generated
per positive and whose positive--negative groups are assigned wholly to train or
test. This dataset is a synthetic-negative shuffle control and must be labeled
accordingly; it does not replace evaluation against genomic non-promoters.

Alternative negative definitions are governed by
`specs/negative_control_protocol.md`. Source-native, GC-matched genomic,
synthetic-shuffle, CDS-derived, and multi-negative training conditions retain
separate identities and test panels. They must not be concatenated into one
reported task or selected using held-out model outcomes.


Datasets must be CSV files with exactly the following required semantic fields:

| Field | Description |
| --- | --- |
| `sequence` | DNA nucleotide sequence normalized to 81 bp |
| `label` | Binary class label: `0` for non-promoter, `1` for promoter |

Validation requirements:

- Every sequence must have length 81.
- Every sequence must use only `A`, `C`, `G`, and `T`.
- Labels must be binary.
- Dataset partitions must be explicit in the filename or configuration.
- Positive and negative counts should be recoverable from the filename when
  the naming convention is used.
- Same-label exact duplicates must be removed before confirmatory partitioning.
- Exact sequence groups must not cross the train/test boundary.
- Identical post-crop sequences with conflicting labels must always be removed
  from both classes before partitioning.
- Every filtering stage must record input counts, rows removed by class, output
  counts, application order, and output hashes in JSON and flat CSV manifests.
- Released GraphPro labels remain exploratory. Any reinstatement follows
  `specs/graphpro_dataset_reconstruction.md`, creates a new derived dataset
  identity, and passes eligibility independently for each organism.

Dataset naming convention:

```text
[study]-[organism]-[dataset_name]-p-[count]-n-[count]-[partition].csv
```

## Feature Engineering Requirements

Supported encodings:

- K-mer frequency vectors for 1-mers through 6-mers.
- One-hot encoding applied to 1-mer through 6-mer representations.
- Physicochemical property vectors for dinucleotides and trinucleotides.
- DNA-BERT embeddings.

The normalized physicochemical reference files are canonical inputs for these
encodings:

- `data/raw/references/normalized-dinuc.tsv` for dinucleotide properties.
- `data/raw/references/normalized-trinuc.tsv` for trinucleotide properties.

Physicochemical encoders must support selecting all properties or a named
subset of properties from the relevant reference file.

The implementation should expose encoders through a common interface so that
models and experiments can switch encodings through YAML configuration.
Experiments must also support feature combinations. Classical models may
receive flattened concatenated feature vectors, while deep neural networks must
be able to receive named feature blocks as independent inputs for multi-head or
multi-branch architectures before feature fusion.

## Model Requirements

Baseline models:

- XGBoost.
- CNNProm.
- iPro-MP.
- EDEN.
- Fine-tuned DNA-BERT.

Proposed models:

- CapsProm.
- SparseCapsProm.

## Experiment Requirements

Experiments must measure:

- Effectiveness.
- Efficiency.
- Robustness.
- Statistical significance where appropriate.

The confirmatory metric, resampling, calibration, replication, and statistical
comparison rules are defined in `specs/statistical_evaluation_protocol.md` and
mirrored in `configs/evaluation_protocol.yaml`. Development runs whose test
results have already informed project decisions must be labeled exploratory and
must not be presented as blind confirmatory evidence.

## Tracking Requirements

MLflow must record:

- Dataset identity and partition metadata.
- Configuration file used for the run.
- Model family and implementation version.
- Feature encoding settings.
- Hyperparameters.
- Metrics.
- Plots and figures.
- Model artifacts when appropriate.

## Configuration Requirements

Experiments must be launched from YAML configuration files. The configuration
schema must be strict enough to make runs reproducible and comparable.

## CLI Requirements

The repository must provide a CLI that can:

- Validate a configuration file.
- Validate datasets.
- Execute an experiment workflow.
- Write outputs and MLflow artifacts in predictable locations.

## Documentation Requirements

All documentation, code, comments, and configuration files must be in English.
Scholarly outputs should be prepared as LaTeX snippets with notes indicating
where they fit in the doctoral thesis. No figure, table, chart, diagram, or
visual artifact may be included without a descriptive caption, a stable label,
and a preceding textual reference in the surrounding text.
