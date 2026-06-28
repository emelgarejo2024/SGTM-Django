"""
Configuración compartida para los tests E2E con Selenium.

El navegador corre en modo headless (sin abrir ventana real) para que
funcione tanto en tu máquina local como en los runners de GitHub Actions,
que no tienen pantalla.
"""

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture
def driver():
    """Crea un navegador Chrome headless para cada test y lo cierra al final."""
    opciones = Options()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--window-size=1280,800")

    navegador = webdriver.Chrome(options=opciones)
    navegador.implicitly_wait(5)

    yield navegador

    navegador.quit()


@pytest.fixture
def base_url():
    """URL base del servidor Django contra el que corren los tests E2E."""
    return BASE_URL