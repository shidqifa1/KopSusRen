PYTHON ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup test lint run

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --no-deps -r requirements.lock
	$(BIN)/python -m pip check
	$(BIN)/pre-commit install --install-hooks

test:
	$(BIN)/python -m pytest

lint:
	$(BIN)/ruff check app tests
	$(BIN)/ruff format --check app tests
	$(BIN)/mypy

run:
	$(BIN)/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
