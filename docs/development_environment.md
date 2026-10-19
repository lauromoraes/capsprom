# Development Environment

This project uses a local virtual environment at the repository root:

```bash
.venv/
```

## Create or Recreate the Environment

The current environment was created with Python 3.13.11 from the WSL Python
installation available through the existing `doc-project` environment:

```bash
/home/lauro/.virtualenvs/doc-project/bin/python -m venv --clear .venv
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
