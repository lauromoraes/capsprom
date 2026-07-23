# Active Source Provenance

This document summarizes the provenance information recorded in the README files
of the four active raw data sources used to create the final intra-source CSV
datasets in `data/processed/assembled_datasets/intra/` and their strict-DNA model-ready copies in `data/processed/assembled_datasets/intra_strict_dna/`.

## Scope

Only sources represented in the final intra-source datasets are included:

- Bhandari et al.
- CDBProm
- CNNProm
- GraphPro

Other raw folders are outside the active dataset scope.

## Source Summary

The table below consolidates the source-level provenance recorded in the raw
folder README files. These notes should be used when describing data origin in
the thesis, while the exact experimental sample counts should continue to come
from the final intra-source CSV files and their strict-DNA cleaned copies.

| Source | Publication or resource described in README | Origin URL or repository | README-level methodological notes |
| --- | --- | --- | --- |
| Bhandari et al. | "Comparison of machine learning and deep learning techniques in promoter prediction across diverse species" by Bhandari, Khare, Walambe, and Kotecha; PeerJ Computer Science, 2021 | Google Drive dataset link recorded in `data/raw/Bhandari_etal/README` | The README identifies this folder as the data associated with a cross-species promoter prediction study. |
| CDBProm | "CDBProm: the Comprehensive Directory of Bacterial Promoters" by Martinez et al.; NAR Genomics and Bioinformatics, 2024 | CDBProm website and `training_sequences.zip` URL recorded in `data/raw/CDBProm/README` | The README identifies bacterial and eukaryotic promoter/non-promoter sequences from the CDBProm resource; only subsets represented in the final intra-source CSV files are active here. |
| CNNProm | "Recognition of Prokaryotic and Eukaryotic Promoters Using Convolutional Deep Learning Neural Networks" by Umarov and Solovyev; PLOS One, 2016 | CNNPromoterData GitHub repository and Softberry website recorded in `data/raw/CNNProm/README` | The README states that bacterial non-promoters were sampled from protein-coding genes on the opposite strand; E. coli sigma-70 promoters came from RegulonDB; Bacillus subtilis promoters came from DBTBS; eukaryotic promoters came from EPDnew; and an additional mouse TATA set came from DBTSS. |
| GraphPro | "GraphPro: An interpretable graph neural network-based model for identifying promoters in multiple species" by Zhang, Wei, and Liu; Computers in Biology and Medicine, 2024 | GraphPro GitHub repository dataset folder recorded in `data/raw/GraphPro/README` | The README lists eukaryotic human and mouse datasets and bacterial datasets for Escherichia coli, Campylobacter jejuni, Bacillus amyloliquefaciens, Clostridium phytofermentans, Rhodobacter capsulatus, and Leptospira interrogans. |

## Source-Specific Notes for Thesis Text

The Bhandari et al. README connects the raw files to a comparative promoter
prediction study spanning diverse species. In this project, the Bhandari files
are treated as one active source group only when they appear in the final
intra-source dataset directory.

The CDBProm README records the source as the CDBProm resource and its associated
training-sequence archive. This provenance is relevant for bacterial promoter
prediction experiments, but the active scope remains the final intra-source
CSV representation rather than the complete upstream resource.

The CNNProm README provides the most detailed origin notes. It documents
different upstream resources for prokaryotic and eukaryotic data and describes
the construction of bacterial non-promoters from opposite-strand coding
fragments. This distinction should be mentioned when discussing possible
source-specific biases or differences in negative-set construction.

The GraphPro README records a multi-species benchmark organized into eukaryotic
and bacterial groups. Its organism list is useful when describing the biological
coverage of the active GraphPro-derived intra-source datasets.

## Thesis Usage

Use this provenance information when describing the active data sources, but keep
it distinct from feature reference files such as `normalized-dinuc.tsv` and
`normalized-trinuc.tsv`, which are encoding references rather than dataset
sources.
