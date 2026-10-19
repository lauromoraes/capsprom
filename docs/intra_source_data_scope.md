# Intra-Source Dataset Scope

For confirmatory experiments using source-provided non-promoters, the active
model-ready directory is:

```text
data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/
```

The original processed directory is preserved for provenance and preprocessing audit:

```text
data/processed/assembled_datasets/intra/
```

The legacy strict-DNA directory is also retained for provenance and audit:

```text
data/processed/assembled_datasets/intra_strict_dna/
```

Bhandari shuffle controls remain in their separately declared leakage-controlled
directory. All dataset processing notes, validation summaries, and
thesis-oriented text must distinguish active and legacy scopes.

## Included Sources

The source inventory contains four source groups:

| Source prefix | Final CSV files | Scope |
| --- | ---: | --- |
| `bhandari` | 6 | Human, plant, and yeast promoter datasets, all represented with biologically consistent eukaryotic filename tags where applicable. |
| `cdbprom` | 22 | Prokaryotic promoter datasets |
| `cnnprom` | 14 | Eukaryotic and prokaryotic CNNProm benchmark datasets |
| `graphpro` | 16 | Eukaryotic and prokaryotic GraphPro benchmark datasets |

The canonical source-negative scope contains 52 CSV files representing 26
train/test pairs. Bhandari datasets are counted separately.


## Active Source Provenance

The README files in the active raw source folders document the source
publications, repositories, and selected methodological notes used to obtain the
data. The consolidated summary is maintained in `docs/source_provenance.md`.
These README-derived notes are part of the project context, but they do not
expand the active data scope beyond the canonical source-negative and declared
Bhandari control directories.

## Excluded Data

Other files or folders that may exist under `data/` are not part of the current
intra-source dataset scope. This includes exploratory archives, unrelated raw
sources, previous prediction outputs, and datasets not represented in the
canonical source-negative or explicitly declared Bhandari control directories.

Excluded examples include:

- `data/raw/iPro-MP/`
- `data/raw/EDP/`
- `data/raw/Fuitfly/`
- `data/raw/Nova pasta/`
- `data/raw/Nova pasta (2)/`

These files should not be described as part of the active experimental dataset
unless a future specification explicitly includes them and new processed outputs
are generated.

## Reference Tables

The physicochemical reference files under `data/raw/references/` are feature
encoding references, not source datasets. They remain valid for feature
construction but should be described separately from the dataset source scope.
