from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import BloqueDisponibilidad, Reserva, Especialidad

class TurnoService:
    @staticmethod
    def registrar_checkin(turno_id, usuario_ejecutor):
        # Usamos select_related para traer el bloque al mismo tiempo y optimizar la BD
        reserva = Reserva.objects.select_related('bloque').get(id=turno_id)
        
        # BR-21 y BR-22: Validar estado y tiempo de tolerancia
        if reserva.estado != 'RESERVADO':
            raise DRFValidationError("La reserva no está en estado válido para check-in.")
            
        ahora = timezone.localtime(timezone.now())
        
        # Como fecha y hora_inicio están separados, los combinamos
        fecha_hora_inicio = timezone.make_aware(
            datetime.combine(reserva.bloque.fecha, reserva.bloque.hora_inicio)
        )
        
        margen_inicio = fecha_hora_inicio - timedelta(minutes=30)
        margen_fin = fecha_hora_inicio + timedelta(minutes=10)
        
        if not (margen_inicio <= ahora <= margen_fin):
            raise DRFValidationError("Fuera del margen de tiempo permitido para el check-in presencial.")
            
        reserva.estado = 'EN_ESPERA'
        reserva.save()
        return "Check-in exitoso"

    @staticmethod
    def cancelar_turno(turno_id, usuario_ejecutor):
        reserva = Reserva.objects.select_related('bloque').get(id=turno_id)
        
        # BR-24: Cancelación con 12 horas de anticipación mínima
        ahora = timezone.localtime(timezone.now())
        fecha_hora_inicio = timezone.make_aware(
            datetime.combine(reserva.bloque.fecha, reserva.bloque.hora_inicio)
        )
        
        diferencia = fecha_hora_inicio - ahora
        if diferencia < timedelta(hours=12):
            raise DRFValidationError("No se puede cancelar con menos de 12 horas de anticipación.")
            
        # BR-25: Cambiar estado y liberar el bloque
        reserva.estado = 'CANCELADO'
        reserva.bloque.esta_disponible = True  
        
        reserva.bloque.save()
        reserva.save()
        return "Turno cancelado y bloque liberado"

class AgendaService:
    @staticmethod
    def bloquear_tramos(medico_id, fecha_inicio, fecha_fin, usuario_ejecutor):
        # Buscamos los bloques libres en ese rango
        bloques = BloqueDisponibilidad.objects.filter(
            medico_id=medico_id, 
            fecha__range=[fecha_inicio, fecha_fin],
            esta_disponible=True
        )
        afectados = bloques.update(esta_disponible=False)
        return afectados

def reservar_bloque_seguro(bloque_id, paciente):
    """
    Implementa la Regla BR-13 del SRS: Atomicidad técnica.
    Bloquea la fila del bloque horario para evitar reservas dobles.

    Estrategia anti-overbooking de 3 capas:
    Capa 1 (Schema):      OneToOneField en Reserva → Bloque
    Capa 2 (Transaccional): select_for_update() + transaction.atomic()
    Capa 3 (Constraint):    clean() con validación de superposición
                            + CheckConstraint en DB
    """
    try:
        with transaction.atomic():
            # select_for_update() bloquea la fila en PostgreSQL
            # hasta que termine la transacción
            bloque = BloqueDisponibilidad.objects.select_for_update().get(
                id=bloque_id
            )

            if bloque.esta_disponible:
                # 1. Marcamos el bloque como ocupado
                bloque.esta_disponible = False
                # CAPA 3: Ejecuta clean() para evitar superposición
                bloque.full_clean()
                bloque.save()

                # 2. Creamos la reserva vinculada a ese bloque
                nueva_reserva = Reserva.objects.create(
                    paciente=paciente, bloque=bloque, estado="RESERVADO"
                )
                return True, f"Reserva exitosa ID: {nueva_reserva.id}"
            else:
                return (
                    False,
                    "Error: El bloque ya fue tomado por otro usuario.",
                )

    except DjangoValidationError as e:
        return (
            False,
            "Error de validación: "
            f"{e.message_dict if hasattr(e, 'message_dict') else str(e)}",
        )
    except BloqueDisponibilidad.DoesNotExist:
        return False, "Error: El bloque seleccionado no existe."
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"


class ReservaFacade:
    """
    Patrón Estructural Facade:
    Proporciona una interfaz simplificada para que las Vistas interactúen
    con la lógica compleja de reservas y disponibilidad.
    """

    @staticmethod
    def obtener_especialidades():
        return Especialidad.objects.all().order_by("nombre")

    @staticmethod
    def obtener_bloques_disponibles(especialidad_id=None, fecha=None):
        """Devuelve los bloques libres, filtrando dinámicamente."""
        # Traemos solo bloques disponibles y optimizamos con select_related
        bloques = BloqueDisponibilidad.objects.filter(
            esta_disponible=True
        ).select_related("medico", "especialidad")

        if especialidad_id:
            bloques = bloques.filter(especialidad_id=especialidad_id)
        if fecha:
            bloques = bloques.filter(fecha=fecha)

        return bloques.order_by("fecha", "hora_inicio")

    @staticmethod
    def procesar_reserva_atomica(bloque_id, paciente):
        """Delega la ejecución a la transacción segura de Edgar."""
        return reservar_bloque_seguro(bloque_id, paciente)