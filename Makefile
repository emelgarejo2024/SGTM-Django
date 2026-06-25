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
	$(MANAGE) test

coverage:
	coverage run --source='.' manage.py test
	coverage xml -o coverage.xml
	coverage report -m