# Dev tooling do workflow-automation-management (nao confundir com o make do
# sync-repos-from-master, que o Optimus chama via `make -C "$SYNC_REPO_PATH"`).

VENV := .venv
PY := $(VENV)/bin/python

.PHONY: test venv clean-pyc

$(VENV)/bin/pytest: requirements-dev.txt
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -r requirements-dev.txt

venv: $(VENV)/bin/pytest

test: $(VENV)/bin/pytest
	$(PY) -m pytest tests/ -q

clean-pyc:
	find . -name __pycache__ -type d -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null; true
