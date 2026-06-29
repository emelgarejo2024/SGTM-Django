"""
Vistas con datos simulados para las plantillas de frontend pendientes.

Estas vistas existen para poder demostrar las plantillas funcionando en
el navegador SIN depender de que el modelo Reserva tenga todos sus estados
implementados ni de que la autenticación JWT esté lista. Los datos son
estructuras de Python hardcodeadas que imitan la forma de los objetos
reales (Usuario, BloqueDisponibilidad, Reserva).

Una vez que el backend esté listo, estas vistas se reemplazan por las
reales en views.py, sin tocar ninguna plantilla.
"""

from datetime import date, timedelta

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

# Constantes de datos simulados (evita literales duplicados detectados
# por SonarQube en múltiples funciones de este archivo).
MEDICO_NOMBRE_DEMO = "Andrés"
MEDICO_APELLIDO_DEMO = "Fuentes"
PACIENTE_NOMBRE_DEMO = "María"
PACIENTE_APELLIDO_DEMO = "González"
ESPECIALIDAD_DEMO = "Cardiología"


class _ObjetoSimulado:
    """
    Envuelve un diccionario para que sus llaves se puedan acceder con
    notación de punto en los templates Django, igual que un objeto real
    de Django (ej: turno.bloque.medico.first_name).
    """

    def __init__(self, datos):
        for clave, valor in datos.items():
            if isinstance(valor, dict):
                valor = _ObjetoSimulado(valor)
            setattr(self, clave, valor)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_estado_display(self):
        mapa_estados = {
            "DISPONIBLE": "Disponible",
            "RESERVADO": "Reservado",
            "CONFIRMADO": "Confirmado",
            "EN_SALA_ESPERA": "En sala de espera",
            "EJECUTADO": "Ejecutado",
            "CANCELADO": "Cancelado",
            "NO_SHOW": "No-show",
        }
        return mapa_estados.get(self.estado, self.estado)


def _crear_medico_demo():
    return _ObjetoSimulado(
        {"first_name": MEDICO_NOMBRE_DEMO, "last_name": MEDICO_APELLIDO_DEMO}
    )


def _crear_paciente_demo(rut="11111111-1"):
    return _ObjetoSimulado(
        {
            "first_name": PACIENTE_NOMBRE_DEMO,
            "last_name": PACIENTE_APELLIDO_DEMO,
            "rut": rut,
        }
    )


def _crear_bloque_demo(medico, fecha, hora_inicio, hora_fin, especialidad=None):
    return _ObjetoSimulado(
        {
            "id": 1,
            "medico": medico,
            "especialidad": _ObjetoSimulado(
                {"nombre": especialidad or ESPECIALIDAD_DEMO}
            ),
            "fecha": fecha,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "esta_disponible": True,
        }
    )


def _crear_turno_demo(turno_id, paciente, bloque, estado):
    return _ObjetoSimulado(
        {"id": turno_id, "paciente": paciente, "bloque": bloque, "estado": estado}
    )


# --------------------------------------------------------------------------- #
#  UC-02: Check-in presencial
# --------------------------------------------------------------------------- #
@require_http_methods(["GET"])
def checkin_simulado(request):
    query = request.GET.get("q", "")
    turnos = []

    if query:
        medico = _crear_medico_demo()
        paciente = _crear_paciente_demo("12345678-9")
        bloque = _crear_bloque_demo(
            medico, date.today(), "09:00", "09:30", "Medicina General"
        )
        turnos = [_crear_turno_demo(1, paciente, bloque, "RESERVADO")]

    return render(request, "checkin.html", {"query": query, "turnos": turnos})


# --------------------------------------------------------------------------- #
#  UC-03, UC-06, UC-08: Historial del paciente
# --------------------------------------------------------------------------- #
@require_http_methods(["GET"])
def historial_simulado(request):
    filtro_activo = request.GET.get("filtro", "futuros")

    medico = _crear_medico_demo()
    paciente = _crear_paciente_demo()

    bloque_reservado = _crear_bloque_demo(
        medico, date.today() + timedelta(days=5), "10:00", "10:30"
    )
    bloque_confirmado = _crear_bloque_demo(
        medico, date.today() + timedelta(days=2), "11:00", "11:30"
    )

    turno_reservado = _crear_turno_demo(1, paciente, bloque_reservado, "RESERVADO")
    turno_reservado.puede_cancelar = True

    turno_confirmado = _crear_turno_demo(2, paciente, bloque_confirmado, "CONFIRMADO")
    turno_confirmado.puede_cancelar = False

    turnos = [turno_reservado, turno_confirmado] if filtro_activo != "pasados" else []

    return render(
        request,
        "historial.html",
        {"filtro_activo": filtro_activo, "turnos": turnos},
    )


# --------------------------------------------------------------------------- #
#  UC-03: Reagendar turno
# --------------------------------------------------------------------------- #
@require_http_methods(["GET"])
def reagendar_turno_simulado(request, turno_id):
    medico = _crear_medico_demo()
    paciente = _crear_paciente_demo()
    fecha_buscada = request.GET.get("fecha", "")

    bloque_original = _crear_bloque_demo(
        medico, date.today() + timedelta(days=5), "10:00", "10:30"
    )
    turno_original = _crear_turno_demo(turno_id, paciente, bloque_original, "RESERVADO")

    bloques_disponibles = []
    if fecha_buscada != "2099-01-01":
        bloque_alternativo = _crear_bloque_demo(
            medico, date.today() + timedelta(days=6), "10:00", "10:30"
        )
        bloque_alternativo.id = 99
        bloques_disponibles = [bloque_alternativo]

    return render(
        request,
        "reagendar_turno.html",
        {
            "turno_original": turno_original,
            "bloques_disponibles": bloques_disponibles,
            "fecha_buscada": fecha_buscada,
        },
    )


# --------------------------------------------------------------------------- #
#  FR-23, FR-24: Panel de reportes
# --------------------------------------------------------------------------- #
@require_http_methods(["GET"])
def reportes_simulado(request):
    especialidades = [
        _ObjetoSimulado({"id": 1, "nombre": "Medicina General"}),
        _ObjetoSimulado({"id": 2, "nombre": ESPECIALIDAD_DEMO}),
        _ObjetoSimulado({"id": 3, "nombre": "Pediatría"}),
    ]

    datos_ocupacion = {
        "labels": '["Medicina General", "Cardiología", "Pediatría"]',
        "valores": "[45, 30, 25]",
    }
    datos_ausentismo = {
        "labels": '["Enero", "Febrero", "Marzo"]',
        "valores": "[3, 5, 2]",
    }

    detalle_profesionales = [
        {
            "medico_id": 1,
            "medico_nombre": f"{MEDICO_NOMBRE_DEMO} {MEDICO_APELLIDO_DEMO}",
            "especialidad": ESPECIALIDAD_DEMO,
            "total_turnos": 40,
            "ejecutados": 35,
            "no_shows": 3,
            "tasa_ocupacion": 87,
        }
    ]

    return render(
        request,
        "reportes.html",
        {
            "especialidades": especialidades,
            "mes_seleccionado": request.GET.get("mes", ""),
            "especialidad_seleccionada": request.GET.get("especialidad", ""),
            "kpi_total_turnos": 120,
            "kpi_tasa_ocupacion": 78,
            "kpi_no_shows": 10,
            "kpi_tasa_ausentismo": 8,
            "datos_ocupacion": datos_ocupacion,
            "datos_ausentismo": datos_ausentismo,
            "detalle_profesionales": detalle_profesionales,
        },
    )


# --------------------------------------------------------------------------- #
#  UC-07, UC-10: Login y registro
# --------------------------------------------------------------------------- #
@require_http_methods(["GET"])
def login_simulado(request):
    return render(request, "login.html")


@require_http_methods(["GET"])
def registro_simulado(request):
    return render(request, "registro.html")


@require_http_methods(["GET"])
def cuenta_bloqueada_simulada(request):
    return render(
        request,
        "cuenta_bloqueada.html",
        {"cantidad_no_shows": 2, "periodo_meses": 6},
    )


# --------------------------------------------------------------------------- #
#  Módulo recepción/admin/médico
# --------------------------------------------------------------------------- #
@require_http_methods(["GET"])
def calendario_global_simulado(request):
    medico = _crear_medico_demo()
    paciente = _crear_paciente_demo()
    bloque = _crear_bloque_demo(medico, date.today(), "10:00", "10:30")
    turno = _crear_turno_demo(1, paciente, bloque, "RESERVADO")

    return render(
        request,
        "calendario_global.html",
        {"medicos": [medico], "turnos": [turno]},
    )


@require_http_methods(["GET"])
def sobrecupo_simulado(request):
    medico = _crear_medico_demo()
    bloque = _crear_bloque_demo(medico, date.today(), "12:00", "12:30")
    return render(request, "sobrecupo.html", {"bloque": bloque})


@require_http_methods(["GET"])
def config_disponibilidad_simulada(request):
    especialidades = [_ObjetoSimulado({"id": 1, "nombre": ESPECIALIDAD_DEMO})]
    medico = _crear_medico_demo()
    bloque = _crear_bloque_demo(
        medico, date.today() + timedelta(days=1), "09:00", "09:30"
    )
    return render(
        request,
        "config_disponibilidad.html",
        {
            "especialidades_medico": especialidades,
            "bloques": [bloque],
            "fecha_minima": date.today().isoformat(),
        },
    )


@require_http_methods(["GET"])
def agenda_medico_simulada(request):
    paciente = _crear_paciente_demo()
    medico = _crear_medico_demo()
    bloque = _crear_bloque_demo(medico, date.today(), "10:00", "10:30")
    turno = _crear_turno_demo(1, paciente, bloque, "EN_SALA_ESPERA")

    return render(
        request,
        "agenda_medico.html",
        {"fecha_hoy": date.today(), "turnos_hoy": [turno]},
    )


@require_http_methods(["GET"])
def bloquear_agenda_simulada(request):
    medico = _crear_medico_demo()
    bloque = _crear_bloque_demo(
        medico, date.today() + timedelta(days=3), "15:00", "15:30"
    )
    return render(
        request,
        "bloquear_agenda.html",
        {"bloques_bloqueables": [bloque]},
    )


@require_http_methods(["GET"])
def levantar_penalizacion_simulada(request):
    rut_buscado = request.GET.get("rut", "")
    paciente_bloqueado = None

    if rut_buscado:
        paciente_bloqueado = _ObjetoSimulado(
            {
                "first_name": "Pedro",
                "last_name": "Ramírez",
                "rut": rut_buscado,
                "id": 1,
                "cantidad_no_shows": 2,
            }
        )

    return render(
        request,
        "levantar_penalizacion.html",
        {"rut_buscado": rut_buscado, "paciente_bloqueado": paciente_bloqueado},
    )
