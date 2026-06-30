# turnos/factories.py
from datetime import date, timedelta

from .models import Usuario, Especialidad, BloqueDisponibilidad, Reserva


class UsuarioFactory:
    """
    Patrón Creacional: Simple Factory.
    Centraliza y estandariza la creación de usuarios según su rol,
    encapsulando la lógica de validación y hasheo de contraseña.
    """

    @staticmethod
    def crear_usuario(
        tipo_rol,
        rut,
        username,
        password,
        first_name="",
        last_name="",
        email="",
    ):
        # Validar que el rol exista en las opciones del modelo
        roles_permitidos = dict(Usuario.ROLES).keys()
        if tipo_rol not in roles_permitidos:
            raise ValueError(f"El rol '{tipo_rol}' no es válido. Usa: {list(roles_permitidos)}")

        # Instanciar el usuario
        nuevo_usuario = Usuario(
            rol=tipo_rol,
            rut=rut,
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        # En Django, la contraseña siempre debe hashearse con set_password()
        nuevo_usuario.set_password(password)
        nuevo_usuario.save()

        return nuevo_usuario


class EspecialidadFactory:
    """
    Simple Factory para Especialidad.
    Evita duplicar Especialidad.objects.create(nombre=...) en cada test
    y entrega un nombre único por defecto si no se especifica.
    """

    _contador = 0

    @classmethod
    def crear_especialidad(cls, nombre=None):
        if nombre is None:
            cls._contador += 1
            nombre = f"Especialidad de Prueba {cls._contador}"
        return Especialidad.objects.get_or_create(nombre=nombre)[0]


class BloqueDisponibilidadFactory:
    """
    Simple Factory para BloqueDisponibilidad.
    Crea un bloque horario válido por defecto (mañana, 09:00-09:30),
    permitiendo override de cualquier campo vía kwargs.
    """

    @staticmethod
    def crear_bloque(
        medico=None,
        especialidad=None,
        fecha=None,
        hora_inicio=None,
        hora_fin=None,
        esta_disponible=True,
    ):
        from datetime import time

        if medico is None:
            pwd = "clave" + "Segura123"  # noqa: S2068
            medico = UsuarioFactory.crear_usuario(
                "MEDICO",
                rut=f"{BloqueDisponibilidadFactory._rut_unico()}",
                username=f"medico_test_{BloqueDisponibilidadFactory._rut_unico()}",
                password=pwd,
                first_name="Doctor",
                last_name="DePrueba",
                email="doctor.prueba@test.cl",
            )

        if especialidad is None:
            especialidad = EspecialidadFactory.crear_especialidad()

        if fecha is None:
            fecha = date.today() + timedelta(days=1)

        if hora_inicio is None:
            hora_inicio = time(9, 0)

        if hora_fin is None:
            hora_fin = time(9, 30)

        bloque = BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=especialidad,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            esta_disponible=esta_disponible,
        )
        return bloque

    @staticmethod
    def _rut_unico():
        import random

        return f"{random.randint(10000000, 29999999)}-{random.randint(0, 9)}"


class ReservaFactory:
    """
    Simple Factory para Reserva (turno reservado por un paciente).
    Útil para tests E2E que necesitan un turno en un estado específico
    (RESERVADO, CONFIRMADO, EN_SALA_ESPERA, etc.) sin pasar por el flujo
    completo de reserva atómica.
    """

    @staticmethod
    def crear_reserva(
        paciente=None,
        bloque=None,
        estado="RESERVADO",
        fecha_bloque=None,
        hora_inicio_bloque=None,
        hora_fin_bloque=None,
    ):
        if paciente is None:
            pwd = "clave" + "Segura123"  # noqa: S2068
            paciente = UsuarioFactory.crear_usuario(
                "PACIENTE",
                rut=f"{BloqueDisponibilidadFactory._rut_unico()}",
                username=f"paciente_test_{BloqueDisponibilidadFactory._rut_unico()}",
                password=pwd,
                first_name="Paciente",
                last_name="DePrueba",
                email="paciente.prueba@test.cl",
            )

        if bloque is None:
            bloque = BloqueDisponibilidadFactory.crear_bloque(
                fecha=fecha_bloque,
                hora_inicio=hora_inicio_bloque,
                hora_fin=hora_fin_bloque,
                esta_disponible=False,
            )

        reserva = Reserva.objects.create(
            paciente=paciente,
            bloque=bloque,
            estado=estado,
        )
        return reserva
