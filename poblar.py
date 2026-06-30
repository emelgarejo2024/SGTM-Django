from turnos.models import Especialidad, BloqueDisponibilidad
from turnos.factories import UsuarioFactory
from datetime import date, time, timedelta, datetime

print("Iniciando población de la Base de Datos...")

# 1. Crear Especialidades
nombres_esp = [
    "Cardiología",
    "Pediatría",
    "Dermatología",
    "Medicina General",
    "Traumatología",
]
especialidades = []
for nombre in nombres_esp:
    esp, created = Especialidad.objects.get_or_create(nombre=nombre)
    especialidades.append(esp)
print("✅ Especialidades creadas.")

# 2. Crear Médicos
try:
    medico1 = UsuarioFactory.crear_usuario(
        "MEDICO",
        "11111111-1",
        "dr_house",
        "admin123",
        "Gregory",
        "House",
        "house@sgtm.cl",
    )
    medico2 = UsuarioFactory.crear_usuario(
        "MEDICO",
        "22222222-2",
        "dra_grey",
        "admin123",
        "Meredith",
        "Grey",
        "grey@sgtm.cl",
    )
    print("✅ Médicos creados.")
except Exception:
    from turnos.models import Usuario

    medico1 = Usuario.objects.get(username="dr_house")
    medico2 = Usuario.objects.get(username="dra_grey")
    print("✅ Médicos ya existían, cargados con éxito.")

# 3. Crear Paciente
try:
    UsuarioFactory.crear_usuario(
        "PACIENTE",
        "33333333-3",
        "paciente_juan",
        "admin123",
        "Juan",
        "Pérez",
        "juan@correo.cl",
    )
    print("✅ Paciente creado.")
except Exception:
    pass

fecha_actual = date.today() + timedelta(days=1)
# Si hoy ya es después del 5 de julio, generamos 15 días hacia adelante
fecha_fin = date(2026, 7, 5)
if fecha_fin < fecha_actual:
    fecha_fin = fecha_actual + timedelta(days=15)

print(f"Generando bloques desde {fecha_actual} hasta {fecha_fin}...")
bloques_creados = 0

while fecha_actual <= fecha_fin:
    # Solo de Lunes a Viernes (0=Lunes, 4=Viernes)
    if fecha_actual.weekday() < 5:
        # Generar bloques de 09:00 a 17:00 (con pausa almuerzo 13:00-14:00)
        horas = [
            time(9, 0),
            time(9, 30),
            time(10, 0),
            time(10, 30),
            time(11, 0),
            time(11, 30),
            time(12, 0),
            time(12, 30),
            time(14, 0),
            time(14, 30),
            time(15, 0),
            time(15, 30),
            time(16, 0),
            time(16, 30),
        ]

        for hora_ini in horas:
            dt_ini = datetime.combine(fecha_actual, hora_ini)
            hora_f = (dt_ini + timedelta(minutes=30)).time()

            # Médico 1: Medicina General
            BloqueDisponibilidad.objects.get_or_create(
                medico=medico1,
                especialidad=especialidades[3],
                fecha=fecha_actual,
                hora_inicio=hora_ini,
                hora_fin=hora_f,
            )

            # Médico 2: Pediatría
            BloqueDisponibilidad.objects.get_or_create(
                medico=medico2,
                especialidad=especialidades[1],
                fecha=fecha_actual,
                hora_inicio=hora_ini,
                hora_fin=hora_f,
            )
            bloques_creados += 2

    fecha_actual += timedelta(days=1)

print(f"✅ {bloques_creados} bloques generados masivamente.")
print("🎉 ¡Base de datos poblada con éxito!")
