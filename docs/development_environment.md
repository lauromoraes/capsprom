# Development Environment

This project uses a local virtual environment at the repository root:

```bash
.venv/
```

## Create or Recreate the Environment

The current environment was created with Python 3.13.11 from the WSL Python
installation (base interpreter `~/miniconda3/bin/python3.13`):

```bash
/home/lauro/miniconda3/bin/python3.13 -m venv --clear .venv
.venv/bin/python -m pip install --upgrade pip
```


## Install Project Dependencies

Install the core stack for EDA, feature engineering, plotting, classical
machine-learning utilities, and MLflow tracking with:

```bash
source .venv/bin/activate
python -m pip install -r requirements/base.txt
```

For development and validation tools, install:

```bash
python -m pip install -r requirements/dev.txt
python -m pip install --no-deps --no-build-isolation -e .
```

XGBoost is kept in a separate optional file because its Linux wheel may download
large binary dependencies:

```bash
python -m pip install -r requirements/models-classical.txt
```

DNA-BERT feature extraction can be prepared with the CPU-oriented dependency group:

```bash
python -m pip install -r requirements/dna-bert-cpu.txt
```

The current validated setup loads `zhihan1996/DNA_bert_6` with PyTorch CPU and
produces 768-dimensional embeddings. When loading the model through
`transformers.AutoModel`, warnings about unused `cls.predictions` weights are
expected because the masked-language-modeling head is not used for feature
encoding.

Deep-learning dependencies for broader neural-network experiments are kept in a
separate optional file because PyTorch, transformers, CUDA, and Python
compatibility should be checked when those experiments begin:

```bash
python -m pip install -r requirements/deep-learning.txt
```

## Activate the Environment

From the repository root:

```bash
source .venv/bin/activate
```

## Verify the Environment

```bash
python --version
python -m pip --version
capsprom status
make check
```

Expected current versions:

```text
Python 3.13.11
pip 26.1.2
```

## Dependency Snapshot

The current Python 3.13 environment snapshot is recorded in:

```text
requirements/lock-py313.txt
```

Use the lock file for auditing the installed environment. Use the smaller
`requirements/*.txt` files to decide which dependency groups should be installed
in a fresh environment.

## Notes

The `.venv/` directory is ignored by Git. Project dependencies should be added
through a versioned dependency file before installing large machine learning or
bioinformatics packages.

## Remote GPU environment

Synthetic accelerator feasibility is available on `bioserver03` through a
project-specific SSH key. Credentials are never stored in repository files.
The remote checkout is `/home/lauro/workspace/capsprom` and the isolated Conda
environment is `/home/lauro/.conda/envs/capsprom-py313`.

The validated remote stack uses Python 3.13.16, PyTorch 2.11.0+cu128, NVIDIA
driver 580.178.04, and an RTX 3060 with 12 GB VRAM. Deterministic CUDA fixture
runs set `CUBLAS_WORKSPACE_CONFIG=:4096:8`. Runner contract version 7 is required
for `device: cuda` or `device: auto`; earlier contracts remain CPU-only so an
existing run cannot change device without changing its versioned contract.

Only code, configurations, tests, and specifications are synchronized by
default. Raw/processed datasets, MLflow databases, checkpoints, predictions,
and generated reports require an explicit transfer decision. Remote environment
freezes and feasibility reports are retrieved into ignored output directories.

The reserved training-only plan root for the blocked GPU contract is
`/home/lauro/workspace/capsprom/outputs/capsprom_basic_canonical_gpu_v1`.
Its `plan_state.json` was created only after the contract audit and remote
dataset-hash verification. All jobs remain pending or blocked and the executor
enforces the false canonical-job gate. Plan presence does not authorize fold
execution, final fits, or external-test access.

`bioserver04` is accessible through the project-specific
`~/.ssh/capsprom_bioserver04` key. The recorded host has 16 logical CPUs,
32.95 GB RAM, Python 3.12.3, and no detected NVIDIA GPU. It is an auxiliary CPU
host only under the current policy; it does not open the `bioserver03` SQLite
tracking database and has no canonical training worker allocation.

## Remote usage policy

Development is local-first. Code editing, configuration drafting,
documentation, focused and fixture tests, code review, and status snapshots do
not require access to either remote host. Do not synchronize routine incremental
changes to the servers.

Use `bioserver03` only for an explicitly authorized workload with many repeated
fits, a material GPU requirement, excessive projected local runtime or memory,
or a remote-specific accelerator check. Use `bioserver04` only for explicitly
authorized heavy CPU work or backup and restore verification belonging to an
authorized remote campaign. A practical planning signal is at least 20 fits,
more than two projected local hours, or less than 25 percent local memory
headroom; these are guidance thresholds rather than automatic authorization.

Synchronize only at a campaign boundary and transfer the minimum immutable
snapshot needed to reproduce that campaign. A small remote pilot is acceptable
only when explicitly authorized as a gate for a larger heavy campaign. During
ordinary development, remote hosts should not be contacted for status polling,
routine tests, documentation checks, or repository mirroring. The active
versioned contract is `configs/capsprom_remote_usage_policy_v3.yaml`; version 2
is retained as historical policy provenance.
