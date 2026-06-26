from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .services import ReservaFacade
from .models import Usuario, Especialidad


def api_obtener_especialidades(request):
    especialidades_lista = list(Especialidad.objects.values("id", "nombre"))
    return JsonResponse({"especialidades": especialidades_lista}, safe=False)


def index(request):
    """Muestra el formulario de búsqueda con datos reales de la BD."""
    especialidades = ReservaFacade.obtener_especialidades()
    return render(request, "index.html", {"especialidades": especialidades})


def agenda(request):
    """Muestra los resultados de la búsqueda de bloques médicos."""
    especialidad_id = request.GET.get("especialidad")
    fecha = request.GET.get("fecha")

    # Usamos el Facade para consultar los bloques reales
    bloques = ReservaFacade.obtener_bloques_disponibles(
        especialidad_id,
        fecha,
    )

    # Obtener el nombre de la especialidad para mostrarlo en el HTML
    especialidad_obj = Especialidad.objects.filter(id=especialidad_id).first()
    nombre_especialidad = (
        especialidad_obj.nombre if especialidad_obj else "Todas"
    )

    contexto = {
        "especialidad": nombre_especialidad,
        "fecha": fecha,
        "bloques": bloques,
    }
    return render(request, "agenda.html", contexto)


def confirmar_reserva(request):
    """Procesa la reserva cuando el paciente hace click en 'Reservar'."""
    if request.method == "POST":
        bloque_id = request.POST.get("bloque_id")

        # SIMULACIÓN DE LOGIN
        # Tomamos el primer paciente que exista en la BD.
        # (Se usa datos_prueba.json para los datos de ejemplo)
        paciente_simulado = Usuario.objects.filter(rol="PACIENTE").first()

        if not paciente_simulado:
            messages.error(
                request,
                "Error interno: No hay pacientes registrados en el sistema.",
            )
            return redirect("index")

        # Procesamos la reserva atómica integrando la consulta de Edgar
        exito, mensaje = ReservaFacade.procesar_reserva_atomica(
            bloque_id,
            paciente_simulado,
        )

        if exito:
            messages.success(request, f"¡Éxito! {mensaje}")
        else:
            messages.error(request, f"Fallo al reservar: {mensaje}")

    return redirect("index")
