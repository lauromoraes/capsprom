# Configuration Files

Experiment configuration files are written in YAML and should be treated as
part of the scientific record. A configuration file must contain enough
information to reproduce a run, compare it with other runs, and connect its
outputs to the doctoral thesis.

`example_experiment.yaml` describes the broader target architecture and includes
features and models beyond the current executable boundary.

`mvp_logistic.yaml` is the executable restart milestone. It runs a deterministic
sampled logistic-regression experiment using 3-mer frequency and GC/skew
features, with local SQLite-backed MLflow tracking. Validate and run it with:

```bash
PYTHONPATH=src python -m capsprom validate-config configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom validate-data configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom audit-data configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom run configs/mvp_logistic.yaml
```

`full_logistic.yaml` promotes the same fixed experimental contract to every
record in the Bhandari human promoter train/test split. It deliberately changes
only the sample limits and MLflow experiment name:

```bash
PYTHONPATH=src python -m capsprom run configs/full_logistic.yaml
```

`full_xgboost.yaml` is the first comparative nonlinear baseline. It preserves
the full logistic-regression data and feature contract while changing only the
model family and its explicit hyperparameters:

```bash
PYTHONPATH=src python -m capsprom run configs/full_xgboost.yaml
```

`evaluation_protocol.yaml` is the machine-readable statistical contract for
future confirmatory experiments. It is marked `partially_implemented`: the
current CLI persists predictions, metrics, calibration summaries, data audits,
and fold manifests, but it does not yet execute repeated-seed orchestration,
paired resampling, or cross-dataset comparisons.

`leakage_controlled_logistic.yaml` and
`leakage_controlled_xgboost.yaml` use the deduplicated, group-split Bhandari
human shuffle-control dataset. They replace the contaminated Bhandari human
split for current development experiments.

`real_negative_smoke_logistic.yaml` and
`real_negative_smoke_xgboost.yaml` exercise the canonical v3 GraphPro
`clostridium_phytofermentans` pair. They are explicitly exploratory integration
checks and must not be treated as confirmatory model comparisons.

Dataset-pair integrity auditing is independent of a model configuration. Audit
the canonical strict-DNA CDBProm, CNNProm, and GraphPro pairs with:

```bash
PYTHONPATH=src python -m capsprom audit-datasets \
  data/processed/assembled_datasets/intra_regenerated_v3_strict_dna \
  data/processed/audits/real_negative_regenerated_v3
```

The command writes JSON, CSV, and Markdown reports with deterministic input
hashes and strict eligibility classifications.
