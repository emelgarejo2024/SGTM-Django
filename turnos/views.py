from django.shortcuts import render
from django.http import JsonResponse
from .models import Especialidad


def api_obtener_especialidades(request):
    especialidades_lista = list(Especialidad.objects.values('id', 'nombre'))
    return JsonResponse({'especialidades': especialidades_lista}, safe=False)


# 👇 ESTA SOLO MUESTRA EL FORMULARIO
def index(request):
    return render(request, 'index.html')


# 👇 ESTA MUESTRA LA AGENDA CON LOS DATOS
def agenda(request):
    especialidad = request.GET.get('especialidad')
    fecha = request.GET.get('fecha')

    # 👇 DATOS DE PRUEBA (puedes agregar más)
    pacientes = [
        {"hora": "09:00", "nombre": "Juan Pérez", "motivo": "Control"},
        {"hora": "10:00", "nombre": "María López", "motivo": "Consulta"},
        {"hora": "11:00", "nombre": "Carlos Soto", "motivo": "Chequeo general"},
        {"hora": "12:00", "nombre": "Ana Torres", "motivo": "Dolor lumbar"},
        {"hora": "13:00", "nombre": "Luis Fernández", "motivo": "Revisión"},
    ]

    contexto = {
        'especialidad': especialidad,
        'fecha': fecha,
        'pacientes': pacientes
    }

    return render(request, 'agenda.html', contexto)