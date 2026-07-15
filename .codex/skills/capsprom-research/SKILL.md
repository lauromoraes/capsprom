---
name: capsprom-research
description: Project-specific guidance for working on the CapsProm doctoral research codebase.
---

# CapsProm Research Skill

Use this skill when working inside the CapsProm repository.

## Project Identity

CapsProm is a doctoral research project for promoter region prediction from DNA
sequences using capsule networks and reproducible machine learning pipelines.

## Non-Negotiable Constraints

- Write all documentation, source code, comments, configuration files, and
  experiment notes in English.
- Treat reproducibility as a research requirement, not an implementation detail.
- Prefer incremental pipeline development over premature model complexity.
- Keep thesis relevance explicit when creating reports, plots, tables, or LaTeX
  snippets.
- Never leave a figure, table, chart, diagram, or other visual artifact without
  a descriptive caption, a stable label, and a preceding textual reference.
- Use YAML configuration files for experiments.
- Use MLflow for experiment tracking.

## Recommended Work Order

1. Confirm the relevant specification in `specs/`.
2. Update or create the smallest useful design note before implementing a new
   pipeline stage.
3. Add or update configuration examples when behavior changes.
4. Implement one pipeline stage at a time.
5. Add focused tests around data validation, encoders, metrics, and tracking.
6. Document experiment outputs in a thesis-oriented format.

## Repository References

- `specs/project_spec.md`: canonical project requirements.
- `specs/pipeline_mvp.md`: first pipeline implementation target.
- `docs/project_brief.md`: research summary and assumptions.
- `docs/roadmap.md`: phased development plan.
- `configs/example_experiment.yaml`: initial experiment configuration shape.
- `specs/academic_writing_spec.md`: thesis writing rules, including mandatory
  figure/table introduction and references.

## Engineering Preferences

- Keep modules small and explicit.
- Validate biological assumptions early.
- Make dataset and run provenance visible in MLflow.
- Avoid hidden defaults in experiments.
- Prefer clear failure messages over permissive behavior.
