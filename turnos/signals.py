from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reserva

# Este es nuestro "Observador"
@receiver(post_save, sender=Reserva)
def auditar_nueva_reserva(sender, instance, created, **kwargs):
    if created:
        print(f"\n[AUDITORÍA - PATRÓN OBSERVER] Nueva reserva detectada.")
        print(f"-> Paciente: {instance.paciente.first_name} | RUT: {instance.paciente.rut}")
        print(f"-> Médico: {instance.bloque.medico.first_name}")
        print(f"-> Fecha y Hora: {instance.bloque.fecha} a las {instance.bloque.hora_inicio}")
        print(f"-> Estado: {instance.estado}")
        print("-" * 50 + "\n")