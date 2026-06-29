"""
Configuración compartida para los tests E2E con Selenium.

El navegador corre en modo headless (sin abrir ventana real) para que
funcione tanto en tu máquina local como en los runners de GitHub Actions,
que no tienen pantalla.

Los fixtures de datos usan las factories de turnos/factories.py para
crear pacientes, médicos, bloques y reservas en los estados que cada
caso de uso del SRS necesita.
"""

from datetime import date, datetime, time, timedelta

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from turnos.factories import (
    BloqueDisponibilidadFactory,
    ReservaFactory,
    UsuarioFactory,
)


# --------------------------------------------------------------------------- #
#  Navegador
# --------------------------------------------------------------------------- #
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
def base_url(live_server):
    """URL base del servidor Django, levantado automáticamente por pytest-django."""
    return live_server.url


def _rut_unico():
    import random

    return f"{random.randint(10000000, 29999999)}-{random.randint(0, 9)}"


# --------------------------------------------------------------------------- #
#  Fixtures de checkin.html (UC-02)
# --------------------------------------------------------------------------- #
@pytest.fixture
def paciente_de_prueba(db):
    """Un paciente simple, sin turnos asociados, para probar la búsqueda."""
    return UsuarioFactory.crear_usuario(
        "PACIENTE",
        rut=_rut_unico(),
        username=f"paciente_checkin_{_rut_unico()}",
        password="claveSegura123",
        first_name="Paciente",
        last_name="Checkin",
        email="paciente.checkin@test.cl",
    )


@pytest.fixture
def turno_reservado_hoy(db):
    """
    Un turno en estado RESERVADO cuyo bloque es hoy, listo para que
    la recepcionista lo busque y le haga check-in (UC-02).
    """
    bloque = BloqueDisponibilidadFactory.crear_bloque(
        fecha=date.today(),
        hora_inicio=time(9, 0),
        hora_fin=time(9, 30),
        esta_disponible=False,
    )
    return ReservaFactory.crear_reserva(bloque=bloque, estado="RESERVADO")


# --------------------------------------------------------------------------- #
#  Fixtures de historial.html (UC-03, UC-06, UC-08)
# --------------------------------------------------------------------------- #
@pytest.fixture
def turno_reservado_paciente(db):
    """Un turno futuro en estado RESERVADO, con margen amplio de anticipación."""
    bloque = BloqueDisponibilidadFactory.crear_bloque(
        fecha=date.today() + timedelta(days=5),
        hora_inicio=time(10, 0),
        hora_fin=time(10, 30),
        esta_disponible=False,
    )
    return ReservaFactory.crear_reserva(bloque=bloque, estado="RESERVADO")


@pytest.fixture
def turno_cancelable(db):
    """
    Un turno RESERVADO con más de 12 horas de anticipación (BR-24),
    por lo que el botón 'Cancelar' debe estar habilitado.
    """
    bloque = BloqueDisponibilidadFactory.crear_bloque(
        fecha=date.today() + timedelta(days=2),
        hora_inicio=time(11, 0),
        hora_fin=time(11, 30),
        esta_disponible=False,
    )
    return ReservaFactory.crear_reserva(bloque=bloque, estado="RESERVADO")


@pytest.fixture
def turno_no_cancelable(db):
    """
    Un turno RESERVADO a menos de 12 horas de anticipación (BR-24),
    por lo que el botón 'Cancelar' debe estar deshabilitado.
    Se construye con fecha de hoy y una hora cercana al momento actual
    para garantizar el margen menor a 12 horas sin importar cuándo corra el test.
    """
    ahora = datetime.now()
    hora_cercana = (ahora + timedelta(hours=2)).time()
    bloque = BloqueDisponibilidadFactory.crear_bloque(
        fecha=ahora.date(),
        hora_inicio=hora_cercana,
        hora_fin=(ahora + timedelta(hours=2, minutes=30)).time(),
        esta_disponible=False,
    )
    return ReservaFactory.crear_reserva(bloque=bloque, estado="RESERVADO")


# --------------------------------------------------------------------------- #
#  Fixtures de reagendar_turno.html (UC-03)
# --------------------------------------------------------------------------- #
@pytest.fixture
def bloque_alternativo(db, turno_reservado_paciente):
    """
    Un bloque DISPONIBLE del mismo médico y especialidad que
    turno_reservado_paciente, para que aparezca como opción de reagendamiento.
    """
    bloque_original = turno_reservado_paciente.bloque
    return BloqueDisponibilidadFactory.crear_bloque(
        medico=bloque_original.medico,
        especialidad=bloque_original.especialidad,
        fecha=bloque_original.fecha + timedelta(days=1),
        hora_inicio=time(10, 0),
        hora_fin=time(10, 30),
        esta_disponible=True,
    )


# --------------------------------------------------------------------------- #
#  Fixtures de login.html / registro.html (UC-07, UC-10)
# --------------------------------------------------------------------------- #
@pytest.fixture
def paciente_existente(db):
    """Un paciente ya registrado, para probar duplicidad de RUT/correo (BR-1)."""
    return UsuarioFactory.crear_usuario(
        "PACIENTE",
        rut="12345678-5",
        username="paciente_existente_test",
        password="claveSegura123",
        first_name="Paciente",
        last_name="Existente",
        email="paciente.existente@test.cl",
    )


@pytest.fixture
def paciente_bloqueado_no_show(db):
    """
    Un paciente con cuenta bloqueada por inasistencias reiteradas (BR-29).
    Expone .password_plano porque set_password() hashea la contraseña
    y el test necesita el valor original para escribirlo en el formulario.
    """
    paciente = UsuarioFactory.crear_usuario(
        "PACIENTE",
        rut=_rut_unico(),
        username=f"paciente_bloqueado_{_rut_unico()}",
        password="claveSegura123",
        first_name="Paciente",
        last_name="Bloqueado",
        email="paciente.bloqueado@test.cl",
    )
    paciente.password_plano = "claveSegura123"

    # Dos no-shows en los últimos 6 meses (BR-29): se modelan como dos
    # reservas pasadas en estado NO_SHOW asociadas al paciente.
    for dias_atras in (10, 40):
        bloque_pasado = BloqueDisponibilidadFactory.crear_bloque(
            fecha=date.today() - timedelta(days=dias_atras),
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
            esta_disponible=False,
        )
        ReservaFactory.crear_reserva(
            paciente=paciente, bloque=bloque_pasado, estado="NO_SHOW"
        )

    return paciente
