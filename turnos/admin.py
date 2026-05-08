from django.contrib import admin
from .models import Usuario, Especialidad, BloqueDisponibilidad, Reserva

admin.site.register(Usuario)
admin.site.register(Especialidad)
admin.site.register(BloqueDisponibilidad)
admin.site.register(Reserva)