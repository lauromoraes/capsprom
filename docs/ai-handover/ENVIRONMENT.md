# Environment

## Local environment

Repository root: `/mnt/d/workspace/capsprom` in WSL. The project uses `.venv/` and Python 3.13. `docs/development_environment.md` reports Python 3.13.11 and pip 26.1.2; verify rather than assuming after migration.

Core setup:

```bash
/home/lauro/.virtualenvs/doc-project/bin/python -m venv --clear .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements/dev.txt -r requirements/models-classical.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
make check
make status
```

`requirements/lock-py313.txt` is the audit snapshot; the smaller requirement groups express installation intent. Deep-learning and DNA-BERT stacks are optional and should not be installed or changed casually. Local MLflow uses SQLite. Generated databases, models, datasets, predictions, and reports are ignored artifacts and must not be committed.

## Remote environments

- `bioserver03`: `/home/lauro/workspace/capsprom`; Conda environment `/home/lauro/.conda/envs/capsprom-py313`; reported Python 3.13.16, PyTorch 2.11.0+cu128, driver 580.178.04, RTX 3060 12 GB. Deterministic CUDA sets `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
- `bioserver04`: auxiliary CPU host; reported Python 3.12.3, 16 logical CPUs, 32.95 GB RAM, no NVIDIA GPU. It must not open the live bioserver03 SQLite database.

Credentials are external and intentionally undocumented. Remote policy is `configs/capsprom_remote_usage_policy_v3.yaml`; operational instructions are in `docs/remote_job_operations.md`. Do not contact, synchronize, launch, stop, or restart remote work merely to validate documentation.

## Compatibility checks

Run `.venv/bin/python --version`, `.venv/bin/python -m pip --version`, `make check`, and `make status`. For an authorized CUDA campaign, additionally validate remote contract version/device support, dataset hashes, SQLite integrity, available storage, and the exact bounded release before launch.
