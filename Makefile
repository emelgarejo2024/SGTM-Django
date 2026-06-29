# Variables
PYTHON = python
MANAGE = $(PYTHON) manage.py

# Patron para excluir todos los archivos E2E de Selenium
E2E_IGNORE = --ignore=turnos/tests/test_checkin_e2e.py \
             --ignore=turnos/tests/test_historial_e2e.py \
             --ignore=turnos/tests/test_login_registro_e2e.py \
             --ignore=turnos/tests/test_reagendar_e2e.py \
             --ignore=turnos/tests/test_reportes_e2e.py

.PHONY: install format lint test coverage test-e2e

install:
	pip install -r requirements.txt
	pip install black flake8 coverage

format:
	black .

lint:
	flake8 .

# Tests unitarios solamente (sin Selenium, sin necesitar servidor corriendo)
test:
	pytest $(E2E_IGNORE)

# Cobertura sin tests E2E (para el pipeline de CI y SonarQube)
coverage:
	pytest $(E2E_IGNORE) --cov=. --cov-report=xml

# Tests E2E con Selenium (requiere: servidor corriendo + ChromeDriver instalado)
test-e2e:
	pytest turnos/tests/test_checkin_e2e.py \
	       turnos/tests/test_historial_e2e.py \
	       turnos/tests/test_login_registro_e2e.py \
	       turnos/tests/test_reagendar_e2e.py \
	       turnos/tests/test_reportes_e2e.py