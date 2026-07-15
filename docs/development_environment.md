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

## Activate the Environment

From the repository root:

```bash
source .venv/bin/activate
```

## Verify the Environment

```bash
python --version
python -m pip --version
```

Expected current versions:

```text
Python 3.13.11
pip 26.1.2
```

## Notes

The `.venv/` directory is ignored by Git. Project dependencies should be added
through a versioned dependency file before installing large machine learning or
bioinformatics packages.
