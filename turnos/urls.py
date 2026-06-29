from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from turnos import views

urlpatterns = [
    # --- Rutas del Frontend (Vistas HTML) ---
    path("", views.index, name="index"),
    path("agenda/", views.agenda, name="agenda"),
    path("reservar/", views.confirmar_reserva, name="confirmar_reserva"),
    path("login/", views.vista_login, name="login"),
    path("registro/", views.vista_registro, name="registro"),
    path("cuenta-bloqueada/", views.vista_cuenta_bloqueada, name="cuenta_bloqueada"),
    
    # 👇 ESTA ES LA RUTA QUE TE CRASHABA EL REGISTRO
    path("recuperar-password/", views.vista_recuperar_password, name="recuperar_password"),

    # --- Endpoints de la API (Autenticación JWT) ---
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 👇 ESTE ES EL ENDPOINT AL QUE LE PEGA EL JAVASCRIPT DE BENJAMÍN
    path('api/auth/registro/', views.api_registrar_usuario, name='api_registrar_usuario'),

    # --- Endpoints de tu misión (Controladores) ---
    path('api/turnos/<int:turno_id>/checkin/', views.registrar_checkin, name='registrar_checkin'),
    path('api/turnos/<int:turno_id>/cancelar/', views.cancelar_turno, name='cancelar_turno'),
    path('api/agenda/bloquear/', views.bloquear_agenda, name='bloquear_agenda'),
]
