from django.db import transaction
from django.core.exceptions import ValidationError
from .models import BloqueDisponibilidad, Reserva
from .models import BloqueDisponibilidad, Reserva, Especialidad

def reservar_bloque_seguro(bloque_id, paciente):
    """
    Implementa la Regla BR-13 del SRS: Atomicidad técnica.
    Bloquea la fila del bloque horario para evitar reservas dobles.
    
    Estrategia anti-overbooking de 3 capas:
      Capa 1 (Schema):       OneToOneField en Reserva → Bloque
      Capa 2 (Transaccional): select_for_update() + transaction.atomic()
      Capa 3 (Constraint):    clean() con validación de superposición + CheckConstraint en DB
    """
    try:
        with transaction.atomic():
            # select_for_update() bloquea la fila en PostgreSQL hasta que termine la transacción
            bloque = BloqueDisponibilidad.objects.select_for_update().get(id=bloque_id)
            
            if bloque.esta_disponible:
                # 1. Marcamos el bloque como ocupado
                bloque.esta_disponible = False
                bloque.full_clean()  # CAPA 3: Ejecuta clean() para validar que no haya superposición
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
    
    except ValidationError as e:
        return False, f"Error de validación: {e.message_dict if hasattr(e, 'message_dict') else str(e)}"
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
        return Especialidad.objects.all().order_by('nombre')
    
    @staticmethod
    def obtener_bloques_disponibles(especialidad_id=None, fecha=None):
        """Devuelve los bloques libres, filtrando dinámicamente."""
        # Traemos solo bloques disponibles y optimizamos la consulta con select_related
        bloques = BloqueDisponibilidad.objects.filter(esta_disponible=True).select_related('medico', 'especialidad')
        
        if especialidad_id:
            bloques = bloques.filter(especialidad_id=especialidad_id)
        if fecha:
            bloques = bloques.filter(fecha=fecha)
            
        return bloques.order_by('fecha', 'hora_inicio')

    @staticmethod
    def procesar_reserva_atomica(bloque_id, paciente):
        """Delega la ejecución a la transacción segura de Edgar."""
        return reservar_bloque_seguro(bloque_id, paciente)