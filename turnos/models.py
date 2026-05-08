from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. USUARIO
class Usuario(AbstractUser):
    ROLES = (
        ('PACIENTE', 'Paciente'),
        ('MEDICO', 'Médico'),
        ('ADMIN', 'Administrador'),
    )
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    rol = models.CharField(max_length=10, choices=ROLES, default='PACIENTE')

    def __str__(self):
        return f"{self.get_full_name()} - {self.rut}"

# 2. ESPECIALIDAD
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

# 3. BLOQUE DE DISPONIBILIDAD (Desacoplado - Responsabilidad del Médico)
class BloqueDisponibilidad(models.Model):
    medico = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='bloques_medico', limit_choices_to={'rol': 'MEDICO'})
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    # Bandera booleana rápida para saber si está libre o no
    esta_disponible = models.BooleanField(default=True)

    class Meta:
        unique_together = ('medico', 'fecha', 'hora_inicio')
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"Bloque: {self.medico.first_name} | {self.fecha} {self.hora_inicio} - {'Libre' if self.esta_disponible else 'Ocupado'}"

# 4. RESERVA (Desacoplado - Responsabilidad del Paciente)
class Reserva(models.Model):
    ESTADOS = (
        ('RESERVADO', 'Reservado'),
        ('CONFIRMADO', 'Confirmado'),
        ('EN_ESPERA', 'En sala de espera'),
        ('EJECUTADO', 'Ejecutado'),
        ('CANCELADO', 'Cancelado'),
        ('NO_SHOW', 'No-show'),
    )
    
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas_paciente', limit_choices_to={'rol': 'PACIENTE'})
    # Relación 1 a 1: Una reserva ocupa un solo bloque, y un bloque tiene solo una reserva activa.
    bloque = models.OneToOneField(BloqueDisponibilidad, on_delete=models.PROTECT) 
    
    estado = models.CharField(max_length=15, choices=ESTADOS, default='RESERVADO')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva de {self.paciente.first_name} para bloque ID: {self.bloque.id} | Estado: {self.estado}"