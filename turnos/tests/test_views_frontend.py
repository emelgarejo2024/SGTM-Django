"""
Tests unitarios de las vistas simuladas en views_frontend.py.

Estas vistas usan datos hardcodeados (no tocan la base de datos), por lo
que los tests son rápidos y no requieren fixtures de modelos reales.
Priorizan las funciones con más líneas de lógica para maximizar la
cobertura aportada por cada test.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestVistasFrontendSimuladas:

    # ------------------------------------------------------------------ #
    #  historial_simulado — cubre ambas ramas del filtro
    # ------------------------------------------------------------------ #
    def test_historial_filtro_futuros_devuelve_turnos(self, client):
        response = client.get(reverse("historial"), {"filtro": "futuros"})
        assert response.status_code == 200
        assert len(response.context["turnos"]) == 2

    def test_historial_filtro_pasados_devuelve_lista_vacia(self, client):
        response = client.get(reverse("historial"), {"filtro": "pasados"})
        assert response.status_code == 200
        assert response.context["turnos"] == []

    # ------------------------------------------------------------------ #
    #  reagendar_turno_simulado — cubre ambas ramas de disponibilidad
    # ------------------------------------------------------------------ #
    def test_reagendar_turno_muestra_bloques_disponibles(self, client):
        response = client.get(reverse("reagendar_turno", args=[1]))
        assert response.status_code == 200
        assert len(response.context["bloques_disponibles"]) == 1
        assert response.context["turno_original"].id == 1

    def test_reagendar_turno_sin_horarios_para_fecha_lejana(self, client):
        response = client.get(
            reverse("reagendar_turno", args=[1]), {"fecha": "2099-01-01"}
        )
        assert response.status_code == 200
        assert response.context["bloques_disponibles"] == []

    # ------------------------------------------------------------------ #
    #  reportes_simulado — cubre los KPIs y el detalle por profesional
    # ------------------------------------------------------------------ #
    def test_reportes_devuelve_kpis_y_detalle(self, client):
        response = client.get(reverse("reportes"))
        assert response.status_code == 200
        assert response.context["kpi_total_turnos"] == 120
        assert len(response.context["detalle_profesionales"]) == 1
        assert response.context["detalle_profesionales"][0]["especialidad"] == (
            "Cardiología"
        )

    def test_reportes_con_filtro_de_mes_y_especialidad(self, client):
        response = client.get(
            reverse("reportes"), {"mes": "2026-06", "especialidad": "2"}
        )
        assert response.status_code == 200
        assert response.context["mes_seleccionado"] == "2026-06"
        assert response.context["especialidad_seleccionada"] == "2"

    # ------------------------------------------------------------------ #
    #  levantar_penalizacion_simulada — cubre ambas ramas de búsqueda
    # ------------------------------------------------------------------ #
    def test_levantar_penalizacion_sin_busqueda(self, client):
        response = client.get(reverse("levantar_penalizacion"))
        assert response.status_code == 200
        assert response.context["paciente_bloqueado"] is None

    def test_levantar_penalizacion_con_rut_busca_paciente(self, client):
        response = client.get(reverse("levantar_penalizacion"), {"rut": "99999999-9"})
        assert response.status_code == 200
        paciente = response.context["paciente_bloqueado"]
        assert paciente is not None
        assert paciente.rut == "99999999-9"
        assert paciente.cantidad_no_shows == 2

    # ------------------------------------------------------------------ #
    #  checkin_simulado — cubre ambas ramas de búsqueda
    # ------------------------------------------------------------------ #
    def test_checkin_sin_query_no_muestra_turnos(self, client):
        response = client.get(reverse("checkin"))
        assert response.status_code == 200
        assert response.context["turnos"] == []

    def test_checkin_con_query_muestra_turno_simulado(self, client):
        response = client.get(reverse("checkin"), {"q": "12345678-9"})
        assert response.status_code == 200
        assert len(response.context["turnos"]) == 1
