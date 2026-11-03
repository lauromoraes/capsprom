# Thesis Drafts

Staging area for text intended for the final thesis. Drafts are written in
English, cite only DOI-checked references, and are promoted into
`docs/thesis/chapters/` after review.

## Layout

- `main.tex` compiles every draft into one report.
- `sections/<topic>.tex` holds one draft each. Every draft opens with a
  `\draftmeta{target}{status}{project sources}` box.
- `draft_references.bib` holds the draft bibliography. Entries move into
  `docs/thesis/references.bib` when their draft is promoted.

Build (output goes to the ignored `build/` folder):

```bash
cd docs/thesis/drafts && latexmk -pdf -outdir=build main.tex
```

## Workflow

1. Add `sections/<topic>.tex` and an `\input` line in `main.tex`.
2. Register it in the index below.
3. Promote: move the text into its target chapter, merge its bib entries,
   and mark the row `promoted`.

## Index

| Draft | Target | Status | Project sources |
| --- | --- | --- | --- |
| `sections/tss_class_selection.tex` | Ch. 4 (dataset reconstruction); summary in Ch. 7 | draft v1, references verified; rule approved (log R-039, R-042) | `specs/graphpro_dataset_reconstruction.md`, log R-035, R-039, R-042, F-115 to F-118 |
| `sections/control_exclusion_radius.tex` | Ch. 4 (negative construction); one sentence in Ch. 7 | draft v1, references verified | log R-036, `specs/sequence_window_policy.md`, F-117 |
| `sections/evaluation_design.tex` | Ch. 7 (replication and inference) | draft v1, references verified; group-aware folds await evaluation protocol v4 | `specs/statistical_evaluation_protocol.md`, `specs/homology_grouping_protocol.md` |
| `sections/paa_provenance_case.tex` | Ch. 4 (provenance) or Ch. 9 (discussion) | draft v1, references verified; exclusion decided (log R-040) | `docs/graphpro_derived_artifact_impact.md`, log R-040, F-013, F-115, F-117 |

## Bibliography

`draft_references.bib` holds only entries new to the thesis. `main.tex` also reads
`../references.bib` (found through `BIBINPUTS` in `.latexmkrc`), so thesis keys (e.g. `dietterich1998approximate`,
`kapoor2023leakage`) are cited directly. On 2026-11-02 no key or DOI in the
draft bibliography duplicated an entry of the thesis bibliography.
