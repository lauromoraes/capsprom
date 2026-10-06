# Full-Dataset Logistic Regression Report

## Purpose

This experiment promotes the restart sanity check to the complete strict-DNA
Bhandari human promoter split. It retains the same dataset partitions, feature
blocks, classifier, hyperparameters, random seed, metrics, and provenance
contract used by the sampled MVP. Only the sample limits were removed.

## Experimental Setup

The model was trained on all 393,513 training records and evaluated once on all
98,375 records in the fixed test partition. Each 81-nucleotide sequence was
represented by 64 normalized 3-mer frequencies, global GC content, and global
GC skew, producing 66 input features. Batched encoding materialized compact
`float32` matrices of 99.07 MiB for training and 24.77 MiB for testing.

The exact configuration is stored in `configs/full_logistic.yaml`. Dataset
SHA-256 hashes, configuration, sample counts, feature metadata, timings,
metrics, run summary, and fitted model were recorded in the local
SQLite-backed MLflow experiment `capsprom-baselines`. The run identifier was
`072d1e1db0e846678bdffd4de43ce8fc`.

## Full-Dataset Results

Table `tab:full-logistic-results` reports the complete fixed-split evaluation.
These values establish the first full-data pipeline reference point. A later
exact-sequence audit found that 49.87% of test rows belong to sequences also
present in training. The values must therefore be treated as potentially
optimistic legacy-split development results, not as independent generalization
estimates or confirmatory evidence. See `docs/bhandari_human_data_audit.md`.

| Metric | Value |
| --- | ---: |
| Accuracy | 0.7807 |
| Precision | 0.7803 |
| Recall | 0.7813 |
| F1 | 0.7808 |
| ROC-AUC | 0.8628 |
| Matthews correlation coefficient | 0.5613 |
| Feature encoding time | 13.9852 s |
| Model training time | 5.3647 s |

Table label: `tab:full-logistic-results`.

## Comparison with the Restart Sample

Table `tab:sample-versus-full-logistic` compares the infrastructure sample with
the full-data run. The full-data model improved every effectiveness metric,
while preserving the same feature and model contract.

| Metric | Sampled MVP | Full dataset | Difference |
| --- | ---: | ---: | ---: |
| Accuracy | 0.7635 | 0.7807 | +0.0172 |
| Precision | 0.7692 | 0.7803 | +0.0111 |
| Recall | 0.7530 | 0.7813 | +0.0283 |
| F1 | 0.7610 | 0.7808 | +0.0198 |
| ROC-AUC | 0.8476 | 0.8628 | +0.0152 |
| Matthews correlation coefficient | 0.5271 | 0.5613 | +0.0342 |

Table label: `tab:sample-versus-full-logistic`.

## Interpretation and Next Gate

The result confirms that the complete dataset can be processed efficiently, but
the audited partition does not provide an independent test of generalization.
The next valid effectiveness comparison requires a deterministic group-aware
split with zero exact-sequence overlap. Repeated seeds, calibration, confidence
intervals, and formal paired comparisons follow only after that correction.
