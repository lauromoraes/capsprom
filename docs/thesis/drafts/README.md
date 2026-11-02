# Thesis Drafts

Staging area for text intended for the final thesis. Drafts are written in
English, cite only DOI-checked references, and are promoted into
`docs/thesis/chapters/` after review.

## Layout

- `main.tex` compiles every draft into one report.
- `sections/<topic>.tex` holds one draft each. Every draft opens with a
  `\draftmeta{target}{status}{project sources}` box.
- `references.bib` holds the draft bibliography. Entries move into
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
| `sections/tss_class_selection.tex` | Ch. 4 (dataset reconstruction); summary in Ch. 7 | draft v1, references verified; P+S rule awaits owner approval | `specs/graphpro_dataset_reconstruction.md`, log R-035, F-115 to F-117 |
