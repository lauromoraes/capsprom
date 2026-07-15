# Roadmap

## Phase 0: Project Foundation

Status: in progress.

Goals:

- Define the canonical project specification.
- Establish repository organization.
- Create an AI-oriented project skill.
- Add a first YAML experiment example.

Exit criteria:

- The repository has clear documentation for scope, constraints, and next
  development steps.

## Phase 1: Pipeline Design

Status: planned.

Goals:

- Use `docs/qualification_context.md` to preserve the methodological continuity
  between the qualification thesis and the current reproducible pipeline.
- Define the minimum viable experiment pipeline.
- Specify dataset validation rules.
- Specify configuration schema.
- Decide how MLflow run metadata and artifacts will be organized.

Exit criteria:

- A pipeline specification exists before implementation.
- The user has reviewed the assumptions.

## Phase 2: Data and Encoding Layer

Status: planned.

Goals:

- Implement dataset loading and validation.
- Implement sequence normalization checks.
- Implement k-mer frequency encodings.
- Implement one-hot encodings for k-mer representations.
- Define interfaces for physicochemical vectors and DNA-BERT embeddings.

Exit criteria:

- Encoders are independently testable.
- Invalid datasets fail with clear errors.

## Phase 3: Baselines

Status: planned.

Goals:

- Implement or integrate baseline models in a controlled way.
- Track all baseline runs in MLflow.
- Define fair comparison conditions.

Exit criteria:

- Baseline results are reproducible from YAML configuration files.

## Phase 4: CapsProm Models

Status: planned.

Goals:

- Reproduce the original CapsProm direction under the unified pipeline.
- Implement CapsProm.
- Implement SparseCapsProm.
- Plan the attention-enhanced A-CapsProm extension after baseline reproduction.
- Add hyperparameter optimization.
- Compare against baselines using the same pipeline.

Exit criteria:

- Proposed models can be evaluated under reproducible, statistically sound
  conditions.

## Phase 5: Interpretability and Thesis Artifacts

Status: planned.

Goals:

- Relate learned patterns to candidate motifs and biological concepts.
- Generate plots, tables, and LaTeX snippets.
- Document where each artifact belongs in the thesis.

Exit criteria:

- Experimental outputs can be directly reused in doctoral writing.
