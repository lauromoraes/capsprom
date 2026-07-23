# Feature-Oriented EDA Report

This report summarizes exploratory analyses for the final intra-source datasets used in the CapsProm project. The goal is to characterize the candidate DNA feature families before model training and to identify interpretable patterns that can motivate later ablation studies.

Table `tab:eda-dataset-summary` should be used to introduce the dataset-level consistency summary. It reports sample counts, class balance, strict DNA validity, and sequence-length consistency.

- Input directory: `data/processed/assembled_datasets/intra`
- Output directory: `outputs/eda/intra_feature_exploration`
- Dataset files analyzed: 58
- Valid sequences analyzed: 1828924
- Feature-level sample per label: 1000
- K-mer sizes analyzed: 2, 3, 4

Table `tab:eda-gc-summary` should be used to discuss global compositional descriptors by class. GC content, GC skew, and AT skew are directly interpretable because they are computed from nucleotide counts.

- GC/skew summary rows: 348

Table `tab:eda-top-kmer-differences` should be used to discuss explicit lexical signals. The reported k-mers are ranked by the absolute difference between promoter and non-promoter frequencies.

- Top k-mer rows: 3828

Table `tab:eda-physicochemical-summary` should be used to discuss biologically informed feature behavior. Each row summarizes a selected normalized physicochemical property after averaging it over sequence positions.

- Physicochemical summary rows: 580

All generated tables require a preceding textual introduction, a stable label, and a descriptive caption before being incorporated into the thesis.
