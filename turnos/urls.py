from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # 👈 ESTA ES LA CLAVE
    path('agenda/', views.agenda, name='agenda'),
]