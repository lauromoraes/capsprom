# Intra-Source Dataset Scope

This project currently considers only the data that was used to create the final
intra-source processed datasets located in:

```text
data/processed/assembled_datasets/intra/
```

All dataset processing notes, validation summaries, and thesis-oriented text
must reflect this scope unless a future experiment explicitly expands it.

## Included Sources

The final intra-source CSV files come from four source groups:

| Source prefix | Final CSV files | Scope |
| --- | ---: | --- |
| `bhandari` | 6 | Human, plant, and yeast promoter datasets, all represented with biologically consistent eukaryotic filename tags where applicable. |
| `cdbprom` | 22 | Prokaryotic promoter datasets |
| `cnnprom` | 14 | Eukaryotic and prokaryotic CNNProm benchmark datasets |
| `graphpro` | 16 | Eukaryotic and prokaryotic GraphPro benchmark datasets |

Total final intra-source CSV files: 58.


## Active Source Provenance

The README files in the active raw source folders document the source
publications, repositories, and selected methodological notes used to obtain the
data. The consolidated summary is maintained in `docs/source_provenance.md`.
These README-derived notes are part of the project context, but they do not
expand the active data scope beyond the final intra-source CSV files.

## Excluded Data

Other files or folders that may exist under `data/` are not part of the current
intra-source dataset scope. This includes exploratory archives, unrelated raw
sources, previous prediction outputs, and datasets not represented in
`data/processed/assembled_datasets/intra/`.

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
