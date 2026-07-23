# Dependency Files

This directory defines the Python dependencies used by the CapsProm project.

- `base.txt`: core stack for EDA, feature engineering, classical machine learning, MLflow tracking, and plotting.
- `dev.txt`: base dependencies plus test/lint tooling.
- `models-classical.txt`: optional dependencies for classical models with large binary wheels, such as XGBoost.
- `dna-bert-cpu.txt`: CPU-oriented dependencies for DNA-BERT feature extraction.
- `deep-learning.txt`: broader optional dependencies for DNA-BERT and neural-network experiments. Install this file only when those experiments begin, because deep-learning wheels may depend on the local Python, CUDA, and platform setup.

Recommended setup from the repository root:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/base.txt
python -m pip install -r requirements/dev.txt
```

Optional classical-model setup:

```bash
python -m pip install -r requirements/models-classical.txt
```

Optional DNA-BERT CPU setup:

```bash
python -m pip install -r requirements/dna-bert-cpu.txt
```

Optional deep-learning setup:

```bash
python -m pip install -r requirements/deep-learning.txt
```
