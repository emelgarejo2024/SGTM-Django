from django.urls import path
from . import views
from . import views_frontend

urlpatterns = [
    # --- Rutas existentes (Rodrigo) ---
    path("", views.index, name="index"),  # 👈 ESTA ES LA CLAVE
    path("agenda/", views.agenda, name="agenda"),
    path("reservar/", views.confirmar_reserva, name="confirmar_reserva"),
    # --- UC-02: Check-in presencial ---
    path("checkin/", views_frontend.checkin_simulado, name="checkin"),
    path(
        "checkin/registrar/",
        views_frontend.checkin_simulado,
        name="registrar_checkin",
    ),
    # --- UC-03, UC-06, UC-08: Historial del paciente ---
    path("historial/", views_frontend.historial_simulado, name="historial"),
    path(
        "reagendar/<int:turno_id>/",
        views_frontend.reagendar_turno_simulado,
        name="reagendar_turno",
    ),
    path(
        "reagendar/confirmar/",
        views_frontend.historial_simulado,
        name="confirmar_reagendamiento",
    ),
    path(
        "historial/confirmar/",
        views_frontend.historial_simulado,
        name="confirmar_turno",
    ),
    path(
        "historial/cancelar/",
        views_frontend.historial_simulado,
        name="cancelar_turno",
    ),
    # --- FR-23, FR-24: Panel de reportes ---
    path("reportes/", views_frontend.reportes_simulado, name="reportes"),
    path(
        "reportes/exportar/",
        views_frontend.reportes_simulado,
        name="exportar_reporte",
    ),
    # --- UC-07, UC-10: Login y registro ---
    path("login/", views_frontend.login_simulado, name="login"),
    path("registro/", views_frontend.registro_simulado, name="registro"),
    path(
        "cuenta-bloqueada/",
        views_frontend.cuenta_bloqueada_simulada,
        name="cuenta_bloqueada",
    ),
    path(
        "recuperar-password/",
        views_frontend.login_simulado,
        name="recuperar_password",
    ),
    # --- Módulo recepción/admin ---
    path(
        "calendario/",
        views_frontend.calendario_global_simulado,
        name="calendario_global",
    ),
    path(
        "calendario/editar/<int:turno_id>/",
        views_frontend.calendario_global_simulado,
        name="editar_turno_recepcion",
    ),
    path("sobrecupo/", views_frontend.sobrecupo_simulado, name="sobrecupo"),
    path(
        "sobrecupo/registrar/",
        views_frontend.sobrecupo_simulado,
        name="registrar_sobrecupo",
    ),
    path(
        "penalizaciones/",
        views_frontend.levantar_penalizacion_simulada,
        name="levantar_penalizacion",
    ),
    path(
        "penalizaciones/confirmar/",
        views_frontend.levantar_penalizacion_simulada,
        name="confirmar_levantamiento",
    ),
    # --- Módulo médico ---
    path(
        "disponibilidad/",
        views_frontend.config_disponibilidad_simulada,
        name="config_disponibilidad",
    ),
    path(
        "disponibilidad/bloquear/",
        views_frontend.bloquear_agenda_simulada,
        name="bloquear_agenda",
    ),
    path(
        "disponibilidad/bloquear/confirmar/",
        views_frontend.bloquear_agenda_simulada,
        name="confirmar_bloqueo_agenda",
    ),
    path(
        "agenda-medico/",
        views_frontend.agenda_medico_simulada,
        name="agenda_medico",
    ),
    path(
        "agenda-medico/json/",
        views_frontend.agenda_medico_simulada,
        name="agenda_medico_json",
    ),
    path(
        "agenda-medico/asistencia/",
        views_frontend.agenda_medico_simulada,
        name="marcar_asistencia",
    ),
]
