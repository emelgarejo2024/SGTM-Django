"""
Test E2E: UC-02 Registrar Check-in Presencial.

Simula a una recepcionista buscando a un paciente por RUT/nombre y
marcando su llegada (check-in) sobre un turno reservado para el día actual.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def buscar_por_testid(driver, testid):
    """Atajo para ubicar un elemento por su atributo data-testid."""
    return driver.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")


def esperar_por_testid(driver, testid, timeout=10):
    """Espera explícita hasta que el elemento con ese data-testid exista."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{testid}']"))
    )


class TestCheckinPresencial:
    """Casos de prueba para la vista de check-in (UC-02)."""

    def test_formulario_de_busqueda_se_muestra(self, driver, base_url):
        """La página de check-in debe mostrar el formulario de búsqueda al entrar."""
        driver.get(f"{base_url}/checkin/")

        formulario = esperar_por_testid(driver, "form-buscar-paciente")
        campo_busqueda = buscar_por_testid(driver, "input-buscar-paciente")
        boton_buscar = buscar_por_testid(driver, "btn-buscar-paciente")

        assert formulario.is_displayed()
        assert campo_busqueda.is_displayed()
        assert boton_buscar.is_displayed()

    def test_busqueda_sin_resultados_muestra_mensaje(self, driver, base_url):
        """Buscar un RUT que no existe debe mostrar el estado vacío, no un error."""
        driver.get(f"{base_url}/checkin/")

        campo_busqueda = esperar_por_testid(driver, "input-buscar-paciente")
        campo_busqueda.send_keys("99999999-9")
        buscar_por_testid(driver, "btn-buscar-paciente").click()

        sin_resultados = esperar_por_testid(driver, "checkin-sin-resultados")
        assert sin_resultados.is_displayed()

    def test_buscar_paciente_muestra_sus_turnos_del_dia(
        self, driver, base_url, paciente_de_prueba
    ):
        """Buscar un paciente con turno reservado hoy debe listar ese turno."""
        driver.get(f"{base_url}/checkin/")

        campo_busqueda = esperar_por_testid(driver, "input-buscar-paciente")
        campo_busqueda.send_keys(paciente_de_prueba.rut)
        buscar_por_testid(driver, "btn-buscar-paciente").click()

        tabla = esperar_por_testid(driver, "tabla-turnos-checkin")
        assert tabla.is_displayed()

    def test_marcar_llegada_cambia_estado_a_en_sala_de_espera(
        self, driver, base_url, turno_reservado_hoy
    ):
        """
        Al hacer click en 'Marcar llegada' sobre un turno reservado,
        el estado debe pasar a 'En sala de espera' (BR-21) sin recargar
        manualmente la página.
        """
        driver.get(f"{base_url}/checkin/?q={turno_reservado_hoy.paciente.rut}")

        boton_checkin = esperar_por_testid(
            driver, f"btn-checkin-{turno_reservado_hoy.id}"
        )
        boton_checkin.click()

        confirmacion = esperar_por_testid(
            driver, f"checkin-ya-realizado-{turno_reservado_hoy.id}"
        )
        assert "sala de espera" in confirmacion.text.lower()