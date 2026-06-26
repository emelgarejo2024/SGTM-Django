import pytest
from datetime import date, time, timedelta
from django.test import Client
from django.urls import reverse
from turnos.models import Especialidad, BloqueDisponibilidad
from turnos.factories import UsuarioFactory


@pytest.mark.django_db
class TestVistas:
    """Cubre todas las vistas de turnos/views.py."""

    @pytest.fixture(autouse=True)
    def client(self):
        """Cliente HTTP de Django disponible en cada test."""
        self.client = Client()

    # ------------------------------------------------------------------ #
    #  GET /                                                               #
    # ------------------------------------------------------------------ #
    def test_index_devuelve_200(self):
        """La vista index debe responder con status 200."""
        response = self.client.get(reverse("index"))
        assert response.status_code == 200

    def test_index_incluye_especialidades_en_contexto(self):
        """El contexto de index debe contener la lista de especialidades."""
        Especialidad.objects.create(nombre="Radiología")
        response = self.client.get(reverse("index"))
        assert response.status_code == 200
        # La clave 'especialidades' debe estar presente en el contexto
        assert "especialidades" in response.context
        nombres = list(
            response.context["especialidades"].values_list("nombre", flat=True)
        )
        assert "Radiología" in nombres

    # ------------------------------------------------------------------ #
    #  GET /agenda/                                                        #
    # ------------------------------------------------------------------ #
    def test_agenda_devuelve_200(self):
        """La vista agenda debe responder con status 200."""
        response = self.client.get(reverse("agenda"))
        assert response.status_code == 200

    def test_agenda_filtra_por_especialidad(self):
        """Filtra bloques por especialidad al recibir el parámetro."""
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "10101010-1", "dr_ag", "123", "L", "M", "l@cl.cl"
        )
        esp = Especialidad.objects.create(nombre="Traumatología")
        manana = date.today() + timedelta(days=3)
        BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(8, 0),
            hora_fin=time(8, 30),
        )
        response = self.client.get(
            reverse("agenda"), {"especialidad": esp.id, "fecha": str(manana)}
        )
        assert response.status_code == 200
        assert "bloques" in response.context
        assert response.context["bloques"].count() == 1

    def test_agenda_sin_especialidad_muestra_todas(self):
        """Sin parámetros, muestra todos los bloques disponibles."""
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "20202020-2", "dr_ag2", "123", "X", "Y", "xy@cl.cl"
        )
        esp = Especialidad.objects.create(nombre="Ginecología")
        manana = date.today() + timedelta(days=4)
        BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
        )
        response = self.client.get(reverse("agenda"))
        assert response.status_code == 200
        assert response.context["especialidad"] == "Todas"

    # ------------------------------------------------------------------ #
    #  GET /api/especialidades/                                            #
    # ------------------------------------------------------------------ #
    def test_api_especialidades_devuelve_json(self):
        """La API JSON de especialidades retorna los datos correctos."""
        Especialidad.objects.create(nombre="Ortopedia")
        response = self.client.get(reverse("api_especialidades"))
        assert response.status_code == 200
        data = response.json()
        assert "especialidades" in data
        nombres = [e["nombre"] for e in data["especialidades"]]
        assert "Ortopedia" in nombres

    # ------------------------------------------------------------------ #
    #  POST /reservar/                                                     #
    # ------------------------------------------------------------------ #
    def test_confirmar_reserva_sin_pacientes_redirige(self):
        """Si no hay pacientes, confirmar_reserva redirige con error."""
        response = self.client.post(
            reverse("confirmar_reserva"), {"bloque_id": 1}
        )
        assert response.status_code == 302
        assert response["Location"].endswith(reverse("index"))

    def test_confirmar_reserva_exitosa_redirige_a_index(self):
        """Una reserva válida se crea y redirige al index."""
        UsuarioFactory.crear_usuario(
            "PACIENTE", "30303030-3", "pac_view", "123", "V", "W", "vw@cl.cl"
        )
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "40404040-4", "dr_view", "123", "Dr", "V", "drv@cl.cl"
        )
        esp = Especialidad.objects.create(nombre="Endocrinología")
        manana = date.today() + timedelta(days=6)
        bloque = BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(15, 0),
            hora_fin=time(15, 30),
        )
        response = self.client.post(
            reverse("confirmar_reserva"), {"bloque_id": bloque.id}
        )
        assert response.status_code == 302
        assert response["Location"].endswith(reverse("index"))

    def test_confirmar_reserva_get_redirige_a_index(self):
        """Un GET a /reservar/ (sin POST) redirige directamente a index."""
        response = self.client.get(reverse("confirmar_reserva"))
        assert response.status_code == 302
        assert response["Location"].endswith(reverse("index"))
