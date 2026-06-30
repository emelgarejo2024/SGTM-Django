from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from turnos import views

urlpatterns = [
    # --- Rutas del Frontend (Vistas HTML) ---
    path("", views.index, name="index"),
    path("agenda/", views.agenda, name="agenda"),
    path("login/", views.vista_login, name="login"),
    path("registro/", views.vista_registro, name="registro"),
    path("cuenta-bloqueada/", views.vista_cuenta_bloqueada, name="cuenta_bloqueada"),
    path(
        "recuperar-password/", views.vista_recuperar_password, name="recuperar_password"
    ),
    # --- Vistas HTML con datos reales ---
    path("historial/", views.historial_view, name="historial"),
    path("historial/cancelar/", views.cancelar_turno_form, name="cancelar_form"),
    path("historial/confirmar/", views.confirmar_turno_form, name="confirmar_form"),
    path("checkin/", views.checkin_view, name="checkin"),
    path("checkin/registrar/", views.checkin_accion, name="checkin_accion"),
    path("reagendar/<int:turno_id>/", views.reagendar_view, name="reagendar_turno"),
    # --- Endpoints de la API (Autenticación JWT) ---
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "api/auth/registro/", views.api_registrar_usuario, name="api_registrar_usuario"
    ),
    path("api/mis-turnos/", views.mis_turnos, name="mis_turnos"),
    # --- Endpoints de la API (Controladores) ---
    path(
        "api/turnos/reservar/",
        views.api_reservar_turno,
        name="api_reservar_turno",
    ),
    path(
        "api/turnos/<int:turno_id>/checkin/",
        views.registrar_checkin,
        name="registrar_checkin",
    ),
    path(
        "api/turnos/<int:turno_id>/cancelar/",
        views.cancelar_turno,
        name="cancelar_turno",
    ),
    path("api/agenda/bloquear/", views.bloquear_agenda, name="bloquear_agenda"),
]
