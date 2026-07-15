# Thesis LaTeX Structure

This directory contains the modular LaTeX structure for the CapsProm doctoral
thesis. It is based on the qualification thesis context summarized in
`docs/qualification_context.md`, but it is organized as a reproducible final
thesis project rather than as a qualification/article-compilation document.

## Entry Point

Compile from:

```text
docs/thesis/main.tex
```

## Organization

- `main.tex`: thesis entry point.
- `preamble/`: packages, metadata, and reusable commands.
- `frontmatter/`: title page, abstracts, acknowledgements, acronyms.
- `chapters/`: one file per thesis chapter.
- `appendices/`: appendix entry point and appendix sections.
- `figures/`: thesis figures generated or curated for LaTeX.
- `tables/`: thesis tables generated or curated for LaTeX.
- `dataset_processing_latex.tex`: active dataset preprocessing section already
  prepared from the current reproducible data pipeline.
- `references.bib`: thesis bibliography file.

## Writing Rules

Every figure, table, chart, diagram, or visual artifact must be introduced in
text before it appears, must have a descriptive caption, and must have a stable
LaTeX label. This is a project-wide rule and applies to every chapter.

The active experimental dataset scope must remain restricted to the final
intra-source datasets and their strict-DNA cleaned copies unless a future
specification explicitly expands the scope.
