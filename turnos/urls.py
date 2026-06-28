from django.urls import path
from . import views

urlpatterns = [
    # --- RUTAS ORIGINALES ---
    path("", views.index, name="index"),  # 👈 ESTA ES LA CLAVE
    path("agenda/", views.agenda, name="agenda"),
    path("reservar/", views.confirmar_reserva, name="confirmar_reserva"),
    
    # --- RUTA PARA LA API DE ESPECIALIDADES ---
    path("api/especialidades/", views.api_obtener_especialidades, name="api_especialidades"),

    # --- NUEVAS RUTAS DE AUTENTICACIÓN (MVP) ---
    path("registro/", views.registro_paciente, name="registro_paciente"),
    path("login/", views.iniciar_sesion, name="iniciar_sesion"),
    path("logout/", views.cerrar_sesion, name="cerrar_sesion"),
]