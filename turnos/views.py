from datetime import datetime, timedelta, date

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .models import Especialidad, Reserva, Usuario
from .services import ReservaFacade
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken
from .services import TurnoService, AgendaService
from django.views.decorators.http import require_GET, require_http_methods


@require_GET
def vista_login(request):
    """Renderiza la plantilla HTML del login."""
    return render(request, "login.html")


@require_GET
def vista_registro(request):
    return render(request, "registro.html")


@require_GET
def vista_cuenta_bloqueada(request):
    return render(request, "cuenta_bloqueada.html")


@require_GET
def vista_recuperar_password(request):
    """Renderiza la plantilla de recuperación (si existe)."""
    return render(request, "recuperar_password.html")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_checkin(request, turno_id):
    """
    Registra el check-in presencial de un paciente.
    Uso exclusivo de Recepción (validado en el servicio).
    """
    try:
        resultado = TurnoService.registrar_checkin(
            turno_id, usuario_ejecutor=request.user
        )
        return Response(
            {"mensaje": "Check-in registrado exitosamente", "estado": resultado},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancelar_turno(request, turno_id):
    """
    Cancela una cita médica. El servicio validará si faltan más de 12 horas.
    """
    try:
        TurnoService.cancelar_turno(turno_id, usuario_ejecutor=request.user)
        return Response(
            {"mensaje": "Turno cancelado correctamente y bloque liberado."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bloquear_agenda(request):
    """
    Bloquea tramos de la agenda del médico por razones administrativas.
    """
    try:
        medico_id = request.data.get("medico_id")
        fecha_inicio = request.data.get("fecha_inicio")
        fecha_fin = request.data.get("fecha_fin")

        resultado = AgendaService.bloquear_tramos(
            medico_id, fecha_inicio, fecha_fin, usuario_ejecutor=request.user
        )
        return Response(
            {
                "mensaje": f"Agenda bloqueada exitosamente. {resultado} bloques afectados."
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_turnos(request):
    """
    Devuelve los turnos del usuario autenticado vía JWT.
    Acepta ?filtro=futuros|pasados|todos
    """
    from django.utils import timezone as tz

    filtro = request.query_params.get("filtro", "futuros")
    hoy = date.today()
    ahora = tz.now()

    reservas = (
        Reserva.objects.select_related(
            "bloque", "bloque__medico", "bloque__especialidad"
        )
        .filter(paciente=request.user)
        .order_by("bloque__fecha", "bloque__hora_inicio")
    )

    if filtro == "futuros":
        reservas = reservas.filter(bloque__fecha__gte=hoy)
    elif filtro == "pasados":
        reservas = reservas.filter(bloque__fecha__lt=hoy)

    data = []
    for r in reservas:
        fecha_hora = tz.make_aware(
            datetime.combine(r.bloque.fecha, r.bloque.hora_inicio)
        )
        diff = fecha_hora - ahora
        puede_cancelar = diff >= timedelta(hours=12) and r.estado in (
            "RESERVADO",
            "CONFIRMADO",
        )
        data.append(
            {
                "id": r.id,
                "fecha": r.bloque.fecha.strftime("%d/%m/%Y"),
                "hora_inicio": r.bloque.hora_inicio.strftime("%H:%M"),
                "hora_fin": r.bloque.hora_fin.strftime("%H:%M"),
                "medico": f"Dr/a. {r.bloque.medico.first_name} {r.bloque.medico.last_name}",
                "especialidad": r.bloque.especialidad.nombre,
                "estado": r.estado,
                "estado_display": r.get_estado_display(),
                "puede_cancelar": puede_cancelar,
            }
        )

    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes(
    [AllowAny]
)  # Cualquiera puede registrarse, no requiere token previo
def api_registrar_usuario(request):
    try:
        # Extraemos los datos del JSON que mandó el frontend
        data = request.data
        rut = data.get("rut")
        email = data.get("email")
        password = data.get("password")
        nombre = data.get("nombre")
        apellido = data.get("apellido")

        # Regla de negocio: Validar que no falten datos
        if not all([rut, email, password, nombre, apellido]):
            return Response(
                {"error": "Faltan datos obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Creamos el usuario en la base de datos
        usuario = Usuario(
            username=rut,  # Django pide un username, usamos el RUT
            rut=rut,
            email=email,
            first_name=nombre,
            last_name=apellido,
            rol="PACIENTE",  # Por defecto, los que se registran por la web son pacientes
        )

        # Hasheamos la contraseña de forma segura
        usuario.set_password(password)
        usuario.save()

        # Generamos los tokens JWT de inmediato para que el frontend inicie sesión automático
        refresh = RefreshToken.for_user(usuario)

        return Response(
            {
                "mensaje": "Cuenta creada exitosamente.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )

    # Si el RUT o el Email ya existen en la base de datos (violación de unicidad)
    except IntegrityError:
        return Response(
            {"errores": {"rut": "El RUT o correo ya está registrado."}},
            status=status.HTTP_409_CONFLICT,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_GET
def api_obtener_especialidades(request):
    especialidades_lista = list(Especialidad.objects.values("id", "nombre"))
    return JsonResponse({"especialidades": especialidades_lista}, safe=False)


@require_GET
def index(request):
    """Muestra el formulario de búsqueda con datos reales de la BD."""
    especialidades = ReservaFacade.obtener_especialidades()
    return render(request, "index.html", {"especialidades": especialidades})


@require_GET
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
    nombre_especialidad = especialidad_obj.nombre if especialidad_obj else "Todas"

    contexto = {
        "especialidad": nombre_especialidad,
        "fecha": fecha,
        "bloques": bloques,
    }
    return render(request, "agenda.html", contexto)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_reservar_turno(request):
    """Procesa la reserva a través de la API DRF usando el usuario autenticado (JWT)."""
    bloque_id = request.data.get("bloque_id")

    if not bloque_id:
        return Response(
            {"error": "Falta el parámetro bloque_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Procesamos la reserva atómica integrando el Facade y usando al usuario autenticado real
    exito, mensaje = ReservaFacade.procesar_reserva_atomica(
        bloque_id,
        request.user,
    )

    if exito:
        return Response({"mensaje": mensaje}, status=status.HTTP_201_CREATED)
    else:
        return Response({"error": mensaje}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Vistas HTML con datos reales de la BD
# ---------------------------------------------------------------------------


@require_GET
def historial_view(request):
    """
    Historial real de turnos leído desde la BD.
    Calcula puede_cancelar aplicando BR-24 (12 horas de anticipación).
    """
    from django.utils import timezone as tz

    filtro = request.GET.get("filtro", "futuros")
    hoy = date.today()
    ahora = tz.now()

    reservas = Reserva.objects.select_related(
        "bloque", "bloque__medico", "bloque__especialidad", "paciente"
    ).order_by("bloque__fecha", "bloque__hora_inicio")

    if filtro == "futuros":
        reservas = reservas.filter(bloque__fecha__gte=hoy)
    elif filtro == "pasados":
        reservas = reservas.filter(bloque__fecha__lt=hoy)

    # Anotar puede_cancelar en cada reserva (BR-24)
    for reserva in reservas:
        fecha_hora = tz.make_aware(
            datetime.combine(reserva.bloque.fecha, reserva.bloque.hora_inicio)
        )
        diff = fecha_hora - ahora
        reserva.puede_cancelar = diff >= timedelta(hours=12) and reserva.estado in (
            "RESERVADO",
            "CONFIRMADO",
        )

    return render(
        request,
        "historial.html",
        {"turnos": reservas, "filtro_activo": filtro},
    )


@require_GET
def checkin_view(request):
    """
    Check-in presencial: muestra reservas de hoy filtradas por RUT o nombre.
    """
    query = request.GET.get("q", "")
    turnos = []

    if query:
        turnos = (
            Reserva.objects.select_related(
                "bloque", "bloque__medico", "bloque__especialidad", "paciente"
            )
            .filter(bloque__fecha=date.today())
            .filter(
                Q(paciente__rut__icontains=query)
                | Q(paciente__first_name__icontains=query)
                | Q(paciente__last_name__icontains=query)
            )
        )

    return render(request, "checkin.html", {"query": query, "turnos": turnos})


@require_http_methods(["POST"])
def checkin_accion(request):
    """
    Procesa el check-in desde el formulario HTML (BR-21, BR-22).
    Redirige de vuelta al check-in con la misma búsqueda activa.
    """
    turno_id = request.POST.get("turno_id")
    q = request.POST.get("q", "")
    try:
        TurnoService.registrar_checkin(int(turno_id), usuario_ejecutor=request.user)
        messages.success(request, "Check-in registrado. Paciente en sala de espera.")
    except Exception as e:
        messages.error(request, f"No se pudo registrar el check-in: {str(e)})")
    return redirect(f"/checkin/?q={q}")


@require_http_methods(["POST"])
def cancelar_turno_form(request):
    """
    Cancela un turno desde el formulario HTML del historial (BR-24, BR-25).
    """
    turno_id = request.POST.get("turno_id")
    try:
        TurnoService.cancelar_turno(int(turno_id), usuario_ejecutor=request.user)
        messages.success(request, "Turno cancelado y bloque liberado correctamente.")
    except Exception as e:
        messages.error(request, f"No se pudo cancelar el turno: {str(e)}")
    return redirect("historial")


@require_http_methods(["POST"])
def confirmar_turno_form(request):
    """
    Confirma un turno (UC-08): cambia el estado de RESERVADO a CONFIRMADO.
    El paciente usa esto para ratificar que asistirá a su cita.
    """
    turno_id = request.POST.get("turno_id")
    try:
        reserva = Reserva.objects.get(id=int(turno_id))
        if reserva.estado == "RESERVADO":
            reserva.estado = "CONFIRMADO"
            reserva.save()
            messages.success(request, "Turno confirmado correctamente.")
        else:
            messages.error(
                request,
                f"No se puede confirmar un turno en estado '{reserva.estado}'.",
            )
    except Reserva.DoesNotExist:
        messages.error(request, "Turno no encontrado.")
    except Exception as e:
        messages.error(request, f"Error al confirmar turno: {str(e)}")
    return redirect("historial")


@require_GET
def reagendar_view(request, turno_id):
    """
    Reagendar turno (UC-03): pendiente de implementación completa.
    Por ahora redirige al historial con un mensaje informativo.
    """
    messages.info(
        request,
        "La funcionalidad de reagendamiento está en desarrollo. "
        "Por favor cancele el turno actual y reserve uno nuevo.",
    )
    return redirect("historial")
