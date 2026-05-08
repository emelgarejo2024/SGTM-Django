from django.db import transaction
from .models import BloqueDisponibilidad, Reserva

def reservar_bloque_seguro(bloque_id, paciente):
    """
    Implementa la Regla BR-13 del SRS: Atomicidad técnica.
    Bloquea la fila del bloque horario para evitar reservas dobles.
    """
    try:
        with transaction.atomic():
            # select_for_update() bloquea la fila en PostgreSQL hasta que termine la transacción
            bloque = BloqueDisponibilidad.objects.select_for_update().get(id=bloque_id)
            
            if bloque.esta_disponible:
                # 1. Marcamos el bloque como ocupado
                bloque.esta_disponible = False
                bloque.save()
                
                # 2. Creamos la reserva vinculada a ese bloque
                nueva_reserva = Reserva.objects.create(
                    paciente=paciente,
                    bloque=bloque,
                    estado='RESERVADO'
                )
                return True, f"Reserva exitosa ID: {nueva_reserva.id}"
            else:
                return False, "Error: El bloque ya fue tomado por otro usuario."
                
    except BloqueDisponibilidad.DoesNotExist:
        return False, "Error: El bloque seleccionado no existe."
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"