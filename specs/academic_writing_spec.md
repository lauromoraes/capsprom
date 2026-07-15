# Academic Writing Specification

## Objective

Academic outputs in this repository must be thesis-ready, traceable to the
experimental pipeline, and internally coherent. This applies to Markdown notes,
LaTeX snippets, generated tables, plots, diagrams, and any text intended for the
doctoral thesis.

## Figure and Table Reference Rule

No figure, table, chart, diagram, or other floating visual artifact may appear
without being introduced and referenced in the surrounding text.

Every figure or table must have:

- A descriptive caption explaining what the reader should understand from it.
- A stable `\label{...}`.
- At least one preceding textual reference using `Figure~\ref{...}` or
  `Table~\ref{...}` before the artifact appears.
- Enough surrounding explanation that the artifact is not interpreted as a
  standalone decoration.

This rule applies to:

- LaTeX tables and figures.
- TikZ diagrams and flowcharts.
- Exported plots and charts.
- Result tables generated from experiments.
- Any thesis-oriented visual or tabular artifact.

## Quality Check

Before finalizing a thesis-oriented document, verify that:

- Every `figure` environment has a preceding textual reference, caption, and
  label.
- Every `table` environment has a preceding textual reference, caption, and
  label.
- Captions describe the analytical purpose of the artifact, not only its title.
- Text explains how the artifact supports the argument or methodology.
