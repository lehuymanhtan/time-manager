# Makefile for Time Manager Testing

# Use venv python
PYTHON := venv/bin/python
PYTEST := $(PYTHON) -m pytest

.PHONY: help install test test-verbose test-coverage test-fast test-unit test-integration test-models test-views test-forms test-utils test-markers clean-coverage clean-pyc clean lint format

help:
	@echo "Time Manager Test Commands:"
	@echo "  make install         - Install all dependencies including test requirements"
	@echo "  make test            - Run all tests"
	@echo "  make test-verbose    - Run all tests with verbose output"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make test-fast       - Run tests quickly (skip slow tests)"
	@echo "  make test-unit       - Run only unit tests"
	@echo "  make test-integration - Run only integration tests"
	@echo "  make test-models     - Run only model tests"
	@echo "  make test-views      - Run only view tests"
	@echo "  make test-forms      - Run only form tests"
	@echo "  make test-utils      - Run only utility tests"
	@echo "  make test-markers    - Show all available test markers"
	@echo "  make clean-coverage  - Remove coverage reports"
	@echo "  make clean-pyc       - Remove Python cache files"
	@echo "  make clean           - Remove all generated files"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTEST)

test-verbose:
	$(PYTEST) -vv

test-coverage:
	$(PYTEST) --cov=meetings --cov=time_mamager --cov-report=html --cov-report=term-missing --cov-report=xml --cov-branch

test-fast:
	$(PYTEST) -m "not slow"

test-unit:
	$(PYTEST) -m unit

test-integration:
	$(PYTEST) -m integration

test-models:
	$(PYTEST) tests/models/ -v

test-views:
	$(PYTEST) tests/views/ -v

test-forms:
	$(PYTEST) tests/forms/ -v

test-utils:
	$(PYTEST) tests/utils/ -v

test-templatetags:
	$(PYTEST) tests/templatetags/ -v

test-markers:
	$(PYTEST) --markers

test-failed:
	$(PYTEST) --lf -v

test-sample:
	$(PYTEST) tests/test_sample.py -v

clean-coverage:
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage

clean-pyc:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete

clean: clean-coverage clean-pyc
	@echo "Cleaned all generated files"
