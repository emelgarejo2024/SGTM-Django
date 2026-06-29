import pytest
from datetime import date, time, timedelta
from django.test import Client
from django.urls import reverse
from turnos.models import Especialidad, BloqueDisponibilidad, Usuario
from turnos.factories import UsuarioFactory
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


# --- Fixture para crear un admin real compatible con el proyecto ---
@pytest.fixture
def admin_user():
    return Usuario.objects.create_superuser(
        username="admin_test", password="password123", rut="11111111-1", rol="ADMIN"
    )


# --- Pruebas para Check-in ---
@pytest.mark.django_db
def test_registrar_checkin_exitoso(api_client, admin_user, turno_reservado_hoy):
    # 1. Ajustamos manualmente la hora del turno para que sea "ahora mismo"
    ahora = timezone.localtime(timezone.now())
    turno_reservado_hoy.bloque.fecha = ahora.date()
    turno_reservado_hoy.bloque.hora_inicio = ahora.time()
    turno_reservado_hoy.bloque.save()

    # 2. Generamos el token y probamos
    token = RefreshToken.for_user(admin_user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("registrar_checkin", args=[turno_reservado_hoy.id])
    response = api_client.post(url)

    # 3. Si esto sigue tirando 400, imprime el error para ver qué dice el servicio
    if response.status_code != 200:
        print(f"\nRespuesta del servidor: {response.data}")

    assert response.status_code == status.HTTP_200_OK
    turno_reservado_hoy.refresh_from_db()
    assert turno_reservado_hoy.estado == "EN_ESPERA"


# --- Pruebas para Cancelación ---
@pytest.mark.django_db
def test_cancelar_turno_exitoso(api_client, turno_cancelable):
    paciente = turno_cancelable.paciente
    token = RefreshToken.for_user(paciente).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("cancelar_turno", args=[turno_cancelable.id])
    response = api_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    turno_cancelable.refresh_from_db()
    assert turno_cancelable.estado == "CANCELADO"
    assert turno_cancelable.bloque.esta_disponible == True


@pytest.mark.django_db
def test_cancelar_turno_falla_por_tiempo(api_client, turno_no_cancelable):
    paciente = turno_no_cancelable.paciente
    token = RefreshToken.for_user(paciente).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("cancelar_turno", args=[turno_no_cancelable.id])
    response = api_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    turno_no_cancelable.refresh_from_db()
    assert turno_no_cancelable.estado == "RESERVADO"


# --- Pruebas para Bloqueo ---
@pytest.mark.django_db
def test_bloquear_agenda_exitoso(api_client, admin_user):
    medico = Usuario.objects.create(username="dr_prueba", rut="9999999-9", rol="MEDICO")
    especialidad = Especialidad.objects.create(nombre="General")
    fecha_hoy = timezone.now().date()

    bloque = BloqueDisponibilidad.objects.create(
        medico=medico,
        especialidad=especialidad,
        fecha=fecha_hoy,
        hora_inicio="10:00:00",
        hora_fin="10:30:00",
        esta_disponible=True,
    )

    token = RefreshToken.for_user(admin_user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("bloquear_agenda")
    payload = {
        "medico_id": medico.id,
        "fecha_inicio": str(fecha_hoy),
        "fecha_fin": str(fecha_hoy),
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    bloque.refresh_from_db()
    assert bloque.esta_disponible == False


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
        response = self.client.post(reverse("confirmar_reserva"), {"bloque_id": 1})
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

    def test_confirmar_reserva_falla_bloque_invalido(self):
        UsuarioFactory.crear_usuario(
            "PACIENTE", "55555555-5", "pac", "123", "A", "B", "a@a.cl"
        )

        response = self.client.post(reverse("confirmar_reserva"), {"bloque_id": 9999})

        assert response.status_code == 302
