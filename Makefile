PYTHON ?= .venv/bin/python

.PHONY: install-dev lint test check status status-snapshot replication-plan replication-resume replication-summary

install-dev:
	$(PYTHON) -m pip install -r requirements/dev.txt -r requirements/models-classical.txt
	$(PYTHON) -m pip install --no-deps --no-build-isolation -e .

lint:
	$(PYTHON) -m ruff check src tests scripts

test:
	$(PYTHON) -m pytest -q

check: lint test

status:
	$(PYTHON) -m capsprom status

status-snapshot:
	$(PYTHON) -m capsprom status --write manifests/current_status.json

replication-plan:
	$(PYTHON) scripts/run_xgboost_replication.py

replication-resume:
	$(PYTHON) scripts/run_xgboost_replication.py --execute

replication-summary:
	$(PYTHON) scripts/summarize_xgboost_replication.py
