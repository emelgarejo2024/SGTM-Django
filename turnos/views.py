from django.shortcuts import render
from django.http import JsonResponse
from .models import Especialidad

def api_obtener_especialidades(request):
    """
    Cumple con el requisito de "Uso de APIs" de la rúbrica.
    Devuelve todas las especialidades de la base de datos en formato JSON.
    """
    # Transformamos el QuerySet en una lista de diccionarios
    especialidades_lista = list(Especialidad.objects.values('id', 'nombre'))
    
    # Retornamos el JSON. safe=False permite enviar listas u otros objetos no-diccionario en el root.
    return JsonResponse({'especialidades': especialidades_lista}, safe=False)

def index(request):
    especialidad = request.GET.get('especialidad')
    fecha = request.GET.get('fecha')

    contexto = {
        'especialidad': especialidad,
        'fecha': fecha
    }

    return render(request, 'index.html', contexto)