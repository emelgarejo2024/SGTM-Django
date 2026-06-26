# Variables
PYTHON = python
MANAGE = $(PYTHON) manage.py

.PHONY: install format lint test coverage

install:
	pip install -r requirements.txt
	pip install black flake8 coverage

format:
	black .

lint:
	flake8 .

test:
	pytest

coverage:
	pytest --cov=. --cov-report=xml