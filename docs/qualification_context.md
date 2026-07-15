# Qualification Thesis Context

This document captures project context extracted from the initial thesis version
located outside the repository at:

```text
C:/Users/lauro/OneDrive/Documents/academic/ufop/doc_tese_v1_0/
```

The source directory is treated as read-only context. This summary should guide
future project specifications, dataset documentation, experiment design, and
thesis writing in the current CapsProm repository.

## Document Structure Observed

The initial thesis version is a modular LaTeX project. The active main file is
`tese-versao.tex`, which currently includes the introduction, materials and
methods, results index, and appendix. Several earlier or article-compilation
chapters remain available but commented in the main file, including basic
concepts, CapsProm, physicochemical-property work, future works, and older
results/conclusion material.

Important context folders include:

- `Intro/`: research context, motivation, objectives, and thesis organization.
- `Main Sections/Methods/`: dataset acquisition, preprocessing, normalization,
  partitioning, and planned feature/model methodology.
- `Main Sections/Results/`: earlier comparative results for CNN and CapsNet.
- `CapsProm/`: chapter wrapper for the 2022 CapsProm article.
- `PhysicochemicalProperties/`: chapter wrapper for the 2023 BRACIS article on
  physicochemical features.
- `FutureWorks/`: planned next steps for unified workflow, baselines,
  attention-enhanced CapsProm, conformal prediction, and thesis completion.
- `Appendix/` and `tables/`: mapping and physicochemical-property reference
  tables relevant to dinucleotide and trinucleotide encodings.

## Research Framing

The initial thesis frames promoter identification as a functional genomic
annotation task. Promoter prediction is modeled as binary classification of DNA
sequence windows into promoter and non-promoter classes. The broader motivation
is the growth of sequencing data and the need for automated, reproducible
computational methods that can support genome annotation.

The stated doctoral direction is to develop and evaluate modern machine learning
approaches for promoter-region prediction in prokaryotic and eukaryotic
organisms. The central modeling hypothesis is that capsule-based neural networks,
possibly enhanced with attention mechanisms, can capture structured sequence
patterns and spatial hierarchies relevant to promoter recognition.

## Prior Contributions to Preserve

The qualification text identifies two prior project contributions that should
remain visible in the current project narrative:

- CapsProm: a capsule-network architecture for promoter prediction, evaluated
  against CNNProm-style convolutional baselines on seven CNNProm datasets.
- Physicochemical-property feature study: an investigation of dinucleotide and
  trinucleotide physicochemical properties as real-valued features for promoter
  classification models.

These contributions define the intellectual starting point for the current
pipeline work. The new repository should not treat the project as beginning from
scratch; it should treat the current pipeline as a reproducible expansion and
consolidation of these prior studies.

## Dataset Context

The initial thesis version identifies four main data sources that match the
current active repository scope:

| Source | Context from the thesis version |
| --- | --- |
| CNNProm / Umarov and Solovyev | Seven benchmark datasets used in the CapsProm work; prokaryotic windows are 81 bp and eukaryotic windows are 251 bp before normalization. |
| GraphPro / Zhang et al. | Multi-species benchmark with 81 bp windows covering human, mouse, and bacterial organisms. |
| Bhandari et al. | Cross-species promoter prediction data, including human, plant, and yeast promoter datasets. |
| CDBProm / Martinez et al. | Bacterial promoter/non-promoter data with promoter windows of 1001 bp and non-promoter windows of 100 bp before normalization. |

The current repository has already narrowed the active experimental scope to the
final intra-source CSV files derived from these sources. Any thesis text created
from this point should use the current validated counts and strict-DNA cleaned
files, while using the initial thesis version for historical and methodological
context.

## Preprocessing Lessons

The initial thesis emphasizes a unified 81 bp representation around the
transcription start site. This remains aligned with the current project choice:
60 bp upstream, the TSS nucleotide, and 20 bp downstream.

The earlier methodology also highlights why this normalization matters:

- It controls input length as a confounding factor.
- It supports direct comparison across heterogeneous source datasets.
- It preserves the core promoter region used by prior CNNProm and GraphPro
  prokaryotic benchmarks.
- It provides a common input shape for feature encoders and neural models.

For the current project, this rationale should be stated carefully: the 81 bp
window is adopted primarily to maintain compatibility with the GraphPro and
CNNProm prokaryotic promoter representation while applying a consistent input
size across all active sources.

## Feature Engineering Lessons

The qualification material and appendix tables reinforce the importance of
representing DNA sequences through more than one feature family. The current
project should preserve at least the following feature directions:

- One-hot or nucleotide-index representations for deep sequence models.
- k-mer frequency representations for classical models and graph-inspired
  baselines.
- Dinucleotide physicochemical features using the normalized 38-property table.
- Trinucleotide physicochemical features using the normalized 12-property table.
- Selectable subsets of physicochemical properties, rather than forcing every
  property into every experiment.
- Feature combination strategies, including flat concatenation for classical
  models and multi-head inputs for deep neural architectures.

This is directly consistent with the current feature architecture implemented in
`src/capsprom/features/`.

## Evaluation Lessons

The earlier work relied on 5-fold cross-validation and binary-classification
metrics such as sensitivity, specificity, accuracy, precision, F1-score, and
Matthews correlation coefficient. MCC remains especially important because many
promoter datasets are class-imbalanced.

The current project should preserve these metrics but make the evaluation more
reproducible and explicit through YAML configurations, fixed dataset manifests,
MLflow tracking, and thesis-ready tables/plots generated from recorded runs.

## Planned Extensions From Qualification Text

The future-work section of the initial thesis identifies several directions that
remain important for this repository:

- Implement a unified end-to-end workflow for preprocessing, training,
  evaluation, and artifact generation.
- Reconduct earlier experiments under one reproducible pipeline.
- Integrate GraphPro and transformer-style baselines where feasible.
- Develop an attention-enhanced CapsProm variant, referred to as A-CapsProm.
- Add conformal prediction to quantify uncertainty in model predictions.
- Add model interpretation analyses, including representation visualization.
- Use MLflow to manage experiment parameters, metrics, artifacts, and
  provenance.

These items should be reflected in the project roadmap as staged work, not as a
single large implementation step.

## Writing Guidance Imported Into Current Project

The initial thesis is already rich in background and motivation. The current
repository should use it to avoid rewriting the conceptual foundation from zero,
but new thesis sections must be updated to reflect the stricter current data
scope and reproducible pipeline decisions.

Important writing rules for this repository remain:

- Do not leave any table, figure, chart, or diagram without a preceding textual
  reference, a descriptive caption, and a stable label.
- Distinguish source provenance from active experimental scope.
- Distinguish inherited filename tags from biological taxonomy when necessary.
- Use final strict-DNA cleaned counts when reporting model-ready datasets.
- Keep feature reference files separate from dataset source descriptions.

## Practical Implications for Next Work

The current project should prioritize the pipeline and reporting layer before
new model complexity. The qualification text supports the following immediate
order:

1. Finish dataset manifests and preprocessing documentation for the active
   intra-source datasets.
2. Implement repeatable experiment execution from YAML configuration.
3. Track all runs and dataset provenance in MLflow.
4. Reproduce core baselines under the unified pipeline.
5. Add feature-combination experiments for k-mer, one-hot, and selected
   physicochemical properties.
6. Only then expand toward CapsProm variants, attention mechanisms, conformal
   prediction, and interpretability analyses.
