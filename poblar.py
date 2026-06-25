from turnos.models import Especialidad, BloqueDisponibilidad
from turnos.factories import UsuarioFactory
from datetime import date, time, timedelta

print("Iniciando población de la Base de Datos...")

# 1. Crear Especialidades
nombres_esp = ['Cardiología', 'Pediatría', 'Dermatología', 'Medicina General', 'Traumatología']
especialidades = []
for nombre in nombres_esp:
    esp, created = Especialidad.objects.get_or_create(nombre=nombre)
    especialidades.append(esp)
print("✅ Especialidades creadas.")

# 2. Crear Médicos
try:
    medico1 = UsuarioFactory.crear_usuario('MEDICO', '11111111-1', 'dr_house', 'admin123', 'Gregory', 'House', 'house@sgtm.cl')
    medico2 = UsuarioFactory.crear_usuario('MEDICO', '22222222-2', 'dra_grey', 'admin123', 'Meredith', 'Grey', 'grey@sgtm.cl')
    print("✅ Médicos creados.")
except Exception:
    from turnos.models import Usuario
    medico1 = Usuario.objects.get(username='dr_house')
    medico2 = Usuario.objects.get(username='dra_grey')
    print("✅ Médicos ya existían, cargados con éxito.")

# 3. Crear Paciente
try:
    UsuarioFactory.crear_usuario('PACIENTE', '33333333-3', 'paciente_juan', 'admin123', 'Juan', 'Pérez', 'juan@correo.cl')
    print("✅ Paciente creado.")
except Exception:
    pass

# 4. Crear Bloques
manana = date.today() + timedelta(days=1)
bloques = [
    (medico1, especialidades[3], time(9, 0), time(9, 30)),
    (medico1, especialidades[3], time(9, 30), time(10, 0)),
    (medico1, especialidades[3], time(10, 0), time(10, 30)),
    (medico2, especialidades[1], time(11, 0), time(11, 30)),
    (medico2, especialidades[1], time(11, 30), time(12, 0)),
]

for med, esp, inicio, fin in bloques:
    BloqueDisponibilidad.objects.get_or_create(
        medico=med, especialidad=esp, fecha=manana, hora_inicio=inicio, hora_fin=fin
    )
print(f"✅ Bloques generados para: {manana}.")
print("🎉 ¡Base de datos poblada con éxito!")