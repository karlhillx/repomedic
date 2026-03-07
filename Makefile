.PHONY: setup scan ci help

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
REPOMEDIC := $(VENV)/bin/repomedic

help:
	@echo "Targets:"
	@echo "  make setup              Create venv and install package"
	@echo "  make scan REPO=owner/repo"
	@echo "  make scan CONFIG=examples/config.json"
	@echo "  make ci                 Compile + CLI smoke test"

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .

scan:
	@if [ -z "$(REPO)" ] && [ -z "$(CONFIG)" ]; then \
		echo "Provide REPO=owner/repo or CONFIG=path.json"; \
		exit 1; \
	fi
	@if [ -n "$(REPO)" ]; then \
		$(REPOMEDIC) scan --repo $(REPO); \
	else \
		$(REPOMEDIC) scan --config $(CONFIG); \
	fi

ci:
	$(PYTHON) -m py_compile src/repomedic/*.py
	@if [ -x "$(REPOMEDIC)" ]; then \
		$(REPOMEDIC) --help > /dev/null; \
		echo "CLI smoke check passed."; \
	else \
		echo "Skipping CLI smoke check (run 'make setup' first)."; \
	fi
	@echo "CI smoke checks passed."
