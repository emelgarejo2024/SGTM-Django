# turnos/factories.py
from .models import Usuario


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
            raise ValueError(
                f"El rol '{tipo_rol}' no es válido. "
                f"Usa: {list(roles_permitidos)}"
            )

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
