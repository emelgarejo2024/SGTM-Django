from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


# 1. USUARIO
class Usuario(AbstractUser):
    ROLES = (
        ("PACIENTE", "Paciente"),
        ("MEDICO", "Médico"),
        ("ADMIN", "Administrador"),
    )
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    rol = models.CharField(max_length=10, choices=ROLES, default="PACIENTE")

    def __str__(self):
        return f"{self.get_full_name()} - {self.rut}"


# 2. ESPECIALIDAD
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Especialidad"
        verbose_name_plural = "Especialidades"

    def __str__(self):
        return self.nombre


# 3. BLOQUE DE DISPONIBILIDAD (Desacoplado - Responsabilidad del Médico)
class BloqueDisponibilidad(models.Model):
    medico = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="bloques_medico",
        limit_choices_to={"rol": "MEDICO"},
    )
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    # Bandera booleana rápida para saber si está libre o no
    esta_disponible = models.BooleanField(default=True)

    class Meta:
        unique_together = ("medico", "fecha", "hora_inicio")
        ordering = ["fecha", "hora_inicio"]
        constraints = [
            # CAPA 3: hora_fin siempre debe ser posterior a hora_inicio
            models.CheckConstraint(
                condition=models.Q(hora_fin__gt=models.F("hora_inicio")),
                name="bloque_hora_fin_despues_de_inicio",
            ),
        ]

    def clean(self):
        """
        CAPA 3 (nivel Django): Valida que no existan bloques superpuestos
        Un bloque se superpone si: su hora_inicio < mi hora_fin
        AND su hora_fin > mi hora_inicio.
        """
        super().clean()

        if (
            self.hora_inicio
            and self.hora_fin
            and self.hora_inicio >= self.hora_fin
        ):
            raise ValidationError(
                {
                    "hora_fin": (
                        "La hora de fin debe ser posterior a la "
                        "hora de inicio."
                    )
                }
            )

        if (
            self.medico_id
            and self.fecha
            and self.hora_inicio
            and self.hora_fin
        ):
            bloques_superpuestos = BloqueDisponibilidad.objects.filter(
                medico=self.medico,
                fecha=self.fecha,
                # El otro empieza antes de que yo termine
                hora_inicio__lt=self.hora_fin,
                # El otro termina después de que yo empiezo
                hora_fin__gt=self.hora_inicio,
            ).exclude(
                pk=self.pk
            )  # Excluir el bloque actual (para ediciones)

            if bloques_superpuestos.exists():
                bloque_conflicto = bloques_superpuestos.first()
                raise ValidationError(
                    f"Este bloque se superpone con otro existente: "
                    f"{bloque_conflicto.hora_inicio} - "
                    f"{bloque_conflicto.hora_fin}. "
                    f"No se permite overbooking."
                )

    def __str__(self):
        estado_str = 'Libre' if self.esta_disponible else 'Ocupado'
        return (
            f"Bloque: {self.medico.first_name} | {self.fecha} "
            f"{self.hora_inicio} - {estado_str}"
        )


# 4. RESERVA (Desacoplado - Responsabilidad del Paciente)
class Reserva(models.Model):
    ESTADOS = (
        ("RESERVADO", "Reservado"),
        ("CONFIRMADO", "Confirmado"),
        ("EN_ESPERA", "En sala de espera"),
        ("EJECUTADO", "Ejecutado"),
        ("CANCELADO", "Cancelado"),
        ("NO_SHOW", "No-show"),
    )

    paciente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="reservas_paciente",
        limit_choices_to={"rol": "PACIENTE"},
    )
    # Relación 1 a 1: Una reserva ocupa un solo bloque,
    # y un bloque tiene solo una reserva activa.
    bloque = models.OneToOneField(
        BloqueDisponibilidad, on_delete=models.PROTECT
    )

    estado = models.CharField(
        max_length=15, choices=ESTADOS, default="RESERVADO"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Reserva de {self.paciente.first_name} "
            f"para bloque ID: {self.bloque.id} | Estado: {self.estado}"
        )
