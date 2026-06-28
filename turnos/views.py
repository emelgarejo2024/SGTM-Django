from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm

from .services import ReservaFacade
from .models import Usuario, Especialidad
from .forms import RegistroPacienteForm # Asumiendo que tienes este form


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


# --- NUEVA VERSIÓN SIN SIMULACIÓN ---
@login_required(login_url='iniciar_sesion')
def confirmar_reserva(request):
    """Procesa la reserva cuando el paciente hace click en 'Reservar'."""
    if request.method == "POST":
        bloque_id = request.POST.get("bloque_id")

        # Usamos el usuario real que inició sesión en Django
        paciente_real = request.user

        # Validamos que el rol sea realmente PACIENTE
        if getattr(paciente_real, 'rol', None) != "PACIENTE":
            messages.error(request, "Acceso denegado: Solo los pacientes pueden reservar horas.")
            return redirect("index")

        # Procesamos la reserva atómica
        exito, mensaje = ReservaFacade.procesar_reserva_atomica(
            bloque_id,
            paciente_real,
        )

        if exito:
            messages.success(request, f"¡Éxito! {mensaje}")
        else:
            messages.error(request, f"Fallo al reservar: {mensaje}")

    return redirect("index")


# --- VISTAS DE AUTENTICACIÓN (REQUERIDAS PARA EL MVP) ---

def registro_paciente(request):
    """Permite a un usuario nuevo crear su cuenta."""
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Asignamos el rol por defecto
            user.rol = "PACIENTE"
            user.save()
            login(request, user)
            messages.success(request, "¡Cuenta creada exitosamente! Ya puedes reservar.")
            return redirect('index')
    else:
        form = RegistroPacienteForm()
    return render(request, 'registro.html', {'form': form})


def iniciar_sesion(request):
    """Autentica a los usuarios en el sistema."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenido, {user.first_name or username}.")
                return redirect('index')
        else:
            messages.error(request, "RUT o contraseña incorrectos.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def cerrar_sesion(request):
    """Cierra la sesión del usuario activo."""
    logout(request)
    messages.info(request, "Has cerrado sesión de forma segura.")
    return redirect('index')