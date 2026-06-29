from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .services import ReservaFacade
from .models import Usuario, Especialidad
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from rest_framework.permissions import AllowAny
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken

def vista_login(request):
    """Renderiza la plantilla HTML del login."""
    return render(request, 'login.html')

def vista_registro(request):
    return render(request, 'registro.html')

def vista_cuenta_bloqueada(request):
    return render(request, 'cuenta_bloqueada.html')

def vista_recuperar_password(request):
    """Renderiza la plantilla de recuperación (si existe)."""
    return render(request, 'recuperar_password.html')

# Importamos los servicios/facades que concentran la lógica de negocio real
from .services import TurnoService, AgendaService 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_checkin(request, turno_id):
    """
    Registra el check-in presencial de un paciente.
    Uso exclusivo de Recepción (validado en el servicio).
    """
    try:
        resultado = TurnoService.registrar_checkin(turno_id, usuario_ejecutor=request.user)
        return Response({"mensaje": "Check-in registrado exitosamente", "estado": resultado}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_turno(request, turno_id):
    """
    Cancela una cita médica. El servicio validará si faltan más de 12 horas.
    """
    try:
        resultado = TurnoService.cancelar_turno(turno_id, usuario_ejecutor=request.user)
        return Response({"mensaje": "Turno cancelado correctamente y bloque liberado."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bloquear_agenda(request):
    """
    Bloquea tramos de la agenda del médico por razones administrativas.
    """
    try:
        medico_id = request.data.get('medico_id')
        fecha_inicio = request.data.get('fecha_inicio')
        fecha_fin = request.data.get('fecha_fin')
        
        resultado = AgendaService.bloquear_tramos(medico_id, fecha_inicio, fecha_fin, usuario_ejecutor=request.user)
        return Response({"mensaje": f"Agenda bloqueada exitosamente. {resultado} bloques afectados."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny]) # Cualquiera puede registrarse, no requiere token previo
def api_registrar_usuario(request):
    try:
        # Extraemos los datos del JSON que mandó el frontend
        data = request.data
        rut = data.get('rut')
        email = data.get('email')
        password = data.get('password')
        nombre = data.get('nombre')
        apellido = data.get('apellido')

        # Regla de negocio: Validar que no falten datos
        if not all([rut, email, password, nombre, apellido]):
            return Response({"error": "Faltan datos obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        # Creamos el usuario en la base de datos
        usuario = Usuario(
            username=rut, # Django pide un username, usamos el RUT
            rut=rut,
            email=email,
            first_name=nombre,
            last_name=apellido,
            rol='PACIENTE' # Por defecto, los que se registran por la web son pacientes
        )
        
        # Hasheamos la contraseña de forma segura
        usuario.set_password(password)
        usuario.save()

        # Generamos los tokens JWT de inmediato para que el frontend inicie sesión automático
        refresh = RefreshToken.for_user(usuario)

        return Response({
            "mensaje": "Cuenta creada exitosamente.",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)

    # Si el RUT o el Email ya existen en la base de datos (violación de unicidad)
    except IntegrityError:
        return Response(
            {"errores": {"rut": "El RUT o correo ya está registrado."}}, 
            status=status.HTTP_409_CONFLICT
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
